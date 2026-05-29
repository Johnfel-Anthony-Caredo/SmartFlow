import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCOPE_PATH = Path("sumo/intersection_1/main_intersection_scope.json")
ROUTES_PATH = Path("sumo/intersection_1/designed_routes.rou.xml")
CONFIG_PATH = Path("sumo/intersection_1/inter.sumocfg")


class TestSumoNetworkScope(unittest.TestCase):
    def test_scope_selects_one_main_intersection(self):
        scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(scope["mode"], "single_intersection")
        self.assertEqual(
            scope["controlled_tls_ids"],
            ["7900968103", "7900968104", "7900968105", "7900968106"],
        )
        self.assertIn("1337657045#0", scope["route_edges"])
        self.assertIn("-1337657045#3", scope["route_edges"])
        self.assertNotIn("1337657045#5", scope["route_edges"])
        self.assertNotIn("-1337657045#5", scope["route_edges"])
        self.assertEqual(scope["visual_center"], {"x": 528.0, "y": 870.0})
        self.assertEqual(scope["visual_radius_m"], 260.0)

    def test_designed_routes_use_named_flows_instead_of_random_vehicle_list(self):
        root = ET.parse(ROUTES_PATH).getroot()
        route_ids = {route.get("id") for route in root.findall("route")}
        flow_ids = {flow.get("id") for flow in root.findall("flow")}
        vehicles = root.findall("vehicle")

        self.assertIn("west_to_east", route_ids)
        self.assertIn("east_to_west", route_ids)
        self.assertIn("north_to_south", route_ids)
        self.assertIn("south_to_north", route_ids)
        self.assertIn("emergency_west_to_east", route_ids)
        self.assertIn("flow_west_to_east", flow_ids)
        self.assertEqual(len(vehicles), 0)

    def test_sumo_config_uses_designed_routes(self):
        text = CONFIG_PATH.read_text(encoding="utf-8")
        self.assertIn('<route-files value="designed_routes.rou.xml"/>', text)


if __name__ == "__main__":
    unittest.main()
