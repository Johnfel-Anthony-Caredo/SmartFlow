from pathlib import Path
import unittest


class TestTrafficMapStyles(unittest.TestCase):
    def test_map_styles_live_in_dedicated_stylesheet(self):
        traffic_css = Path("assets/traffic-map.css")
        global_css = Path("assets/styles.css").read_text(encoding="utf-8")

        self.assertTrue(traffic_css.exists())
        css = traffic_css.read_text(encoding="utf-8")
        self.assertIn(".traffic-map-road", css)
        self.assertIn(".traffic-map-junction-box", css)
        self.assertIn(".traffic-map-sidewalk-zone", css)
        self.assertIn(".traffic-map-crossing", css)
        self.assertIn(".traffic-map-stop-bar", css)
        self.assertIn(".traffic-map-constraint-band", css)
        self.assertIn(".traffic-map-empty-banner", css)
        self.assertNotIn(".traffic-map-road", global_css)


if __name__ == "__main__":
    unittest.main()
