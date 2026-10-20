"""Optional real-asset output regression checks captured by scripts/capture_golden.py."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "golden.json"
SCALERS = (ROOT / "scaler_geo.pkl", ROOT / "scaler_perf.pkl")
MODEL = ROOT / "forward_model_v2_curve.keras"
DATA = ROOT / "antenna_data_cleaned.csv"


def _real_assets_available() -> bool:
    return (
        all(path.is_file() and not path.read_bytes()[:32].startswith(b"version https://git-lfs") for path in SCALERS)
        and MODEL.is_file()
        and DATA.is_file()
    )


def _assert_equivalent(expected: Any, actual: Any, path: str = "response") -> None:
    if isinstance(expected, bool) or expected is None or isinstance(expected, str):
        assert actual == expected, path
    elif isinstance(expected, (int, float)):
        assert isinstance(actual, (int, float)), path
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-7), path
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), path
        for index, (left, right) in enumerate(zip(expected, actual)):
            _assert_equivalent(left, right, f"{path}[{index}]")
    elif isinstance(expected, dict):
        assert isinstance(actual, dict) and set(actual) == set(expected), path
        for key, value in expected.items():
            _assert_equivalent(value, actual[key], f"{path}.{key}")
    else:
        raise AssertionError(f"Unsupported fixture value {type(expected).__name__} at {path}")


def test_golden_api_outputs_match_real_engine() -> None:
    if not FIXTURE.is_file():
        pytest.skip("Golden fixture absent; generate on an asset-provisioned machine with python scripts/capture_golden.py")
    if not _real_assets_available():
        pytest.skip("Real scalers, forward_model_v2_curve.keras, or antenna_data_cleaned.csv are unavailable")
    pytest.importorskip("tensorflow", reason="TensorFlow is required to run golden engine checks")

    os.environ.pop("ANTDESIGNER_DISABLE_ENGINE_WARMUP", None)
    from fastapi.testclient import TestClient
    from antdesigner.api.main import app

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture.get("schema_version") == 1
    cases = fixture.get("cases", [])
    assert sum(case["endpoint"] == "/api/forward" for case in cases) >= 3
    assert sum(case["endpoint"] == "/api/inverse" for case in cases) >= 2

    os.chdir(ROOT)
    with TestClient(app) as client:
        for case in cases:
            response = client.post(case["endpoint"], json=case["request"])
            assert response.status_code == case["status_code"], case["name"]
            _assert_equivalent(case["response"], response.json(), case["name"])
