#!/usr/bin/env python3
"""Capture real AntDesigner API outputs as a regression fixture.

Run only on a trusted machine with authentic scaler files and the Hugging Face
model/CST CSV already available in the repository root. This script contacts the
local API in-process; it does not deploy or contact Fly.io.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
os.chdir(ROOT)

SCALERS = (ROOT / "scaler_geo.pkl", ROOT / "scaler_perf.pkl")
MODEL = ROOT / "forward_model_v2_curve.keras"
DATA = ROOT / "antenna_data_cleaned.csv"


def require_real_assets() -> None:
    for path in SCALERS:
        if not path.is_file():
            raise SystemExit(f"Missing required scaler file: {path}")
        if path.read_bytes()[:32].startswith(b"version https://git-lfs"):
            raise SystemExit(f"{path.name} is an LFS pointer, not authentic scaler bytes")
    for path in (MODEL, DATA):
        if not path.is_file():
            raise SystemExit(f"Missing required local inference asset: {path}")


CASES = [
    {
        "name": "forward_rectangle",
        "endpoint": "/api/forward",
        "request": {"shape_id": 1, "lp": 20.0, "wp": 20.0, "use_ml_refine": True},
    },
    {
        "name": "forward_ellipse",
        "endpoint": "/api/forward",
        "request": {"shape_id": 4, "lp": 24.0, "wp": 18.0, "use_ml_refine": False},
    },
    {
        "name": "forward_triangle",
        "endpoint": "/api/forward",
        "request": {"shape_id": 7, "lp": 16.0, "wp": 25.0, "use_ml_refine": True},
    },
    {
        "name": "inverse_rectangular",
        "endpoint": "/api/inverse",
        "request": {"target_fr": 3.0, "family": "Rectangular", "priority": "Balanced Profile"},
    },
    {
        "name": "inverse_circular",
        "endpoint": "/api/inverse",
        "request": {"target_fr": 5.0, "family": "Circular", "priority": "Maximize Gain"},
    },
]


def main() -> None:
    require_real_assets()
    os.environ.pop("ANTDESIGNER_DISABLE_ENGINE_WARMUP", None)
    from fastapi.testclient import TestClient
    from antdesigner.api.main import app

    captured = []
    with TestClient(app) as client:
        for case in CASES:
            response = client.post(case["endpoint"], json=case["request"])
            if response.status_code != 200:
                raise SystemExit(
                    f"{case['name']} returned HTTP {response.status_code}; "
                    f"no golden fixture was written: {response.text}"
                )
            captured.append(
                {
                    **case,
                    "status_code": response.status_code,
                    "response": response.json(),
                }
            )

    fixture = ROOT / "tests" / "fixtures" / "golden.json"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(
        json.dumps({"schema_version": 1, "cases": captured}, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(captured)} real engine outputs to {fixture}")


if __name__ == "__main__":
    main()
