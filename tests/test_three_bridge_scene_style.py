import unittest
from pathlib import Path


BRIDGE_PATH = Path("assets/three-bridge.mjs")


class TestThreeBridgeSceneStyle(unittest.TestCase):
    def test_three_bridge_has_infinitown_markers(self):
        text = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn("PerspectiveCamera", text)
        self.assertIn("worldRoot", text)
        self.assertIn("WORLD_SCALE", text)
        self.assertIn("GLTFLoader", text)
        self.assertIn("traffic_light.gltf", text)

    def test_three_container_css_exists(self):
        css = Path("assets/styles.css").read_text(encoding="utf-8")
        self.assertIn(".three-container", css)


if __name__ == "__main__":
    unittest.main()

