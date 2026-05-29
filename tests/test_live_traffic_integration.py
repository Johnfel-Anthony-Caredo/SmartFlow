import unittest
from pathlib import Path


class TestLiveTrafficIntegration(unittest.TestCase):
    def test_live_traffic_page_is_routed_and_uses_svg_renderer(self):
        app_text = Path("app.py").read_text(encoding="utf-8")
        page_text = Path("pages/live_traffic.py").read_text(encoding="utf-8")
        sidebar_text = Path("components/sidebar.py").read_text(encoding="utf-8")

        self.assertIn("live_traffic", app_text)
        self.assertIn("'/live-traffic'", app_text)
        self.assertIn("build_traffic_map", page_text)
        self.assertIn("lt-map-container", page_text)
        self.assertIn("Live Traffic", sidebar_text)

    def test_callbacks_update_dashboard_and_live_traffic_map_from_engine_state(self):
        callback_text = Path("callbacks.py").read_text(encoding="utf-8")

        self.assertIn("traffic-map-container", callback_text)
        self.assertIn("lt-map-container", callback_text)
        self.assertIn("build_traffic_map", callback_text)
        self.assertNotIn("traffic_intersection.png", callback_text)

    def test_dashboard_map_view_has_dedicated_shell_and_toggle_hook(self):
        layout_text = Path("layout.py").read_text(encoding="utf-8")
        callback_text = Path("callbacks.py").read_text(encoding="utf-8")

        self.assertIn("simulation-map-shell", layout_text)
        self.assertIn("simulation-map-legend", layout_text)
        self.assertIn("sim-viewport", layout_text)
        self.assertIn("simulation-map-shell", callback_text)

    def test_live_traffic_page_uses_map_first_operator_layout(self):
        page_text = Path("pages/live_traffic.py").read_text(encoding="utf-8")

        self.assertIn("lt-live-map-shell", page_text)
        self.assertIn("lt-live-map-meta", page_text)
        self.assertIn("lt-live-legend", page_text)
        self.assertNotIn("lt-live-phase-chip", page_text)


if __name__ == "__main__":
    unittest.main()
