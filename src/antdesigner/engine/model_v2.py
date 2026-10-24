"""
Inference engine - Main brain only (dip specialist removed)
=============================================================
Loads:
  - forward_model_v2_curve.keras   (main brain, dip-weighted, 2 heads)
  - scaler_geo.pkl, scaler_perf.pkl

The s11_dip_specialist.pkl ensemble was optional and is no longer used.
The engine now runs CSV anchoring as primary with the main Keras brain as
fallback / neural refinement. This removes the HF dependency on the specialist
pickle and the "Two-Brain 2.0" labeling.

Public API:
  load_v2_engines()           -> (main_model, None, s_geo, s_perf, FREQS_RAW)
  forward_v2(...)             -> dict with fr, s11, bw, gain, eff, status, f, c, v, ...
  forward_v2_with_csv_anchor  -> CSV-anchored path (kept for compatibility, now CSV-only)

Backward compatible with the retired Streamlit entry point v1 forward_ml() / forward_anchor() helpers.
"""
import os
import numpy as np
import joblib
import tensorflow as tf

HF_REPO = os.getenv("HF_REPO", "kara-nawzad/antenna-models")


def _download_hf(filename):
    """Download a file from Hugging Face Hub if not already local."""
    if os.path.exists(filename):
        return
    try:
        from huggingface_hub import hf_hub_download
        hf_hub_download(repo_id=HF_REPO, filename=filename, local_dir=".")
        print(f"[HF] Downloaded {filename} from {HF_REPO}")
    except Exception as e:
        print(f"[HF] Skipping {filename}: {e}")


FREQS_RAW = np.linspace(1.0, 7.0, 151)


def load_v2_engines(model_dir=None, main_model=None):
    """Load the main-brain stack.

    main_model : optional already-loaded Keras model. The API engine loads
      forward_model_v2_curve.keras for the main path; passing that same object here
      avoids loading the identical 115 MB model a second time. Holding two full
      copies of it plus TensorFlow inside a 1 GB container was the single largest
      memory cost in the app and the most likely cause of OOM restarts.
    """
    if model_dir is not None:
        os.chdir(model_dir)

    if main_model is not None:
        return _finish_load(main_model)

    main_path = "forward_model_v2_curve.keras"
    if not os.path.exists(main_path):
        _download_hf("forward_model_v2_curve.keras")
    if not os.path.exists(main_path):
        for alt in ("forward_model_shrunk.keras", "forward_model_final.keras", "forward_model_final.h5"):
            if os.path.exists(alt):
                main_path = alt
                break
        else:
            raise FileNotFoundError(
                "No main brain found. Expected one of: "
                "forward_model_v2_curve.keras, forward_model_shrunk.keras, "
                "forward_model_final.keras, forward_model_final.h5"
            )

    main = tf.keras.models.load_model(main_path, compile=False)
    return _finish_load(main)


def _finish_load(main):
    """Shared tail of load_v2_engines(): load scalers."""
    # Dip specialist removed — no s11_dip_specialist.pkl download or load.
    s_geo = joblib.load("scaler_geo.pkl")
    s_perf = joblib.load("scaler_perf.pkl")

    # Keep 5-tuple return for backward compatibility with core.py:
    # (main, dip_specialist, s_geo, s_perf, FREQS_RAW)
    # dip_specialist is always None now.
    return main, None, s_geo, s_perf, FREQS_RAW


# ---------------------------------------------------------------------------
# DSP / VNA helpers
# ---------------------------------------------------------------------------
def _apply_dsp_polishing(freqs, curve):
    from scipy.interpolate import make_interp_spline

    freqs = np.asarray(freqs, dtype=float)
    curve = np.asarray(curve, dtype=float)
    if len(freqs) != len(curve) or len(curve) < 2:
        raise ValueError("freqs and curve must be same length >= 2")

    finite = np.isfinite(freqs) & np.isfinite(curve)
    if not np.all(finite):
        freqs = freqs[finite]
        curve = curve[finite]
        if len(freqs) < 2:
            raise ValueError("Not enough finite points for polishing")

    # Cubic spline upsampling from 151 to 1000 pts. NO Savitzky-Golay — it destroys dip accuracy.
    f_fine = np.linspace(freqs.min(), freqs.max(), 1000)
    k = min(3, len(freqs) - 1)
    spline = make_interp_spline(freqs, curve, k=k)
    return f_fine, spline(f_fine)


def _vna_measure(freqs, curve):
    idx_min = int(np.argmin(curve))
    m_fr = float(freqs[idx_min])
    m_s11 = float(curve[idx_min])
    mask = (curve <= -10.0).astype(int)
    diff = np.diff(np.concatenate(([0], mask, [0])))
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0] - 1
    status = "WORKING" if len(starts) > 0 else "NOT WORKING"
    bw = 0.0
    if len(starts) > 0:
        primary = next(((s, e) for s, e in zip(starts, ends) if s <= idx_min <= e), (starts[0], ends[0]))
        bw = float(freqs[primary[1]] - freqs[primary[0]])
    gamma = 10 ** (np.clip(curve, -100, 0) / 20.0)
    vswr = np.clip((1 + gamma) / np.maximum(1e-8, (1 - gamma)), 1, 10)
    return m_fr, m_s11, bw, status, vswr


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def forward_v2(lp, wp, shape_id, main_model, dip_specialist, s_geo, s_perf,
               use_anchor=True, blend_window_mhz=50.0, anchor_strength=1.0,
               verbose=0):
    """
    Args:
        lp, wp    : geometry (mm)
        shape_id  : 1..12
        main_model: the TF model (v2 preferred, v1 also works)
        dip_specialist: ignored (kept for compatibility, always None)
        s_geo, s_perf: scalers from 2_preprocessing.py
        use_anchor: ignored (dip specialist removed)
        blend_window_mhz: ignored
        anchor_strength: ignored

    Returns: dict (matches the retired Streamlit entry point forward_ml() output format)
    """
    # Build the 14-dim input (Lp, Wp, 12 shape one-hots) and scale
    x = np.zeros((1, 14), dtype=float)
    x[0, 0] = float(lp)
    x[0, 1] = float(wp)
    if 1 <= int(shape_id) <= 12:
        x[0, 1 + int(shape_id)] = 1.0
    x_scaled = s_geo.transform(x)

    # Run main brain (2 heads: scalars [fr, Gain, Eff, S11_min], curve [151])
    p_scalars, p_curve = main_model.predict(x_scaled, verbose=verbose)
    p_scalars = p_scalars[0]
    p_curve = p_curve[0]

    # Reconstruct the full 157-dim prediction.
    recon = np.zeros((1, 157), dtype=float)
    recon[0, [0, 2, 3, 4]] = p_scalars
    recon[0, 6:] = p_curve
    perf = s_perf.inverse_transform(recon)[0]
    base_s11_min = float(perf[4])
    base_gain = float(perf[2])
    base_eff = float(perf[3])

    base_curve = perf[6:].astype(float)

    # Dip specialist removed — no anchor blend
    final_curve = base_curve
    used_specialist = False

    # DSP polishing + VNA measurement
    f_s, c_s = _apply_dsp_polishing(FREQS_RAW, final_curve)
    fr, s11, bw, status, vswr = _vna_measure(f_s, c_s)

    return {
        "fr": fr,
        "s11": s11,
        "bw": bw,
        "gain": base_gain,
        "eff": base_eff,
        "status": status,
        "f": f_s,
        "c": c_s,
        "v": vswr,
        "spec_f_dip": None,
        "spec_s11_min": None,
        "main_s11_min": base_s11_min,
        "used_specialist": used_specialist,
        "engine": "Main-Brain only",
    }


def forward_v2_with_csv_anchor(lp, wp, shape_id, main_model, dip_specialist, s_geo, s_perf,
                                csv_curve, csv_f_axis,
                                use_anchor=True, blend_window_mhz=50.0, anchor_strength=1.0,
                                verbose=0):
    """
    CSV-anchored path — dip specialist removed, now pure CSV.
    Kept for compatibility with core.py; returns polished CSV curve.
    """
    # If we have CSV data, use it directly (CSV is ground truth)
    if csv_curve is not None and len(csv_curve) > 0:
        final_curve = csv_curve
        used_specialist = False
        f_s, c_s = _apply_dsp_polishing(csv_f_axis, final_curve)
    else:
        # No CSV data - use pure ML prediction
        result = forward_v2(lp, wp, shape_id, main_model, dip_specialist, s_geo, s_perf,
                           use_anchor=use_anchor, blend_window_mhz=blend_window_mhz,
                           anchor_strength=anchor_strength, verbose=verbose)
        return result

    fr, s11, bw, status, vswr = _vna_measure(f_s, c_s)

    return {
        "fr": fr,
        "s11": s11,
        "bw": bw,
        "gain": float(np.nan),
        "eff": float(np.nan),
        "status": status,
        "f": f_s,
        "c": c_s,
        "v": vswr,
        "spec_f_dip": None,
        "spec_s11_min": None,
        "used_specialist": used_specialist,
        "engine": "CSV-only",
    }
