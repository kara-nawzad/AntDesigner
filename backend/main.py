"""FastAPI application for the AntDesigner HTML rebuild.

The API is deliberately a thin transport layer.  Numerical work is delegated to
``backend.engine_core`` (the legacy Streamlit science copied without algorithmic
changes) and ``engine_v2.py`` (left untouched).
"""
from __future__ import annotations

import hashlib
import importlib
import math
import os
import platform
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend import aether

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
ASSETS_DIR = PROJECT_ROOT / "assets"


def _asset_version() -> str:
    """Fingerprint local browser assets so immutable caching remains deploy-safe."""
    digest = hashlib.sha256()
    for directory in (FRONTEND_DIR, ASSETS_DIR):
        for path in sorted(item for item in directory.rglob("*") if item.is_file()):
            digest.update(str(path.relative_to(PROJECT_ROOT)).encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


ASSET_VERSION = _asset_version()

# Shapes/families/priorities mirror the legacy behavior source. The public dimension
# range is intentionally constrained to the CST-backed domain below.
API_SHAPES = {
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
API_FAMILY_MAP = {
    "Rectangular": [1, 2, 3],
    "Circular": [4, 5, 6],
    "Triangular": [7, 8, 9],
    "Polygonal": [10, 11, 12],
}
API_PRIORITIES = ("Balanced Profile", "Maximize Gain", "Maximize Bandwidth")
API_TRAINED_MIN_MM = 10.0
API_TRAINED_MAX_MM = 35.0
# The public workbench deliberately accepts only the range backed by real CST data.
# The copied legacy engine retains its original 5–40 mm clamp for rollback/parity.
API_SLIDER_MIN_MM = API_TRAINED_MIN_MM
API_SLIDER_MAX_MM = API_TRAINED_MAX_MM
API_ML_BLEND_WEIGHT = 0.25
API_ML_BLEND_RADIUS_MM = 0.60


class ForwardRequest(BaseModel):
    shape_id: int
    lp: float
    wp: float
    use_ml_refine: bool = True


class InverseRequest(BaseModel):
    target_fr: float
    family: str
    priority: str


class AntennaVisualRequest(BaseModel):
    shape_id: int
    lp: float
    wp: float
    label: str = ""


class ResponseVisualRequest(BaseModel):
    f: list[float] = Field(min_length=2, max_length=2000)
    c: list[float] = Field(min_length=2, max_length=2000)
    v: list[float] = Field(min_length=2, max_length=2000)
    fr: float | None = None
    bw: float | None = None
    title: str = "Predicted Response"


class ThreeDVisualRequest(BaseModel):
    shape_id: int
    lp: float
    wp: float
    label: str = ""


class CompareEntry(BaseModel):
    label: str = Field(min_length=1, max_length=160)
    f: list[float] = Field(min_length=2, max_length=2000)
    c: list[float] = Field(min_length=2, max_length=2000)


class CompareVisualRequest(BaseModel):
    entries: list[CompareEntry] = Field(min_length=2, max_length=6)


class AetherMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class AetherRequest(BaseModel):
    messages: list[AetherMessage] = Field(min_length=1, max_length=40)
    preferred_model: str | None = Field(default=None, max_length=120)


class SelfTestRequest(BaseModel):
    sample_size: int = Field(default=220, ge=40, le=400)


class AbTestRequest(BaseModel):
    sample_size: int = Field(default=150, ge=40, le=400)


class InverseTestRequest(BaseModel):
    per_family: int = Field(default=3, ge=2, le=8)
    fast_mode: bool = True


def _finite_float(value: Any, name: str) -> float:
    """Convert a client number safely and reject NaN/infinity with a useful error."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{name} must be a number.") from exc
    if not math.isfinite(number):
        raise HTTPException(status_code=422, detail=f"{name} must be finite.")
    return number


def _validate_shape_and_dimensions(shape_id: int, lp: float, wp: float) -> tuple[float, float]:
    if shape_id not in API_SHAPES.values():
        raise HTTPException(status_code=422, detail="shape_id must be between 1 and 12.")
    lp = _finite_float(lp, "lp")
    wp = _finite_float(wp, "wp")
    if not API_SLIDER_MIN_MM <= lp <= API_SLIDER_MAX_MM:
        raise HTTPException(status_code=422, detail="lp must be between 10 and 35 mm.")
    if not API_SLIDER_MIN_MM <= wp <= API_SLIDER_MAX_MM:
        raise HTTPException(status_code=422, detail="wp must be between 10 and 35 mm.")
    return lp, wp


def json_safe(value: Any) -> Any:
    """Convert numpy/pandas values and non-finite floats to browser-safe JSON."""
    # Imports stay local so /health can answer even when optional ML dependencies
    # have not initialized yet.
    try:
        import numpy as np
        import pandas as pd
    except Exception:  # pragma: no cover - only used in a missing-dependency state
        np = None
        pd = None

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if np is not None and isinstance(value, np.generic):
        return json_safe(value.item())
    if np is not None and isinstance(value, np.ndarray):
        return [json_safe(item) for item in value.tolist()]
    if pd is not None and isinstance(value, pd.DataFrame):
        return json_safe(value.to_dict(orient="records"))
    if pd is not None and isinstance(value, pd.Series):
        return json_safe(value.to_dict())
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return number if math.isfinite(number) else None


class EngineManager:
    """Owns one load of the unchanged engine and its data resources."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._started = False
        self._status = "warming"
        self._error: str | None = None
        self._core: Any | None = None
        self._resources: tuple[Any, Any, Any, Any, Any, Any] | None = None
        self._startup_health: dict[str, Any] | None = None

    def load_before_serving(self) -> None:
        """Load synchronously so a normally deployed page is usable on first render."""
        with self._lock:
            if self._started:
                return
            self._started = True
        self._load()

    def start_in_background(self) -> None:
        """Opt-in development mode for environments that intentionally defer loading."""
        with self._lock:
            if self._started:
                return
            self._started = True
            threading.Thread(target=self._load, name="antdesigner-engine-loader", daemon=True).start()

    def mark_warmup_disabled(self) -> None:
        """Make test/preview-only disabled warmup explicit rather than endlessly pending."""
        with self._lock:
            self._started = True
            self._status = "error"
            self._error = "Engine warm-up is disabled for this runtime."

    def _load(self) -> None:
        try:
            # Original loaders use project-relative model/data paths. Docker's
            # WORKDIR is /app; this also makes local uvicorn invocation reliable.
            os.chdir(PROJECT_ROOT)
            core = importlib.import_module("backend.engine_core")
            fwd, s_geo, s_perf, v2_fwd, v2_dip_specialist = core.load_brains()
            db = core.load_data()
            if db is None:
                raise RuntimeError("CSV database not found after the existing loader ran.")
            startup_health = core.run_startup_healthcheck(db, fwd, s_geo, s_perf)
            with self._lock:
                self._core = core
                self._resources = (fwd, s_geo, s_perf, v2_fwd, v2_dip_specialist, db)
                self._startup_health = startup_health
                self._status = "ready"
                self._error = None
        except Exception as exc:
            # Do not send traceback/provider detail to browsers or logs. Startup
            # still completes so /health can return a clear deployment error.
            with self._lock:
                self._status = "error"
                self._error = f"Engine initialization failed ({type(exc).__name__})."

    def context(self) -> tuple[Any, tuple[Any, Any, Any, Any, Any, Any]]:
        with self._lock:
            if self._status != "ready" or self._core is None or self._resources is None:
                message = "Engine is warming up. Please retry shortly."
                if self._status == "error":
                    message = "The antenna engine is unavailable. Check the server deployment assets."
                raise HTTPException(status_code=503, detail=message)
            return self._core, self._resources

    def health(self) -> dict[str, Any]:
        with self._lock:
            fwd = v2_fwd = dip_specialist = db = None
            if self._resources is not None:
                fwd, _, _, v2_fwd, dip_specialist, db = self._resources
            return {
                "status": "ok" if self._status == "ready" else self._status,
                "engine_ready": self._status == "ready",
                "v2_loaded": bool(v2_fwd is not None),
                "model_loaded": bool(fwd is not None),
                "dip_specialist_loaded": bool(dip_specialist is not None),
                "rows": int(len(db)) if db is not None else 0,
                "aether_configured": aether.configured(),
                "startup_health": json_safe(self._startup_health),
                "message": self._error if self._status == "error" else None,
                "versions": {
                    "api": "1",
                    "python": platform.python_version(),
                },
            }


@dataclass
class ValidationJob:
    id: str
    kind: str
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    result: Any = None
    csv_text: str | None = None
    error: str | None = None


class JobManager:
    """Single-worker validation queue: protects a small Fly shared CPU VM."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: dict[str, ValidationJob] = {}
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="antdesigner-validation")

    def submit(self, kind: str, work: Callable[[], tuple[Any, str | None]]) -> ValidationJob:
        job = ValidationJob(id=uuid.uuid4().hex, kind=kind)
        with self._lock:
            self._jobs[job.id] = job

        def runner() -> None:
            with self._lock:
                job.status = "running"
                job.started_at = time.time()
            try:
                result, csv_text = work()
                with self._lock:
                    job.result = result
                    job.csv_text = csv_text
                    job.status = "completed"
                    job.finished_at = time.time()
            except Exception as exc:
                with self._lock:
                    job.status = "failed"
                    job.error = f"Validation failed ({type(exc).__name__})."
                    job.finished_at = time.time()

        self._executor.submit(runner)
        return job

    def get(self, job_id: str) -> ValidationJob:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Validation job not found.")
            return job


engine_manager = EngineManager()
job_manager = JobManager()

app = FastAPI(
    title="AntDesigner API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


@app.on_event("startup")
def start_engine_before_serving() -> None:
    """Default to ready-only startup; opt into async warmup only for development."""
    if os.getenv("ANTDESIGNER_DISABLE_ENGINE_WARMUP", "").lower() in {"1", "true", "yes"}:
        engine_manager.mark_warmup_disabled()
    elif os.getenv("ANTDESIGNER_BACKGROUND_ENGINE_WARMUP", "").lower() in {"1", "true", "yes"}:
        engine_manager.start_in_background()
    else:
        engine_manager.load_before_serving()


@app.middleware("http")
async def cache_static_assets(request: Request, call_next: Callable[..., Any]) -> Response:
    response = await call_next(request)
    path = request.url.path
    if path in {"/", "/index.html"}:
        response.headers["Cache-Control"] = "no-cache"
    elif path.startswith(("/static/", "/assets/")):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@app.exception_handler(RequestValidationError)
async def request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request input.", "errors": json_safe(exc.errors())},
    )


@app.exception_handler(Exception)
async def unhandled_error(_: Request, __: Exception) -> JSONResponse:
    # API routes should never expose tracebacks to a browser.
    return JSONResponse(status_code=500, content={"detail": "The server could not complete that request."})


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, Any]:
    """Immediate deployment/UI health state; works while the model loads."""
    return engine_manager.health()


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    return {
        "shapes": [{"label": label, "id": shape_id} for label, shape_id in API_SHAPES.items()],
        "families": API_FAMILY_MAP,
        "priorities": list(API_PRIORITIES),
        "slider_range_mm": {"min": API_SLIDER_MIN_MM, "max": API_SLIDER_MAX_MM, "step": 0.01},
        "target_frequency_range_ghz": {"min": 1.0, "max": 7.0, "step": 0.01},
        "trained_range_mm": {"min": API_TRAINED_MIN_MM, "max": API_TRAINED_MAX_MM},
        "ml_blend_weight": API_ML_BLEND_WEIGHT,
        "ml_blend_radius_mm": API_ML_BLEND_RADIUS_MM,
    }


def _nearest_row_payload(row: Any) -> dict[str, float] | None:
    if row is None:
        return None
    return {
        "lp": float(row["Lp"]),
        "wp": float(row["Wp"]),
        "fr": float(row["fr (GHz)"]) if "fr (GHz)" in row.index else float("nan"),
        "s11": float(row["S11_min"]) if "S11_min" in row.index else float("nan"),
        "dist": float(row["dist"]),
    }


def _neural_note(result: dict[str, Any], requested: bool) -> str:
    """Mirror the legacy forward-panel state selection exactly."""
    if not requested:
        return "off"
    engine = str(result.get("engine", ""))
    if "Hybrid" in engine or "refine" in engine:
        return "active"
    near = result.get("near_row")
    if isinstance(near, dict) and float(near.get("dist", 999.0)) <= API_ML_BLEND_RADIUS_MM:
        return "not_applied_near_cst"
    return "not_applied"


@app.post("/api/forward")
def forward(payload: ForwardRequest) -> dict[str, Any]:
    lp, wp = _validate_shape_and_dimensions(payload.shape_id, payload.lp, payload.wp)
    core, resources = engine_manager.context()
    fwd, s_geo, s_perf, v2_fwd, v2_dip_specialist, db = resources

    # This is the exact branch used by the legacy Forward button.
    use_v2 = v2_fwd is not None
    if use_v2:
        result = core.forward_physics_first_v2(
            lp,
            wp,
            payload.shape_id,
            v2_fwd,
            v2_dip_specialist,
            s_geo,
            s_perf,
            db,
            use_ml_refine=payload.use_ml_refine,
            blend_window_mhz=30,
            anchor_strength=0.3,
        )
    else:
        result = core.forward_physics_first(
            lp,
            wp,
            payload.shape_id,
            fwd,
            s_geo,
            s_perf,
            db,
            use_ml_refine=payload.use_ml_refine,
        )

    if result is None:
        raise HTTPException(status_code=503, detail="No CSV anchor or trained model is available.")

    near = core.nearest_csv_row(db, lp, wp, payload.shape_id)
    result = dict(result)
    result.update(
        {
            "lp": lp,
            "wp": wp,
            "id": payload.shape_id,
            "shape_id": payload.shape_id,
            "use_ml_refine": payload.use_ml_refine,
            "use_v2": use_v2,
            "near_row": _nearest_row_payload(near),
            "out_of_range": core.out_of_training_range(lp, wp),
        }
    )
    result["neural_note"] = _neural_note(result, payload.use_ml_refine)
    result["vswr_at_min"] = float(result["v"][int(result["c"].argmin())])
    return json_safe(result)


def _within_public_geometry(lp: Any, wp: Any) -> bool:
    return (
        API_SLIDER_MIN_MM <= float(lp) <= API_SLIDER_MAX_MM
        and API_SLIDER_MIN_MM <= float(wp) <= API_SLIDER_MAX_MM
    )


def _bounded_inverse_axis(center: float) -> tuple[float, ...]:
    """Match the legacy 0.25 mm inverse grid, clipped to the public CST domain."""
    lower = max(API_SLIDER_MIN_MM, center - 1.5)
    upper = min(API_SLIDER_MAX_MM, center + 1.5)
    if upper < lower:
        return ()
    count = int(math.floor((upper - lower) / 0.25 + 1e-9))
    return tuple(lower + index * 0.25 for index in range(count + 1))


def _legacy_nan_to_zero(value: Any) -> float:
    """Use the same scalar conversion used by the untouched inverse solver."""
    # Keep this import lazy so a bare /health endpoint remains available during a
    # missing-dependency deployment diagnosis. A real inverse request requires
    # NumPy/TensorFlow anyway, and NumPy is pinned in requirements.txt.
    import numpy as np

    return float(np.nan_to_num(value, nan=0.0))


def _run_bounded_inverse_solver(
    core: Any,
    target_fr: float,
    family: str,
    priority: str,
    fwd: Any,
    s_geo: Any,
    s_perf: Any,
    db: Any,
) -> dict[str, Any] | None:
    """Re-run the legacy scoring policy only inside the user-requested 10–35 mm domain.

    ``engine_core.run_inverse_solver`` remains unchanged for source parity and
    rollback. This adapter is invoked only when that legacy 5–40 mm search selects
    an unsupported result. It calls the same unchanged forward engine and retains
    the same anchor, grid step, priorities, scores, and per-family selection rules.
    """
    results: list[dict[str, Any]] = []
    for shape_id in API_FAMILY_MAP[family]:
        subset = db[db["Antenna_ID"] == shape_id].copy()
        if subset.empty:
            continue
        subset["df"] = (subset["fr (GHz)"] - target_fr).abs()
        anchor = subset.sort_values("df").iloc[0]
        lp_values = _bounded_inverse_axis(float(anchor["Lp"]))
        wp_values = _bounded_inverse_axis(float(anchor["Wp"]))
        if not lp_values or not wp_values:
            continue

        best_local: dict[str, Any] | None = None
        for lp in lp_values:
            for wp in wp_values:
                prediction = core.forward_physics_first(
                    float(lp), float(wp), shape_id, fwd, s_geo, s_perf, db, use_ml_refine=False
                )
                if prediction is None:
                    continue
                fr_err = abs(float(prediction["fr"]) - target_fr)
                status_penalty = 0.04 if prediction["status"] != "WORKING" else 0.0
                if priority == "Maximize Gain":
                    score = fr_err + status_penalty - 0.015 * _legacy_nan_to_zero(prediction["gain"])
                elif priority == "Maximize Bandwidth":
                    score = fr_err + status_penalty - 0.010 * _legacy_nan_to_zero(prediction["bw"])
                else:
                    score = (
                        fr_err
                        + status_penalty
                        - 0.006 * _legacy_nan_to_zero(prediction["gain"])
                        - 0.004 * _legacy_nan_to_zero(prediction["bw"])
                    )
                if best_local is None or score < best_local["score"]:
                    best_local = {
                        "shape_id": shape_id,
                        "lp": float(lp),
                        "wp": float(wp),
                        "fr": float(prediction["fr"]),
                        "err": float(fr_err),
                        "gain": _legacy_nan_to_zero(prediction["gain"]),
                        "bw": _legacy_nan_to_zero(prediction["bw"]),
                        "status": prediction["status"],
                        "score": float(score),
                    }
        if best_local is not None:
            results.append(best_local)
    return min(results, key=lambda result: result["err"]) if results else None


@app.post("/api/inverse")
def inverse(payload: InverseRequest) -> dict[str, Any]:
    target_fr = _finite_float(payload.target_fr, "target_fr")
    if not 1.0 <= target_fr <= 7.0:
        raise HTTPException(status_code=422, detail="target_fr must be between 1 and 7 GHz.")
    if payload.family not in API_FAMILY_MAP:
        raise HTTPException(status_code=422, detail="Unknown shape family.")
    if payload.priority not in API_PRIORITIES:
        raise HTTPException(status_code=422, detail="Unknown optimization priority.")

    core, resources = engine_manager.context()
    fwd, s_geo, s_perf, _, _, db = resources
    best = core.run_inverse_solver(target_fr, payload.family, payload.priority, fwd, s_geo, s_perf, db)
    if best is None:
        raise HTTPException(status_code=422, detail="No valid inverse-design candidate was found.")
    if not _within_public_geometry(best["lp"], best["wp"]):
        best = _run_bounded_inverse_solver(core, target_fr, payload.family, payload.priority, fwd, s_geo, s_perf, db)
    if best is None:
        raise HTTPException(
            status_code=422,
            detail="No CST-backed inverse candidate was found inside the 10–35 mm geometry range.",
        )

    err_pct = float(best["err"]) / max(1e-8, target_fr) * 100.0
    return json_safe(
        {
            "lp": float(best["lp"]),
            "wp": float(best["wp"]),
            "id": int(best["shape_id"]),
            "shape_id": int(best["shape_id"]),
            "fr": float(best["fr"]),
            "err": float(best["err"]),
            "err_pct": float(err_pct),
            "gain": float(best["gain"]),
            "bw": float(best["bw"]),
            "status": str(best["status"]),
            "priority": payload.priority,
            "family": payload.family,
            "target_fr": target_fr,
        }
    )


@app.post("/api/visual/antenna")
def antenna_visual(payload: AntennaVisualRequest) -> dict[str, str]:
    lp, wp = _validate_shape_and_dimensions(payload.shape_id, payload.lp, payload.wp)
    try:
        from antenna_viz import antenna_animated_html

        # Labels are canonical server metadata rather than arbitrary HTML-client input.
        label = next(label for label, sid in API_SHAPES.items() if sid == payload.shape_id)
        return {"html": antenna_animated_html(payload.shape_id, round(lp, 2), round(wp, 2), label)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The antenna visual is unavailable.") from exc


@app.post("/api/visual/response")
def response_visual(payload: ResponseVisualRequest) -> dict[str, str]:
    if not (len(payload.f) == len(payload.c) == len(payload.v)):
        raise HTTPException(status_code=422, detail="f, c, and v must have the same length.")
    try:
        from antenna_charts import s11_vswr_animated_html

        return {
            "html": s11_vswr_animated_html(
                payload.f, payload.c, payload.v, fr=payload.fr, bw=payload.bw, title=payload.title
            )
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The response visual is unavailable.") from exc


@app.post("/api/visual/3d")
def three_d_visual(payload: ThreeDVisualRequest) -> dict[str, Any]:
    lp, wp = _validate_shape_and_dimensions(payload.shape_id, payload.lp, payload.wp)
    try:
        import antenna_charts

        label = next(label for label, sid in API_SHAPES.items() if sid == payload.shape_id)
        return json_safe(antenna_charts.patch_3d_fig(payload.shape_id, lp, wp, label).to_plotly_json())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The 3D visual is unavailable.") from exc


@app.post("/api/visual/compare")
def comparison_visual(payload: CompareVisualRequest) -> dict[str, Any]:
    try:
        import antenna_charts

        entries = [{"label": entry.label, "f": entry.f, "c": entry.c} for entry in payload.entries]
        return json_safe(antenna_charts.compare_fig(entries).to_plotly_json())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The comparison visual is unavailable.") from exc


@app.get("/api/visual/design-space")
def design_space_visual(shape_id: int) -> dict[str, Any] | None:
    if shape_id not in API_SHAPES.values():
        raise HTTPException(status_code=422, detail="shape_id must be between 1 and 12.")
    _, resources = engine_manager.context()
    *_, db = resources
    try:
        import antenna_charts

        label = next(label for label, sid in API_SHAPES.items() if sid == shape_id)
        figure = antenna_charts.design_space_fig(db, shape_id, label)
        return None if figure is None else json_safe(figure.to_plotly_json())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The design-space visual is unavailable.") from exc


@app.get("/api/data-story")
def data_story() -> dict[str, Any]:
    """Small, deterministic CST data summary for the frontend's real data story."""
    _, resources = engine_manager.context()
    *_, db = resources
    required = {"Lp", "Wp", "Antenna_ID", "fr (GHz)"}
    if not required.issubset(db.columns):
        raise HTTPException(status_code=503, detail="The CST dataset does not contain the required data-story columns.")
    try:
        import numpy as np

        frame = db[["Lp", "Wp", "Antenna_ID", "fr (GHz)"]].copy()
        frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
        if frame.empty:
            raise HTTPException(status_code=503, detail="The CST dataset has no finite data-story rows.")
        sample = frame.sample(min(2000, len(frame)), random_state=42)
        values = frame["fr (GHz)"].to_numpy(dtype=float)
        counts, edges = np.histogram(values, bins=20)
        return json_safe({
            "rows": int(len(frame)),
            "histogram": {"edges": edges.tolist(), "counts": counts.tolist()},
            "scatter": {
                "lp": sample["Lp"].to_numpy(dtype=float).tolist(),
                "wp": sample["Wp"].to_numpy(dtype=float).tolist(),
                "fr": sample["fr (GHz)"].to_numpy(dtype=float).tolist(),
                "shape_id": sample["Antenna_ID"].to_numpy(dtype=int).tolist(),
            },
        })
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The CST data story is unavailable.") from exc


@app.post("/api/aether")
def aether_chat(payload: AetherRequest) -> dict[str, Any]:
    messages = [{"role": message.role, "content": message.content.strip()} for message in payload.messages]
    if any(not message["content"] for message in messages):
        raise HTTPException(status_code=422, detail="AETHER messages cannot be empty.")
    return aether.complete(messages, payload.preferred_model)


def _new_validation_job(kind: str, work: Callable[[Any, tuple[Any, Any, Any, Any, Any, Any]], tuple[Any, str | None]]) -> dict[str, Any]:
    core, resources = engine_manager.context()
    job = job_manager.submit(kind, lambda: work(core, resources))
    return {"job_id": job.id, "kind": job.kind, "status": job.status}


@app.post("/api/validate/self-test")
def validate_self_test(payload: SelfTestRequest) -> dict[str, Any]:
    def work(core: Any, resources: tuple[Any, Any, Any, Any, Any, Any]) -> tuple[Any, str | None]:
        *_, db = resources
        return core.run_engine_self_test(db, sample_size=payload.sample_size), None

    return _new_validation_job("self-test", work)


@app.post("/api/validate/ab-test")
def validate_ab_test(payload: AbTestRequest) -> dict[str, Any]:
    def work(core: Any, resources: tuple[Any, Any, Any, Any, Any, Any]) -> tuple[Any, str | None]:
        fwd, s_geo, s_perf, _, _, db = resources
        return core.run_engine_ab_test(db, fwd, s_geo, s_perf, sample_size=payload.sample_size), None

    return _new_validation_job("ab-test", work)


@app.post("/api/validate/inverse-test")
def validate_inverse_test(payload: InverseTestRequest) -> dict[str, Any]:
    def work(core: Any, resources: tuple[Any, Any, Any, Any, Any, Any]) -> tuple[Any, str | None]:
        fwd, s_geo, s_perf, _, _, db = resources
        summary, family_df = core.run_inverse_self_test(
            db, fwd, s_geo, s_perf, per_family=payload.per_family, fast_mode=payload.fast_mode
        )
        records = [] if family_df is None else family_df.to_dict(orient="records")
        csv_text = None if family_df is None else family_df.to_csv(index=False)
        return {"summary": summary, "family": records}, csv_text

    return _new_validation_job("inverse-test", work)


@app.post("/api/validate/healthcheck")
def validate_healthcheck() -> dict[str, Any]:
    def work(core: Any, resources: tuple[Any, Any, Any, Any, Any, Any]) -> tuple[Any, str | None]:
        fwd, s_geo, s_perf, _, _, db = resources
        return core.run_startup_healthcheck(db, fwd, s_geo, s_perf), None

    return _new_validation_job("healthcheck", work)


@app.get("/api/jobs/{job_id}")
def validation_job(job_id: str) -> dict[str, Any]:
    job = job_manager.get(job_id)
    return json_safe(
        {
            "job_id": job.id,
            "kind": job.kind,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "result": job.result if job.status == "completed" else None,
            "error": job.error,
            "csv_ready": bool(job.csv_text),
        }
    )


@app.get("/api/jobs/{job_id}/inverse.csv")
def inverse_validation_csv(job_id: str) -> Response:
    job = job_manager.get(job_id)
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="The inverse validation job has not finished.")
    if not job.csv_text:
        raise HTTPException(status_code=404, detail="This validation job has no CSV output.")
    return Response(
        content=job.csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="inverse_self_test_results.csv"'},
    )


@app.get("/")
@app.get("/index.html")
def index() -> Response:
    html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    return Response(
        content=html.replace("__ASSET_VERSION__", ASSET_VERSION),
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/favicon.ico")
def favicon() -> FileResponse:
    return FileResponse(ASSETS_DIR / "antdesigner_favicon.png")


# Mount static paths last so they cannot shadow API routes.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
