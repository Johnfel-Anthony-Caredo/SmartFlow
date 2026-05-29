import unittest
from pathlib import Path


BRIDGE_PATH = Path("assets/three-bridge.mjs")


class TestThreeBridgeSceneStyle(unittest.TestCase):
    def test_three_bridge_loads_generated_sumo_visual_network(self):
        text = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn("PerspectiveCamera", text)
        self.assertIn("worldRoot", text)
        self.assertIn("VISUAL_NETWORK_URL", text)
        self.assertIn("/assets/generated/visual_network.json", text)
        self.assertIn("loadVisualNetwork", text)
        self.assertIn("buildRoadsFromNetwork", text)
        self.assertIn("createLaneStrip", text)
        self.assertNotIn("const ROAD_PATHS", text)
        self.assertNotIn("const INTERSECTION_POLYGON", text)
        self.assertNotIn("const CROSSWALK_SEGMENTS", text)

    def test_three_container_css_exists(self):
        css = Path("assets/styles.css").read_text(encoding="utf-8")
        self.assertIn(".three-container", css)

    def test_three_bridge_uses_sumo_entity_registries(self):
        text = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn("vehicleRegistry", text)
        self.assertIn("pedestrianRegistry", text)
        self.assertIn("constraintMarker", text)
        self.assertIn("signalRegistry", text)

    def test_callback_serializer_forwards_visual_state_to_three_bridge(self):
        text = Path("callbacks.py").read_text(encoding="utf-8")
        self.assertIn("'visual': state.get('visual', {})", text)
        self.assertIn("'scenario': state.get('scenario', {})", text)

    def test_three_bridge_uses_geometry_first_camera_and_transform(self):
        text = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn("camera.position.set(46, 54, 46)", text)
        self.assertIn("camera.lookAt(SCENE_FOCUS.x, SCENE_FOCUS.y, SCENE_FOCUS.z)", text)
        self.assertIn("configureTransform(network.bounds)", text)
        self.assertIn("worldScale", text)
        self.assertIn("sumoOrigin", text)

    def test_three_bridge_uses_procedural_clarity_assets(self):
        text = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn("createVehicleMesh", text)
        self.assertIn("createPedestrianMesh", text)
        self.assertIn("createTrafficSignalMesh", text)
        self.assertIn("createConstraintMesh", text)
        self.assertNotIn("GLTFLoader", text)
        self.assertNotIn("traffic_light.gltf", text)
        self.assertNotIn("VEHICLE_MODEL_URLS", text)
        self.assertNotIn("PEDESTRIAN_MODEL_URL", text)

    def test_generated_visual_network_is_available_for_dash_assets(self):
        network_path = Path("assets/generated/visual_network.json")
        text = network_path.read_text(encoding="utf-8")
        self.assertIn('"roads"', text)
        self.assertIn('"crossings"', text)
        self.assertIn('"signals"', text)

    def test_flat_geometry_rotates_around_vertical_axis(self):
        text = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertIn("strip.rotation.y = Math.atan2(delta.x, delta.z)", text)
        self.assertIn("marker.rotation.y = Math.atan2(delta.x, delta.z)", text)
        self.assertIn("stripe.rotation.y = Math.atan2(delta.x, delta.z)", text)

    def test_pedestrian_animation_does_not_accumulate_child_offsets(self):
        text = BRIDGE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("child.position.y +=", text)
        self.assertIn("entry.group.position.y = entry.targetPosition.y +", text)


if __name__ == "__main__":
    unittest.main()
