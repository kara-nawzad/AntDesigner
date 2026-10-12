"""Static guard: copied API engine functions must remain source-identical to legacy math."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "10_web_app.py"
CORE = ROOT / "src" / "backend" / "engine_core.py"
UI_ONLY = {
    "sync_lp_from_slider",
    "sync_lp_from_input",
    "sync_wp_from_slider",
    "sync_wp_from_input",
}
API_ONLY = {"clear_loader_caches"}


def functions_from_source(source: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.FunctionDef):
            continue
        # Drop cache decorators before comparison: Streamlit cache plumbing became
        # lru_cache/no-cache integration plumbing, while bodies remain unchanged.
        normalized = ast.parse(ast.unparse(node)).body[0]
        normalized.decorator_list = []
        result[normalized.name] = ast.dump(normalized, include_attributes=False)
    return result


class EngineCoreSourceTests(unittest.TestCase):
    def test_retained_function_bodies_match_legacy_pre_ui_source(self) -> None:
        legacy_text = LEGACY.read_text(encoding="utf-8")
        pre_ui = legacy_text[:legacy_text.index("\nst.set_page_config(")]
        legacy = functions_from_source(pre_ui)
        core = functions_from_source(CORE.read_text(encoding="utf-8"))

        expected_names = set(legacy) - UI_ONLY
        copied_names = set(core) - API_ONLY
        self.assertEqual(expected_names, copied_names)
        for name in sorted(expected_names):
            self.assertEqual(legacy[name], core[name], name)

    def test_scientific_constants_match_legacy_source(self) -> None:
        legacy_text = LEGACY.read_text(encoding="utf-8")
        pre_ui = legacy_text[:legacy_text.index("\nst.set_page_config(")]

        def assignments(source: str) -> dict[str, str]:
            found: dict[str, str] = {}
            for node in ast.parse(source).body:
                if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                    continue
                found[node.targets[0].id] = ast.dump(node.value, include_attributes=False)
            return found

        names = {
            "HF_REPO", "FREQS_RAW", "RESONANCE_ALIGN", "ML_BLEND_WEIGHT", "ML_BLEND_RADIUS_MM",
            "TRAINED_MIN_MM", "TRAINED_MAX_MM", "SHAPES", "FAMILY_MAP", "KNOWN_META_COLS",
        }
        legacy = assignments(pre_ui)
        core = assignments(CORE.read_text(encoding="utf-8"))
        for name in names:
            self.assertIn(name, legacy)
            self.assertIn(name, core)
            self.assertEqual(legacy[name], core[name], name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
