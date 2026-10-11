"""FastAPI shell checks that do not require model/data inference assets."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("ANTDESIGNER_DISABLE_ENGINE_WARMUP", "1")

IMPORT_ERROR = None
try:
    from fastapi.testclient import TestClient
    from backend.main import EngineManager, app
except ModuleNotFoundError as exc:  # clear standalone result on an unprovisioned host
    TestClient = None
    EngineManager = None
    app = None
    IMPORT_ERROR = exc.name


@unittest.skipIf(TestClient is None, f"NOT VERIFIED: API dependency unavailable ({IMPORT_ERROR})")
class ApiShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    def test_ready_only_loader_runs_synchronously(self) -> None:
        manager = EngineManager()
        calls: list[str] = []
        manager._load = lambda: calls.append("loaded")  # type: ignore[method-assign]
        manager.load_before_serving()
        self.assertEqual(calls, ["loaded"])
        self.assertTrue(manager._started)

    def test_health_answers_while_engine_is_not_started(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn(payload["status"], {"warming", "error", "ok"})
        self.assertIn("engine_ready", payload)
        self.assertIn("aether_configured", payload)

    def test_meta_exposes_all_current_shapes_and_inverse_options(self) -> None:
        response = self.client.get("/api/meta")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["shapes"]), 12)
        self.assertEqual(set(payload["families"]), {"Rectangular", "Circular", "Triangular", "Polygonal"})
        self.assertEqual(payload["priorities"], ["Balanced Profile", "Maximize Gain", "Maximize Bandwidth"])
        self.assertEqual(payload["slider_range_mm"], {"min": 10.0, "max": 35.0, "step": 0.01})

    def test_forward_rejects_invalid_shape_before_engine_execution(self) -> None:
        response = self.client.post("/api/forward", json={"shape_id": 13, "lp": 22.5, "wp": 18.0, "use_ml_refine": True})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "shape_id must be between 1 and 12.")

    def test_forward_rejects_dimensions_outside_the_cst_backed_range(self) -> None:
        response = self.client.post("/api/forward", json={"shape_id": 1, "lp": 9.99, "wp": 18.0, "use_ml_refine": True})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "lp must be between 10 and 35 mm.")

    def test_inverse_never_returns_a_geometry_outside_the_cst_backed_range(self) -> None:
        class OutsideRangeCore:
            @staticmethod
            def run_inverse_solver(*_args):
                return {"lp": 35.25, "wp": 18.0}

        resources = (None, None, None, None, None, object())
        with patch("backend.main.engine_manager.context", return_value=(OutsideRangeCore(), resources)):
            response = self.client.post(
                "/api/inverse",
                json={"target_fr": 3.5, "family": "Rectangular", "priority": "Balanced Profile"},
            )
        self.assertEqual(response.status_code, 422)
        self.assertIn("10–35 mm geometry range", response.json()["detail"])

    def test_index_and_static_css_are_served(self) -> None:
        index = self.client.get("/")
        self.assertEqual(index.status_code, 200)
        self.assertIn("AntDesigner — AI-Based CPW Antenna Synthesis", index.text)
        self.assertNotIn("__ASSET_VERSION__", index.text)
        self.assertIn("/static/js/app.js?v=", index.text)
        self.assertEqual(index.headers.get("cache-control"), "no-cache")
        css = self.client.get("/static/css/app.css")
        self.assertEqual(css.status_code, 200)
        self.assertIn("max-age=31536000", css.headers.get("cache-control", ""))

    def test_aether_without_a_key_returns_the_legacy_info_message(self) -> None:
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
            response = self.client.post("/api/aether", json={"messages": [{"role": "user", "content": "Hello"}]})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "not_configured")
        self.assertEqual(payload["model"], None)
        self.assertIn("Set GROQ_API_KEY", payload["reply"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
