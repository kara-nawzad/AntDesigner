"""Asset-free structural checks for the production engine package."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "src" / "backend" / "engine_core.py"


class EngineCoreSourceTests(unittest.TestCase):
    def test_engine_exposes_expected_scientific_entry_points(self):
        source = CORE.read_text(encoding="utf-8")
        for symbol in ("load_brains", "load_data", "forward_physics_first",
                       "run_inverse_solver", "run_startup_healthcheck"):
            with self.subTest(symbol=symbol):
                self.assertIn(f"def {symbol}(", source)

    def test_production_engine_has_no_streamlit_dependency(self):
        source = CORE.read_text(encoding="utf-8")
        self.assertNotIn("import streamlit", source)


if __name__ == "__main__":
    unittest.main()
