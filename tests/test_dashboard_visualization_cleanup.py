import unittest
from pathlib import Path


class TestDashboardVisualizationCleanup(unittest.TestCase):
    def test_legacy_2d_page_and_renderer_files_are_removed(self):
        app_text = Path("app.py").read_text(encoding="utf-8")
        sidebar_text = Path("components/sidebar.py").read_text(encoding="utf-8")

        legacy_module = "live" + "_traffic"
        legacy_route = "'/live" + "-traffic'"
        legacy_nav_label = "Live " + "Traffic"

        self.assertNotIn(legacy_module, app_text)
        self.assertNotIn(legacy_route, app_text)
        self.assertNotIn(legacy_nav_label, sidebar_text)
        self.assertFalse((Path("pages") / f"{legacy_module}.py").exists())
        self.assertFalse((Path("components") / ("traffic" + "_map.py")).exists())
        self.assertFalse((Path("assets") / ("traffic" + "-map.css")).exists())
        self.assertFalse((Path("assets") / ("traffic" + "_intersection.png")).exists())

    def test_callbacks_keep_three_bridge_without_2d_map_outputs(self):
        callback_text = Path("callbacks.py").read_text(encoding="utf-8")

        self.assertIn("engine-state-json", callback_text)
        self.assertIn("SmartFlowScene.update", callback_text)
        self.assertIn("three-container", callback_text)
        for token in (
            "traffic" + "-map-container",
            "lt" + "-map-container",
            "build_" + "traffic" + "_map",
            "btn" + "-map-view",
            "simulation" + "-map-shell",
            "traffic" + "_intersection.png",
        ):
            self.assertNotIn(token, callback_text)

    def test_dashboard_layout_is_three_view_only_for_now(self):
        layout_text = Path("layout.py").read_text(encoding="utf-8")

        self.assertIn("three-container", layout_text)
        self.assertIn("simulation-overlays", layout_text)
        self.assertIn("sim-viewport", layout_text)
        for token in (
            "traffic" + "-map-container",
            "simulation" + "-map-shell",
            "simulation" + "-map-legend",
            "btn" + "-map-view",
            "btn" + "-3d-view",
        ):
            self.assertNotIn(token, layout_text)

    def test_global_styles_no_longer_include_2d_map_classes(self):
        styles_text = Path("assets/styles.css").read_text(encoding="utf-8")

        for token in (
            "traffic" + "-map",
            "lt" + "-live",
            "simulation" + "-map-shell",
            "sim" + "-view-toggle",
            "map" + "-mode",
        ):
            self.assertNotIn(token, styles_text)


if __name__ == "__main__":
    unittest.main()
