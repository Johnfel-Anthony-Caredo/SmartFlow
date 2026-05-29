import json
import subprocess
import sys
import unittest
from pathlib import Path


EXPORTER_PATH = Path("tools/export_sumo_visual_network.py")
VISUAL_NETWORK_PATH = Path("assets/generated/visual_network.json")


class TestSumoVisualNetworkExport(unittest.TestCase):
    def test_exporter_writes_visual_network_from_sumo_geometry(self):
        subprocess.run([sys.executable, str(EXPORTER_PATH)], check=True)

        network = json.loads(VISUAL_NETWORK_PATH.read_text(encoding="utf-8"))
        road_ids = {road["edge_id"] for road in network["roads"]}
        signal_ids = {signal["id"] for signal in network["signals"]}

        self.assertEqual(network["scope"]["mode"], "single_intersection")
        self.assertEqual(network["source_net"], "inter_ped.net.xml")
        self.assertIn("1337657045#0", road_ids)
        self.assertIn("-1337657045#3", road_ids)
        self.assertNotIn("1337657045#5", road_ids)
        self.assertNotIn("-1337657045#5", road_ids)
        self.assertGreaterEqual(len(network["crossings"]), 4)
        self.assertGreaterEqual(len(network["walking_areas"]), 4)
        self.assertEqual(
            signal_ids,
            {"7900968103", "7900968104", "7900968105", "7900968106"},
        )

    def test_exported_roads_keep_lane_shapes_for_three_js(self):
        subprocess.run([sys.executable, str(EXPORTER_PATH)], check=True)
        network = json.loads(VISUAL_NETWORK_PATH.read_text(encoding="utf-8"))

        first_road = network["roads"][0]
        first_lane = first_road["lanes"][0]
        first_point = first_lane["shape"][0]

        self.assertIn("bounds", network)
        self.assertLessEqual(network["bounds"]["max_x"] - network["bounds"]["min_x"], 520.0)
        self.assertLessEqual(network["bounds"]["max_y"] - network["bounds"]["min_y"], 520.0)
        self.assertIn("width", first_lane)
        self.assertIsInstance(first_point["x"], float)
        self.assertIsInstance(first_point["y"], float)


if __name__ == "__main__":
    unittest.main()
