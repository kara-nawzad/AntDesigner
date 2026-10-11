"""Numerical-parity check for the HTML/FastAPI rebuild.

Run this inside a fully provisioned image or checkout that has the real scaler
bytes, Keras model, and CST CSV available:

    python tests/test_parity.py

It dynamically evaluates only the pre-UI section of the untouched legacy
``10_web_app.py`` with Streamlit caching disabled, then compares those original
function bodies to HTTP responses from the new FastAPI routes.  No expected RF
numbers are hard-coded here.
"""
from __future__ import annotations

import math
import os
import sys
import types
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("ANTDESIGNER_DISABLE_ENGINE_WARMUP", "1")


def _missing_runtime_reason() -> str | None:
    required_imports = ("fastapi", "numpy", "pandas", "tensorflow", "joblib", "scipy")
    for name in required_imports:
        try:
            __import__(name)
        except Exception as exc:
            return f"{name} is unavailable ({type(exc).__name__})"
    for filename in ("scaler_geo.pkl", "scaler_perf.pkl"):
        path = ROOT / filename
        if not path.exists():
            return f"{filename} is missing"
        if path.read_bytes()[:32].startswith(b"version https://git-lfs"):
            return f"{filename} is an unresolved Git-LFS pointer"
    return None


SKIP_REASON = _missing_runtime_reason()


@unittest.skipIf(SKIP_REASON is not None, f"NOT VERIFIED: {SKIP_REASON}")
class NumericalParityTests(unittest.TestCase):
    """Compare original Streamlit-source functions against the JSON API."""

    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient

        import backend.engine_core as core
        import backend.main as main

        cls.core = core
        cls.main = main
        cls.legacy = cls._load_legacy_core()
        fwd, s_geo, s_perf, v2_fwd, v2_dip_specialist = core.load_brains()
        db = core.load_data()
        if db is None or len(db) == 0:
            raise unittest.SkipTest("NOT VERIFIED: the CST CSV could not be loaded")
        cls.resources = (fwd, s_geo, s_perf, v2_fwd, v2_dip_specialist, db)
        # The app normally gets here through its background loader.  The parity
        # test injects the same objects so API and legacy functions share models/data.
        with main.engine_manager._lock:  # test-only controlled setup
            main.engine_manager._core = core
            main.engine_manager._resources = cls.resources
            main.engine_manager._status = "ready"
            main.engine_manager._error = None
        cls.client = TestClient(main.app)

    @classmethod
    def _load_legacy_core(cls) -> types.ModuleType:
        source = (ROOT / "10_web_app.py").read_text(encoding="utf-8")
        pre_ui = source[:source.index("\nst.set_page_config(")]
        # Streamlit's caches are intentionally integration-only differences.  The
        # legacy numerical function bodies are otherwise executed as written.
        pre_ui = pre_ui.replace("@st.cache_resource", "@identity_cache")
        # Streamlit is deliberately not a production dependency. Its imports sit
        # above the legacy UI boundary but are not needed by the numerical code
        # evaluated here, so replace only those import lines for this test harness.
        pre_ui = pre_ui.replace(
            "import streamlit as st\nimport streamlit.components.v1 as components\n",
            "st = None\ncomponents = None\n",
        )
        namespace: dict[str, Any] = {
            "__name__": "legacy_streamlit_core_for_parity",
            "__file__": str(ROOT / "10_web_app.py"),
            "identity_cache": lambda function: function,
        }
        exec(compile(pre_ui, str(ROOT / "10_web_app.py"), "exec"), namespace)
        module = types.ModuleType("legacy_streamlit_core_for_parity")
        module.__dict__.update(namespace)
        return module

    @staticmethod
    def _safe(value: Any) -> Any:
        return NumericalParityTests.main.json_safe(value)

    def _legacy_forward(self, lp: float, wp: float, shape_id: int, use_ml_refine: bool) -> dict[str, Any]:
        fwd, s_geo, s_perf, v2_fwd, v2_dip_specialist, db = self.resources
        if v2_fwd is not None:
            result = self.legacy.forward_physics_first_v2(
                lp, wp, shape_id, v2_fwd, v2_dip_specialist, s_geo, s_perf, db,
                use_ml_refine=use_ml_refine, blend_window_mhz=30, anchor_strength=0.3,
            )
        else:
            result = self.legacy.forward_physics_first(
                lp, wp, shape_id, fwd, s_geo, s_perf, db, use_ml_refine=use_ml_refine,
            )
        near = self.legacy.nearest_csv_row(db, lp, wp, shape_id)
        result = dict(result)
        result["near_row"] = None if near is None else {
            "lp": float(near["Lp"]),
            "wp": float(near["Wp"]),
            "fr": float(near["fr (GHz)"]) if "fr (GHz)" in near.index else float("nan"),
            "s11": float(near["S11_min"]) if "S11_min" in near.index else float("nan"),
            "dist": float(near["dist"]),
        }
        return self._safe(result)

    def _assert_same(self, expected: Any, actual: Any, path: str = "value") -> None:
        if expected is None or actual is None:
            self.assertIs(expected, actual, path)
            return
        if isinstance(expected, str) or isinstance(actual, str):
            self.assertEqual(expected, actual, path)
            return
        if isinstance(expected, bool) or isinstance(actual, bool):
            self.assertEqual(expected, actual, path)
            return
        if isinstance(expected, dict):
            self.assertIsInstance(actual, dict, path)
            self.assertEqual(set(expected), set(actual), path)
            for key in expected:
                self._assert_same(expected[key], actual[key], f"{path}.{key}")
            return
        if isinstance(expected, (list, tuple)):
            self.assertIsInstance(actual, list, path)
            self.assertEqual(len(expected), len(actual), path)
            for index, (left, right) in enumerate(zip(expected, actual)):
                self._assert_same(left, right, f"{path}[{index}]")
            return
        self.assertTrue(
            math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=1e-9),
            f"{path}: expected {expected!r}, got {actual!r}",
        )

    def _far_inside_case(self, shape_id: int) -> tuple[float, float]:
        """Choose an in-training candidate maximally distant from CST nodes."""
        import numpy as np

        db = self.resources[-1]
        subset = db[db["Antenna_ID"] == shape_id]
        candidates = [(lp, wp) for lp in np.linspace(10.11, 34.89, 13) for wp in np.linspace(10.23, 34.77, 13)]
        lp, wp = max(
            candidates,
            key=lambda pair: float(np.min(np.hypot(subset["Lp"] - pair[0], subset["Wp"] - pair[1]))),
        )
        return float(lp), float(wp)

    def _forward_cases(self) -> list[tuple[int, float, float, bool]]:
        db = self.resources[-1]
        cases: list[tuple[int, float, float, bool]] = []
        for shape_id in range(1, 13):
            subset = db[db["Antenna_ID"] == shape_id]
            self.assertFalse(subset.empty, f"CST data is missing shape {shape_id}")
            row = subset.iloc[0]
            near = (float(row["Lp"]), float(row["Wp"]))
            far = self._far_inside_case(shape_id)
            # 48 cases total: all shapes, near/far/out-of-range, and both values
            # of the neural-refinement flag across each category.
            cases.extend([
                (shape_id, near[0], near[1], True),
                (shape_id, far[0], far[1], False),
                (shape_id, 5.0, 40.0, shape_id % 2 == 0),
                (shape_id, 40.0, 5.0, shape_id % 2 != 0),
            ])
        return cases

    def test_forward_api_matches_legacy_source_for_48_cases(self) -> None:
        compared = 0
        for shape_id, lp, wp, use_ml_refine in self._forward_cases():
            with self.subTest(shape_id=shape_id, lp=lp, wp=wp, use_ml_refine=use_ml_refine):
                expected = self._legacy_forward(lp, wp, shape_id, use_ml_refine)
                response = self.client.post(
                    "/api/forward",
                    json={"shape_id": shape_id, "lp": lp, "wp": wp, "use_ml_refine": use_ml_refine},
                )
                self.assertEqual(response.status_code, 200, response.text)
                actual = response.json()
                for key in ("fr", "bw", "s11", "gain", "eff", "status", "engine", "f", "c", "v", "near_row"):
                    self._assert_same(expected[key], actual[key], key)
                compared += 1
        self.assertGreaterEqual(compared, 40)

    def test_inverse_api_matches_legacy_source_for_all_families_priorities_and_targets(self) -> None:
        fwd, s_geo, s_perf, _, _, db = self.resources
        targets = (2.0, 3.5, 6.0)
        compared = 0
        for family in self.legacy.FAMILY_MAP:
            for priority in ("Balanced Profile", "Maximize Gain", "Maximize Bandwidth"):
                for target in targets:
                    with self.subTest(family=family, priority=priority, target=target):
                        expected = self.legacy.run_inverse_solver(target, family, priority, fwd, s_geo, s_perf, db)
                        self.assertIsNotNone(expected)
                        response = self.client.post(
                            "/api/inverse",
                            json={"target_fr": target, "family": family, "priority": priority},
                        )
                        self.assertEqual(response.status_code, 200, response.text)
                        actual = response.json()
                        for key, expected_value in {
                            "lp": float(expected["lp"]),
                            "wp": float(expected["wp"]),
                            "shape_id": int(expected["shape_id"]),
                            "fr": float(expected["fr"]),
                            "err": float(expected["err"]),
                            "gain": float(expected["gain"]),
                            "bw": float(expected["bw"]),
                            "status": str(expected["status"]),
                            "priority": priority,
                            "family": family,
                            "target_fr": target,
                        }.items():
                            self._assert_same(expected_value, actual[key], key)
                        compared += 1
        self.assertEqual(compared, 36)


if __name__ == "__main__":
    unittest.main(verbosity=2)
