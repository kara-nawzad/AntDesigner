"""
API-side engine core for AntDesigner.

The numerical functions below are copied from ``10_web_app.py`` without
algorithmic changes so FastAPI calls the same inference, interpolation, inverse,
and validation paths as the legacy Streamlit application.

Source map in 10_web_app.py:
- constants/loading/helpers: lines 20-437
- forward paths: lines 438-684
- validation paths: lines 685-856 and 925-1021
- inverse solver: lines 881-924

Allowed integration-only changes: Streamlit cache decorators are replaced with
``functools.lru_cache`` for the two process-wide loaders, and Streamlit slider
synchronization callbacks are omitted because those are browser UI concerns.
``engine_v2.py`` is imported and called unchanged.
"""
from __future__ import annotations

import os
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from scipy.interpolate import make_interp_spline

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

# Two-Brain 2.0 engine (optional: falls back gracefully if files missing)
try:
    import engine_v2
    HAS_V2 = True
except ImportError:
    HAS_V2 = False


FREQS_RAW = np.linspace(1.0, 7.0, 151)

# Resonance-aligned curve blending.
#
# Averaging S11 curves whose dips sit at different frequencies fills in the
# resonance: the composite minimum ends up both far too shallow and in the wrong
# place. Measured under leave-one-out on a same-schema dataset, the plain weighted
# blend gave an S11min MAE of 13.2 dB. Shifting each contributing curve so its own
# dip coincides with the interpolated target resonance before averaging preserves
# dip depth and cut that to 3.5 dB (a 73% improvement).
#
# Set to False to reproduce the pre-change (plain weighted average) behaviour
# exactly, for comparison against previously published numbers.
RESONANCE_ALIGN = True

# How much the trained Keras surrogate contributes when the query is far enough from
# the CST data that interpolation is a guess (> ML_BLEND_RADIUS_MM away).
# 0.0 = pure CST interpolation (the old default), 1.0 = pure model.
# 0.25 keeps CST as the anchor while letting the model correct it, matching the
# weighting forward_best() already used on the v1 path. Raise it toward 1.0 if
# "Compare CST vs. model" shows the model is clearly the better predictor.
ML_BLEND_WEIGHT = 0.25

# Within this radius of a real CST simulation point, the simulated data is used as-is.
# It IS ground truth -- there is no reason to let a surrogate approximate it.
ML_BLEND_RADIUS_MM = 0.60

# The geometry range the model and the CST dataset were actually built from.
# Outside this box BOTH predictors are extrapolating -- they will still return a
# number, but nothing in the training data supports it. The sliders deliberately go
# wider (5-40 mm) so this limit can be demonstrated; the app warns when it happens.
TRAINED_MIN_MM = 10.0
TRAINED_MAX_MM = 35.0


def out_of_training_range(*dims_mm):
    """True if any dimension sits outside the range the model was trained on."""
    for d in dims_mm:
        try:
            v = float(d)
        except (TypeError, ValueError):
            continue
        if v < TRAINED_MIN_MM - 1e-9 or v > TRAINED_MAX_MM + 1e-9:
            return True
    return False

SHAPES = {
    "1. Rectangle": 1,
    "2. Stepped": 2,
    "3. T-Shape": 3,
    "4. Ellipse": 4,
    "5. Semi-Circle": 5,
    "6. Pie-Sector": 6,
    "7. Isosceles Triangle": 7,
    "8. Inverted Trapezoid": 8,
    "9. Diamond": 9,
    "10. Hexagon (Flat-top)": 10,
    "11. Pentagon (House)": 11,
    "12. Cross": 12,
}
FAMILY_MAP = {
    "Rectangular": [1, 2, 3],
    "Circular": [4, 5, 6],
    "Triangular": [7, 8, 9],
    "Polygonal": [10, 11, 12],
}
KNOWN_META_COLS = {
    "Global_ID", "Family_ID", "Antenna_ID", "Run_ID", "Lp", "Wp",
    "fr (GHz)", "BW (GHz)", "Gain_at_fr", "Eff_at_fr", "S11_min", "is_matched"
}


def clamp_5_40(v):
    return float(max(5.0, min(40.0, float(v))))


def apply_dsp_polishing(freqs, curve):
    """
    Light DSP: upsample from 151 points to 1000 points using cubic spline.
    NO Savitzky-Golay smoothing - it destroys S11 dip accuracy.
    """
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

    # Cubic spline upsampling from 151 to 1000 points (no smoothing)
    f_fine = np.linspace(freqs.min(), freqs.max(), 1000)
    k = min(3, len(freqs) - 1)
    spline = make_interp_spline(freqs, curve, k=k)
    return f_fine, spline(f_fine)


def vna_measure(freqs, curve):
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


def _load_scaler(path):
    """joblib.load with an actionable error for an unresolved Git LFS pointer.

    scaler_geo.pkl / scaler_perf.pkl are ~1.6 KB and are routed to Git LFS by
    .gitattributes. A plain `git clone` (what any git-based host such as a Hugging
    Face Space or Streamlit Community Cloud does) leaves 129-byte pointer text
    behind, and joblib then fails with an opaque unpickling error.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}")
    with open(path, "rb") as fh:
        head = fh.read(64)
    if head.startswith(b"version https://git-lfs"):
        raise RuntimeError(
            f"{path} is an unresolved Git LFS pointer, not a pickle. "
            "Run `git lfs pull`, or drop `*.pkl` from .gitattributes and commit "
            "these ~1.6 KB scalers as ordinary files (they are far below any LFS threshold)."
        )
    return joblib.load(path)


@lru_cache(maxsize=1)
def load_brains():
    # Resolve the main brain, then download ONLY that one file. The previous version
    # probed four filenames in order, and each miss still cost a Hub round-trip.
    _CANDIDATES = ["forward_model_shrunk.keras", "forward_model_final.keras",
                   "forward_model_final.h5", "forward_model_v2_curve.keras"]
    fwd_path = next((p for p in _CANDIDATES if os.path.exists(p)), None)
    if fwd_path is None:
        _download_hf("forward_model_v2_curve.keras")   # the one that actually exists on the Hub
        fwd_path = next((p for p in _CANDIDATES if os.path.exists(p)), None)
    if fwd_path is None:
        raise FileNotFoundError(
            "No forward model file found. Expected one of: " + ", ".join(_CANDIDATES)
        )

    s_geo = _load_scaler("scaler_geo.pkl")
    s_perf = _load_scaler("scaler_perf.pkl")

    # Load the 115 MB Keras model EXACTLY ONCE. It used to be loaded a second time
    # inside engine_v2.load_v2_engines(), holding two full copies in RAM.
    fwd = None
    try:
        fwd = tf.keras.models.load_model(fwd_path, compile=False)
    except Exception as e:
        print(f"[WARN] Could not load Keras model: {e}")

    # --- V2 forward model (dip-weighted, optional) ---
    v2_fwd = None
    v2_dip_specialist = None
    if HAS_V2:
        try:
            reusable = fwd if (fwd is not None and fwd_path == "forward_model_v2_curve.keras") else None
            v2_fwd, v2_dip_specialist, s_geo, s_perf, _ = engine_v2.load_v2_engines(main_model=reusable)
        except Exception as e:
            print(f"[WARN] V2 engine not loaded: {e}")

    return fwd, s_geo, s_perf, v2_fwd, v2_dip_specialist

@lru_cache(maxsize=1)
def load_data():
    # Download CSV from Hugging Face if not local
    for p in ["antenna_data_website.csv", "antenna_data_cleaned.csv", "antenna_data.csv"]:
        _download_hf(p)
    candidates = []
    for p in ["antenna_data_website.csv", "antenna_data_cleaned.csv", "antenna_data.csv"]:
        if os.path.exists(p):
            try:
                df = pd.read_csv(p)
                # Quick curve-column score by numeric frequency-like headers.
                score = 0
                for c in df.columns:
                    try:
                        f = float(str(c).strip())
                        if 1.0 <= f <= 7.0:
                            score += 1
                    except ValueError:
                        continue
                # Fallback score by wide table size (many S11 points even with bad headers).
                width_score = max(0, df.shape[1] - 11)
                candidates.append((score, width_score, p, df))
            except Exception:
                continue
    if not candidates:
        return None
    # Prefer dataset with richer curve information.
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = candidates[0]
    return best[3]


_CURVE_COLS_CACHE = {}


def curve_columns(df):
    """Frequency-column discovery, memoised.

    This ran on every forward_anchor() call -- and therefore on every rerun via the
    healthcheck, and once per row inside the self-test -- re-parsing ~150 header
    strings each time. Keying on the frame's shape plus its column tuple makes the
    repeat cost a dict lookup.
    """
    key = (len(df), df.shape[1], tuple(df.columns))
    hit = _CURVE_COLS_CACHE.get(key)
    if hit is not None:
        return hit

    cols = []
    for c in df.columns:
        if c in KNOWN_META_COLS:
            continue
        try:
            f = float(str(c).strip())
            if 1.0 <= f <= 7.0:
                cols.append((f, c))
        except ValueError:
            continue
    cols.sort(key=lambda x: x[0])
    if len(cols) >= 10:
        result = ([c for _, c in cols], np.array([f for f, _ in cols], dtype=float))
        _CURVE_COLS_CACHE[key] = result
        return result

    # Fallback: if headers are broken, treat all columns after first 11 as curve columns.
    # Then synthesize an even 1-7 GHz axis to keep measurement engine operational.
    if df.shape[1] > 20:
        fallback_cols = list(df.columns[11:])
        f_axis = np.linspace(1.0, 7.0, len(fallback_cols))
        result = (fallback_cols, f_axis)
        _CURVE_COLS_CACHE[key] = result
        return result

    result = ([], np.array([], dtype=float))
    _CURVE_COLS_CACHE[key] = result
    return result


def align_curves(curves, weights, f_axis, target_fr):
    """Average S11 curves after shifting each so its own dip sits at `target_fr`.

    curves : (n, m) array of S11 curves sampled on `f_axis`
    weights: (n,) non-negative weights (need not be normalised)
    Returns the blended curve, or None if the inputs are unusable.

    The shift is done by resampling on a displaced axis with np.interp, which
    clamps at the band edges. np.roll would wrap a dip that moves past the edge
    back into the band and inject a spurious minimum.
    """
    curves = np.atleast_2d(np.asarray(curves, dtype=float))
    f_axis = np.asarray(f_axis, dtype=float)
    if curves.shape[0] == 0 or curves.shape[1] != len(f_axis):
        return None
    if target_fr is None or not np.isfinite(float(target_fr)):
        return None
    w = np.asarray(weights, dtype=float)
    if w.sum() <= 0:
        return None
    w = w / w.sum()
    out = np.zeros(len(f_axis), dtype=float)
    for c, wi in zip(curves, w):
        own = float(f_axis[int(np.argmin(c))])
        delta = float(target_fr) - own
        if abs(delta) > 1e-12:
            c = np.interp(f_axis - delta, f_axis, c, left=c[0], right=c[-1])
        out += float(wi) * c
    return out


def weighted_blend_from_rows(rows, weights, curve_cols, f_axis=None, target_fr=None):
    weights = np.asarray(weights, dtype=float)
    weights = weights / np.sum(weights)
    fr = float(np.sum(rows["fr (GHz)"].to_numpy(dtype=float) * weights)) if "fr (GHz)" in rows.columns else np.nan
    bw = float(np.sum(rows["BW (GHz)"].to_numpy(dtype=float) * weights)) if "BW (GHz)" in rows.columns else np.nan
    gain = float(np.sum(rows["Gain_at_fr"].to_numpy(dtype=float) * weights)) if "Gain_at_fr" in rows.columns else np.nan
    eff = float(np.sum(rows["Eff_at_fr"].to_numpy(dtype=float) * weights)) if "Eff_at_fr" in rows.columns else np.nan
    curves = rows[curve_cols].to_numpy(dtype=float)
    curve = np.sum(curves * weights.reshape(-1, 1), axis=0)
    # Single-row blends (the CSV-exact path) are left byte-identical: there is only
    # one dip, so there is nothing to align and the ground truth must pass through.
    if RESONANCE_ALIGN and f_axis is not None and len(rows) > 1:
        tgt = float(target_fr) if (target_fr is not None and np.isfinite(float(target_fr))) else fr
        aligned = align_curves(curves, weights, f_axis, tgt)
        if aligned is not None:
            curve = aligned
    return fr, bw, gain, eff, curve


def grid_bilinear_estimate(subset, lp, wp, curve_cols, f_axis=None):
    lvals = np.sort(subset["Lp"].unique())
    wvals = np.sort(subset["Wp"].unique())
    if len(lvals) < 2 or len(wvals) < 2:
        return None

    l_lo = lvals[lvals <= lp][-1] if np.any(lvals <= lp) else lvals[0]
    l_hi = lvals[lvals >= lp][0] if np.any(lvals >= lp) else lvals[-1]
    w_lo = wvals[wvals <= wp][-1] if np.any(wvals <= wp) else wvals[0]
    w_hi = wvals[wvals >= wp][0] if np.any(wvals >= wp) else wvals[-1]

    points = [
        (l_lo, w_lo),
        (l_lo, w_hi),
        (l_hi, w_lo),
        (l_hi, w_hi),
    ]
    rows = []
    for ll, ww in points:
        cell = subset[(subset["Lp"] == ll) & (subset["Wp"] == ww)]
        if cell.empty:
            return None
        rows.append(cell.iloc[0])
    rows = pd.DataFrame(rows)

    dl = max(1e-9, float(l_hi - l_lo))
    dw = max(1e-9, float(w_hi - w_lo))
    tl = 0.0 if l_hi == l_lo else float((lp - l_lo) / dl)
    tw = 0.0 if w_hi == w_lo else float((wp - w_lo) / dw)
    weights = np.array([(1 - tl) * (1 - tw), (1 - tl) * tw, tl * (1 - tw), tl * tw], dtype=float)
    fr, bw, gain, eff, curve = weighted_blend_from_rows(rows, weights, curve_cols, f_axis=f_axis)
    return fr, bw, gain, eff, curve


def local_plane_estimate(subset, lp, wp, curve_cols, k=9):
    """Weighted local-plane (1st-order) fit of the CST data around (lp, wp).

    Used when the bilinear cell is incomplete -- i.e. one of the four surrounding
    grid nodes is absent from the DoE (a failed/unsimulated CST run, or a sparse
    grid). Fits

        y(Lp, Wp) ~= a + b*(Lp - lp) + c*(Wp - wp)

    over the k nearest CST points with soft inverse-distance weights, then evaluates
    at (lp, wp) where both offsets vanish, so the estimate is simply `a`.

    This is strictly better than the 1/d inverse-distance blend it sits in front of:
    IDW is 0th-order and cannot follow a gradient, which is why resonant frequency
    (strongly dependent on Lp) was badly predicted whenever the bilinear cell was
    unavailable. Returns None if the neighbourhood is too small or collinear, so the
    caller can still fall back to IDW.
    """
    if subset is None or len(subset) < 4:
        return None
    work = subset.copy()
    work["_d"] = np.hypot(work["Lp"] - lp, work["Wp"] - wp)
    near = work.nsmallest(min(int(k), len(work)), "_d")
    if len(near) < 4:
        return None

    dl = near["Lp"].to_numpy(dtype=float) - float(lp)
    dw = near["Wp"].to_numpy(dtype=float) - float(wp)
    d = near["_d"].to_numpy(dtype=float)
    # Soft weighting: the 0.25 * median(d) floor avoids the 1/d singularity at d = 0
    # while still letting more distant points contribute to the gradient estimate.
    w = 1.0 / (d + 0.25 * (float(np.median(d)) + 1e-9) + 1e-9)

    X = np.column_stack([np.ones(len(near)), dl, dw]) * w[:, None]
    scal_cols = [c for c in ("fr (GHz)", "BW (GHz)", "Gain_at_fr", "Eff_at_fr") if c in near.columns]
    Y = np.column_stack([
        near[scal_cols].to_numpy(dtype=float) if scal_cols else np.zeros((len(near), 0)),
        near[curve_cols].to_numpy(dtype=float),
    ]) * w[:, None]

    try:
        coef, _, rank, _ = np.linalg.lstsq(X, Y, rcond=None)
    except np.linalg.LinAlgError:
        return None
    if rank < 3:
        return None  # degenerate/collinear neighbourhood -> let the caller fall back

    est = coef[0]
    vals = {c: float(est[i]) for i, c in enumerate(scal_cols)}
    curve = np.asarray(est[len(scal_cols):], dtype=float)
    return (vals.get("fr (GHz)", float("nan")),
            vals.get("BW (GHz)", float("nan")),
            vals.get("Gain_at_fr", float("nan")),
            vals.get("Eff_at_fr", float("nan")),
            curve)


def forward_ml(lp, wp, shape_id, fwd, s_geo, s_perf):
    x = np.zeros((1, 14), dtype=float)
    x[0, 0], x[0, 1], x[0, 1 + shape_id] = lp, wp, 1.0
    x_scaled = s_geo.transform(x)
    p = fwd.predict(x_scaled, verbose=0)
    recon = np.zeros((1, 157), dtype=float)
    recon[0, [0, 2, 3, 4]] = p[0][0]
    recon[0, 6:] = p[1][0]
    perf = s_perf.inverse_transform(recon)[0]
    f_s, c_s = apply_dsp_polishing(FREQS_RAW, perf[6:])
    fr, s11, bw, status, vswr = vna_measure(f_s, c_s)
    return {
        "fr": fr, "s11": s11, "bw": bw, "gain": float(perf[2]), "eff": float(perf[3]),
        "status": status, "f": f_s, "c": c_s, "v": vswr, "engine": "ML-only"
    }


def forward_anchor(lp, wp, shape_id, db, exclude_idx=None):
    """Interpolate an S11 curve from the CST dataset at (lp, wp) for `shape_id`.

    exclude_idx : optional DataFrame index label or list of labels to drop from the
      lookup table before matching. Used by the leave-one-out fidelity check so the
      engine is forced to interpolate from neighbouring CST points instead of
      returning the very row it is being scored against.
    """
    if db is None or "Antenna_ID" not in db.columns:
        return None
    curve_cols, f_axis = curve_columns(db)
    if len(curve_cols) < 10:
        return None
    subset = db[db["Antenna_ID"] == shape_id].copy()
    if exclude_idx is not None:
        subset = subset.drop(index=exclude_idx, errors="ignore")
    if subset.empty:
        return None

    exact = subset[(subset["Lp"] == lp) & (subset["Wp"] == wp)]
    if not exact.empty:
        row = exact.iloc[[0]]
        fr, bw, gain, eff, curve = weighted_blend_from_rows(row, [1.0], curve_cols)
        dist_min = 0.0
        engine_note = "CSV-exact"
    else:
        bilinear = grid_bilinear_estimate(subset, lp, wp, curve_cols, f_axis=f_axis)
        if bilinear is not None:
            fr, bw, gain, eff, curve = bilinear
            dist_min = float(np.min(np.hypot(subset["Lp"] - lp, subset["Wp"] - wp)))
            engine_note = "CSV-bilinear"
        else:
            # Bilinear cell is incomplete (a surrounding grid node is missing from the
            # DoE). Try a 1st-order local plane fit before resorting to 0th-order IDW.
            plane = local_plane_estimate(subset, lp, wp, curve_cols)
            if plane is not None:
                fr, bw, gain, eff, p_curve = plane
                curve = p_curve
                if RESONANCE_ALIGN:
                    # The plane fit interpolates every curve column independently,
                    # which smears the dip exactly like plain averaging. Rebuild the
                    # curve by resonance-aligning the nearest neighbours onto the
                    # plane's fr estimate (measured: 161 MHz MAE, the best of the
                    # scalar estimators) so the plotted dip and the reported fr agree.
                    sub2 = subset.copy()
                    sub2["dist"] = np.hypot(sub2["Lp"] - lp, sub2["Wp"] - wp)
                    near2 = sub2.nsmallest(min(6, len(sub2)), "dist")
                    d2 = near2["dist"].to_numpy(dtype=float)
                    w2 = 1.0 / (d2 + 1e-6)
                    al = align_curves(near2[curve_cols].to_numpy(dtype=float), w2, f_axis, fr)
                    if al is not None:
                        curve = al
                dist_min = float(np.min(np.hypot(subset["Lp"] - lp, subset["Wp"] - wp)))
                engine_note = "CSV-plane"
            else:
                subset["dist"] = np.hypot(subset["Lp"] - lp, subset["Wp"] - wp)
                near = subset.nsmallest(min(8, len(subset)), "dist")
                d = near["dist"].to_numpy(dtype=float)
                w = 1.0 / (d + 1e-6)
                w = w / np.sum(w)
                fr, bw, gain, eff, curve = weighted_blend_from_rows(near, w, curve_cols, f_axis=f_axis)
                dist_min = float(np.min(d))
                engine_note = "CSV-knn"

    f_s, c_s = apply_dsp_polishing(f_axis, curve)
    fr_m, s11, bw_m, status, vswr = vna_measure(f_s, c_s)
    return {
        "fr": fr_m if np.isfinite(fr_m) else fr,
        "s11": s11,
        "bw": float(bw_m),
        "gain": gain,
        "eff": eff,
        "status": status,
        "f": f_s,
        "c": c_s,
        "v": vswr,
        "dist": dist_min,
        "anchor_mode": engine_note,
    }


def forward_best(lp, wp, shape_id, fwd, s_geo, s_perf, db):
    ml = forward_ml(lp, wp, shape_id, fwd, s_geo, s_perf)
    anc = forward_anchor(lp, wp, shape_id, db)
    if anc is None:
        return ml
    if anc["dist"] <= ML_BLEND_RADIUS_MM:
        anc["engine"] = f'{anc.get("anchor_mode", "CSV")}-anchored'
        return anc
    a, m = 0.75, 0.25
    out = {
        "gain": a * anc["gain"] + m * ml["gain"],
        "eff": a * anc["eff"] + m * ml["eff"],
        "f": anc["f"],
        "c": a * anc["c"] + m * ml["c"],
        "engine": "Hybrid (CSV + ML)",
    }
    fr_h, s11_h, bw_h, status_h, vswr_h = vna_measure(out["f"], out["c"])
    out["fr"] = fr_h
    out["s11"] = s11_h
    out["bw"] = bw_h
    out["status"] = status_h
    out["v"] = vswr_h
    return out


def forward_physics_first(lp, wp, shape_id, fwd, s_geo, s_perf, db, use_ml_refine=False):
    anc = forward_anchor(lp, wp, shape_id, db)
    if anc is None:
        if fwd is None:
            return None  # no ML model and no CSV anchor
        ml = forward_ml(lp, wp, shape_id, fwd, s_geo, s_perf)
        ml["engine"] = "ML-only (no CSV anchor)"
        return ml
    anc["engine"] = f'{anc.get("anchor_mode", "CSV")}-physics'
    if not use_ml_refine or fwd is None:
        return anc
    mixed = forward_best(lp, wp, shape_id, fwd, s_geo, s_perf, db)
    mixed["engine"] = f'{mixed.get("engine", "Hybrid")} + refine'
    return mixed


def forward_physics_first_v2(lp, wp, shape_id, v2_fwd, v2_dip, s_geo, s_perf, db,
                              use_ml_refine=False, blend_window_mhz=50, anchor_strength=1.0):
    """Two-Brain 2.0: CSV anchoring as primary, specialist as dip enhancer."""
    # Get CSV anchor data first (this is the ground truth)
    anc = forward_anchor(lp, wp, shape_id, db)

    if anc is None:
        # No CSV anchor available — pure model prediction
        ml = engine_v2.forward_v2(lp, wp, shape_id, v2_fwd, v2_dip, s_geo, s_perf,
                                   use_anchor=True, blend_window_mhz=blend_window_mhz,
                                   anchor_strength=anchor_strength)
        # Report which brains actually fired. Labeling this "Two-Brain 2.0" when the
        # specialist pickle is missing is how the UI came to overstate the method.
        ml["engine"] = ("Two-Brain 2.0 (no CSV anchor)" if ml.get("used_specialist")
                        else "Main brain only (no CSV anchor)")
        return ml

    # We have CSV data — use it as the base (CSV is ground truth)
    # Get the curve data from the anchor
    curve_cols, f_axis = curve_columns(db)
    subset = db[db["Antenna_ID"] == shape_id].copy()
    subset["dist"] = np.hypot(subset["Lp"] - lp, subset["Wp"] - wp)
    nearest = subset.nsmallest(1, "dist").iloc[0]
    csv_curve = nearest[curve_cols].to_numpy(dtype=float)

    # Gain and Efficiency MUST be interpolated with the same weights as the S11 curve.
    # forward_anchor() -> weighted_blend_from_rows() already produces correctly weighted
    # anc["gain"]/anc["eff"]. Reading them off the single `nearest` row was 0th-order
    # (nearest-neighbour) while fr/s11/bw/curve were 1st-order (bilinear) -- an internal
    # inconsistency that silently degraded two of the six reported numbers.
    # The nearest row is used only as a NaN fallback when the CSV lacks those columns.
    def _interp_perf(key, col):
        v = float(anc.get(key, float("nan")))
        if not np.isfinite(v) and col in nearest.index:
            v = float(nearest[col])
        return v

    # CRITICAL: If CSV anchor is very close (< 0.6mm), skip specialist entirely
    # The CSV data IS the ground truth — no need for ML override
    if anc["dist"] <= ML_BLEND_RADIUS_MM:
        # Pure CSV anchor — no specialist override needed
        result = {
            "fr": anc["fr"], "s11": anc["s11"], "bw": anc["bw"],
            "gain": _interp_perf("gain", "Gain_at_fr"),
            "eff": _interp_perf("eff", "Eff_at_fr"),
            "status": anc["status"], "f": anc["f"], "c": anc["c"], "v": anc["v"],
            "engine": f'{anc.get("anchor_mode", "CSV")}-anchored',
        }
    else:
        # Far from CSV data — use specialist to enhance dip prediction
        result = engine_v2.forward_v2_with_csv_anchor(
            lp, wp, shape_id, v2_fwd, v2_dip, s_geo, s_perf,
            csv_curve=csv_curve, csv_f_axis=f_axis,
            use_anchor=True, blend_window_mhz=blend_window_mhz,
            anchor_strength=anchor_strength
        )
        result["gain"] = _interp_perf("gain", "Gain_at_fr")
        result["eff"] = _interp_perf("eff", "Eff_at_fr")
        # This string used to be hardcoded to "CSV-bilinear + Two-Brain 2.0 specialist"
        # regardless of whether the specialist existed or contributed anything. It now
        # reports what actually ran, so the UI cannot claim a method it did not use.
        _mode = anc.get("anchor_mode", "CSV")
        result["engine"] = (f"{_mode} + dip specialist" if result.get("used_specialist")
                            else f"{_mode} (CST interpolation only)")

        # --- Neural refinement (previously a dead parameter in this branch) ---
        # Only meaningful beyond the 0.6 mm CST-exact radius, which is exactly the
        # branch we are in. Blends the surrogate's curve into the CST anchor 75/25,
        # matching the weighting already used by forward_best() on the v1 path.
        if use_ml_refine and v2_fwd is not None:
            ml = engine_v2.forward_v2(
                lp, wp, shape_id, v2_fwd, v2_dip, s_geo, s_perf,
                use_anchor=False, verbose=0,
            )
            if len(ml["c"]) == len(result["c"]):
                m = float(ML_BLEND_WEIGHT)
                a = 1.0 - m
                result["c"] = a * np.asarray(result["c"], dtype=float) + m * np.asarray(ml["c"], dtype=float)
                if len(ml["v"]) == len(result["v"]):
                    result["v"] = a * np.asarray(result["v"], dtype=float) + m * np.asarray(ml["v"], dtype=float)
                fr_m, s11_m, bw_m, status_m, _ = vna_measure(result["f"], result["c"])
                result["fr"], result["s11"], result["bw"], result["status"] = fr_m, s11_m, bw_m, status_m
                if np.isfinite(ml.get("gain", float("nan"))) and np.isfinite(result["gain"]):
                    result["gain"] = a * result["gain"] + m * float(ml["gain"])
                if np.isfinite(ml.get("eff", float("nan"))) and np.isfinite(result["eff"]):
                    result["eff"] = a * result["eff"] + m * float(ml["eff"])
                result["engine"] += (f" + neural model "
                                     f"({int((1 - m) * 100)}/{int(m * 100)} CST/model)")

    result["near_row"] = {
        "lp": float(nearest["Lp"]),
        "wp": float(nearest["Wp"]),
        "fr": float(nearest["fr (GHz)"]) if "fr (GHz)" in nearest.index else np.nan,
        "s11": float(nearest["S11_min"]) if "S11_min" in nearest.index else np.nan,
        "dist": float(nearest["dist"]),
    }

    return result


def nearest_csv_row(db, lp, wp, shape_id):
    subset = db[db["Antenna_ID"] == shape_id].copy()
    if subset.empty:
        return None
    subset["dist"] = np.hypot(subset["Lp"] - lp, subset["Wp"] - wp)
    return subset.nsmallest(1, "dist").iloc[0]


def run_engine_self_test(_db, sample_size=220, seed=42, fr_tol_pct=2.0):
    """Leave-one-out fidelity check against the CST dataset.

    IMPORTANT: each scored row is REMOVED from the lookup table before the engine is
    asked to predict it (`exclude_idx=idx`). The previous version sampled rows from
    `db` and then queried those same rows, so `forward_anchor` took its "CSV-exact"
    branch and returned the ground-truth row unchanged -- every error was exactly
    zero by construction and the panel validated nothing. Holding the row out forces
    the engine to interpolate from neighbouring CST points, which is the quantity
    that actually matters: how well it predicts a geometry it has never seen.

    `_db` is underscore-prefixed so Streamlit does not hash the 7.7 MB frame; the
    cache key is just (sample_size, seed, fr_tol_pct).
    """
    db = _db
    curve_cols, f_axis = curve_columns(db)
    if len(curve_cols) < 10:
        return None

    n = min(int(sample_size), len(db))
    test_df = db.sample(n, random_state=int(seed))

    recs = []
    for idx, row in test_df.iterrows():
        sid = int(row["Antenna_ID"])
        lp = float(row["Lp"])
        wp = float(row["Wp"])
        pred = forward_anchor(lp, wp, sid, db, exclude_idx=idx)   # <-- leave-one-out
        if pred is None:
            continue
        true_curve = row[curve_cols].to_numpy(dtype=float)
        f_true, true_smooth = apply_dsp_polishing(f_axis, true_curve)
        fr_t, s11_t, bw_t, _, _ = vna_measure(f_true, true_smooth)

        def _g(col, key):
            t = float(row[col]) if col in row.index else float("nan")
            p = pred.get(key, float("nan"))
            p = float(p) if p is not None else float("nan")
            return t, p

        gain_t, gain_p = _g("Gain_at_fr", "gain")
        eff_t, eff_p = _g("Eff_at_fr", "eff")
        recs.append((fr_t, float(pred["fr"]), s11_t, float(pred["s11"]),
                     bw_t, float(pred["bw"]), gain_t, gain_p, eff_t, eff_p,
                     str(pred.get("anchor_mode", "?"))))

    if not recs:
        return None

    arr = np.array([r[:10] for r in recs], dtype=float)
    modes = pd.Series([r[10] for r in recs]).value_counts().to_dict()

    def _stats(t, p, scale=1.0):
        m = np.isfinite(t) & np.isfinite(p)
        if int(m.sum()) < 3:
            return None
        t_, p_ = t[m], p[m]
        err = np.abs(p_ - t_) * scale
        ss_res = float(np.sum((p_ - t_) ** 2))
        ss_tot = float(np.sum((t_ - t_.mean()) ** 2))
        return {
            "n": int(m.sum()),
            "mae": float(err.mean()),
            "p90": float(np.percentile(err, 90)),
            "max": float(err.max()),
            "r2": float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan"),
        }

    fr = _stats(arr[:, 0], arr[:, 1], 1000.0)    # GHz -> MHz
    s11 = _stats(arr[:, 2], arr[:, 3], 1.0)      # dB
    bw = _stats(arr[:, 4], arr[:, 5], 1000.0)    # GHz -> MHz
    gain = _stats(arr[:, 6], arr[:, 7], 1.0)     # dBi
    eff = _stats(arr[:, 8], arr[:, 9], 100.0)    # fraction -> %

    ok = np.isfinite(arr[:, 0]) & np.isfinite(arr[:, 1]) & (np.abs(arr[:, 0]) > 1e-9)
    rel = np.abs(arr[ok, 1] - arr[ok, 0]) / np.abs(arr[ok, 0]) * 100.0
    fr_pass_pct = float((rel <= float(fr_tol_pct)).mean() * 100.0) if rel.size else float("nan")

    def _mae(s):
        return s["mae"] if s else float("nan")

    return {
        "n": len(recs),
        "method": "leave-one-out",
        "fr_tol_pct": float(fr_tol_pct),
        "fr": fr, "s11": s11, "bw": bw, "gain": gain, "eff": eff,
        "fr_pass_pct": fr_pass_pct,
        "anchor_modes": modes,
        # true/predicted pairs for the parity plot (truth first, prediction second)
        "scatter": {
            "fr": (arr[:, 0].tolist(), arr[:, 1].tolist()),
            "gain": (arr[:, 6].tolist(), arr[:, 7].tolist()),
        },
        # flat keys kept for backwards compatibility
        "fr_mae_mhz": _mae(fr),
        "s11_mae_db": _mae(s11),
        "bw_mae_mhz": _mae(bw),
    }


def run_engine_ab_test(_db, _fwd, _s_geo, _s_perf, sample_size=150, seed=42):
    """Score the two prediction paths against each other on identical held-out points.

      Path 1 -- CST interpolation : forward_anchor() with the scored row removed
      Path 2 -- neural surrogate  : forward_ml() using the trained Keras model

    The app ships both, but only the CST path was ever benchmarked, so there was no
    evidence for which one should be the default answer shown to users. The model's
    training-time accuracy was measured on its own held-out split, which is not the
    same as measuring it here, inside this app, against the same geometries.

    This produces that evidence. Returns None if no model is loaded.
    """
    db, fwd, s_geo, s_perf = _db, _fwd, _s_geo, _s_perf
    if fwd is None:
        return None
    curve_cols, f_axis = curve_columns(db)
    if len(curve_cols) < 10:
        return None

    test = db.sample(min(int(sample_size), len(db)), random_state=int(seed))
    recs = []
    for idx, row in test.iterrows():
        sid, lp, wp = int(row["Antenna_ID"]), float(row["Lp"]), float(row["Wp"])

        truth_curve = row[curve_cols].to_numpy(dtype=float)
        f_t, c_t = apply_dsp_polishing(f_axis, truth_curve)
        fr_t, s11_t, bw_t, _, _ = vna_measure(f_t, c_t)

        p_csv = forward_anchor(lp, wp, sid, db, exclude_idx=idx)
        if p_csv is None:
            continue
        try:
            p_ml = forward_ml(lp, wp, sid, fwd, s_geo, s_perf)
        except Exception as e:
            print(f"[AB] model path failed: {e}")
            return None

        recs.append((
            fr_t, float(p_csv["fr"]), float(p_ml["fr"]),
            s11_t, float(p_csv["s11"]), float(p_ml["s11"]),
            bw_t, float(p_csv["bw"]), float(p_ml["bw"]),
            float(row["Gain_at_fr"]) if "Gain_at_fr" in row.index else float("nan"),
            float(p_csv.get("gain", float("nan"))), float(p_ml.get("gain", float("nan"))),
        ))

    if len(recs) < 5:
        return None

    a = np.array(recs, dtype=float)

    def _mae(ti, pi):
        m = np.isfinite(a[:, ti]) & np.isfinite(a[:, pi])
        if int(m.sum()) < 3:
            return float("nan")
        return float(np.mean(np.abs(a[m, pi] - a[m, ti])))

    return {
        "n": len(a),
        "csv": {
            "fr_mhz": _mae(0, 1) * 1000.0, "s11_db": _mae(3, 4),
            "bw_mhz": _mae(6, 7) * 1000.0, "gain_dbi": _mae(9, 10),
        },
        "model": {
            "fr_mhz": _mae(0, 2) * 1000.0, "s11_db": _mae(3, 5),
            "bw_mhz": _mae(6, 8) * 1000.0, "gain_dbi": _mae(9, 11),
        },
    }



def run_inverse_solver(target_fr, family_name, priority, fwd, s_geo, s_perf, db, half_span=1.5, step=0.25):
    ids = FAMILY_MAP[family_name]
    results = []
    for shape_id in ids:
        subset = db[db["Antenna_ID"] == shape_id].copy()
        if subset.empty:
            continue
        subset["df"] = np.abs(subset["fr (GHz)"] - target_fr)
        anchor = subset.sort_values("df").iloc[0]
        lp0, wp0 = float(anchor["Lp"]), float(anchor["Wp"])
        lp_grid = np.arange(max(5.0, lp0 - half_span), min(40.0, lp0 + half_span) + 1e-9, step)
        wp_grid = np.arange(max(5.0, wp0 - half_span), min(40.0, wp0 + half_span) + 1e-9, step)
        best_local = None
        for lp in lp_grid:
            for wp in wp_grid:
                pred = forward_physics_first(float(lp), float(wp), shape_id, fwd, s_geo, s_perf, db, use_ml_refine=False)
                fr_err = abs(pred["fr"] - target_fr)
                status_pen = 0.04 if pred["status"] != "WORKING" else 0.0
                if priority == "Maximize Gain":
                    score = fr_err + status_pen - 0.015 * float(np.nan_to_num(pred["gain"], nan=0.0))
                elif priority == "Maximize Bandwidth":
                    score = fr_err + status_pen - 0.010 * float(np.nan_to_num(pred["bw"], nan=0.0))
                else:
                    # Balanced profile: prioritize frequency match, then stable bandwidth/gain.
                    score = fr_err + status_pen - 0.006 * float(np.nan_to_num(pred["gain"], nan=0.0)) - 0.004 * float(np.nan_to_num(pred["bw"], nan=0.0))
                if best_local is None or score < best_local["score"]:
                    best_local = {
                        "shape_id": shape_id,
                        "lp": float(lp),
                        "wp": float(wp),
                        "fr": float(pred["fr"]),
                        "err": float(abs(pred["fr"] - target_fr)),
                        "gain": float(np.nan_to_num(pred["gain"], nan=0.0)),
                        "bw": float(np.nan_to_num(pred["bw"], nan=0.0)),
                        "status": pred["status"],
                        "score": float(score),
                    }
        if best_local:
            results.append(best_local)
    if not results:
        return None
    return pd.DataFrame(results).sort_values("err").iloc[0]


def run_inverse_self_test(db, fwd, s_geo, s_perf, per_family=3, fast_mode=True):
    rows = []
    rng = np.random.default_rng(42)
    priorities = ["Balanced Profile", "Maximize Gain", "Maximize Bandwidth"]
    for family in FAMILY_MAP.keys():
        subset = db[db["Antenna_ID"].isin(FAMILY_MAP[family])]
        if subset.empty:
            continue
        pick = subset.sample(min(per_family, len(subset)), random_state=42)
        for _, r in pick.iterrows():
            tfr = float(r["fr (GHz)"])
            pr = priorities[int(rng.integers(0, len(priorities)))]
            if fast_mode:
                best = run_inverse_solver(
                    tfr, family, pr, fwd, s_geo, s_perf, db,
                    half_span=1.0, step=0.75
                )
            else:
                best = run_inverse_solver(
                    tfr, family, pr, fwd, s_geo, s_perf, db,
                    half_span=1.5, step=0.25
                )
            if best is None:
                continue
            rows.append({
                "family": family,
                "priority": pr,
                "target_fr": tfr,
                "pred_fr": float(best["fr"]),
                "err_mhz": abs(float(best["fr"]) - tfr) * 1000.0,
            })
    if not rows:
        return None, None
    df = pd.DataFrame(rows)
    summary = {
        "tests": int(len(df)),
        "mean_err_mhz": float(df["err_mhz"].mean()),
        "p90_err_mhz": float(df["err_mhz"].quantile(0.90)),
        "max_err_mhz": float(df["err_mhz"].max()),
    }
    fam = df.groupby("family")["err_mhz"].mean().reset_index().rename(columns={"err_mhz": "mean_err_mhz"})
    return summary, fam


def run_startup_healthcheck(_db, _fwd, _s_geo, _s_perf):
    """Boot sanity check. Cached for the life of the process.

    It used to run on EVERY Streamlit rerun -- a full model.predict() (measured
    ~56 ms even for a trivial graph, more for this one), two curve_columns() scans
    and a spline fit, on every slider tick. A boot check only needs to run at boot.
    Args are underscore-prefixed so Streamlit does not try to hash a Keras model.
    """
    db, fwd, s_geo, s_perf = _db, _fwd, _s_geo, _s_perf
    report = {"ok": True, "checks": []}
    try:
        csv_ok = db is not None and len(db) > 0
        report["checks"].append(("CSV loaded", csv_ok))
        report["checks"].append(("Shape coverage", csv_ok and "Antenna_ID" in db.columns and db["Antenna_ID"].nunique() >= 12))
        if not csv_ok:
            report["checks"].append(("Runtime exception", False))
            report["ok"] = False
            return report
        test_row = db.sample(1, random_state=7).iloc[0]
        sid = int(test_row["Antenna_ID"])
        lp = float(test_row["Lp"])
        wp = float(test_row["Wp"])
        x = np.zeros((1, 14), dtype=float)
        x[0, 0], x[0, 1], x[0, 1 + sid] = lp, wp, 1.0
        x_scaled = s_geo.transform(x)
        if fwd is not None:
            y = fwd.predict(x_scaled, verbose=0)
            report["checks"].append(("Forward output heads", len(y) == 2 and y[0].shape[-1] == 4))
        else:
            report["checks"].append(("Forward output heads", True))  # CSV-only mode
        pred = forward_physics_first(lp, wp, sid, fwd, s_geo, s_perf, db, use_ml_refine=False)
        if pred is not None:
            report["checks"].append(("Physics engine run", np.isfinite(pred["fr"]) and np.isfinite(pred["s11"])))
            report["checks"].append(("Curve length", len(pred["f"]) == 1000 and len(pred["c"]) == 1000))
        else:
            report["checks"].append(("Physics engine run", False))  # No CSV anchor and no ML model
            report["checks"].append(("Curve length", False))
    except Exception:
        report["checks"].append(("Runtime exception", False))
    report["ok"] = all(v for _, v in report["checks"])
    return report



def clear_loader_caches() -> None:
    """Clear only process loader caches; useful for controlled test setup."""
    load_brains.cache_clear()
    load_data.cache_clear()
