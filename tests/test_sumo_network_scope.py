import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SCOPE_PATH = Path("sumo/Tagum_1/main_intersection_scope.json")
ROUTES_PATH = Path("sumo/Tagum_1/tagum1.rou.xml")
CONFIG_PATH = Path("sumo/Tagum_1/tagum1.sumocfg")
NET_PATH = Path("sumo/Tagum_1/tagum1.net.xml")


class TestSumoNetworkScope(unittest.TestCase):
    def test_scope_selects_one_main_intersection(self):
        scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(scope["mode"], "tagum_j1_single_intersection")
        self.assertEqual(scope["controlled_tls_ids"], ["J1"])
        self.assertIn("-E2", scope["route_edges"])
        self.assertIn("-E1", scope["route_edges"])
        self.assertIn("E3", scope["route_edges"])
        self.assertIn("E0", scope["route_edges"])
        self.assertEqual(scope["visual_center"], {"x": -22.41, "y": 4.76})
        self.assertEqual(scope["visual_radius_m"], 80.0)

    def test_tagum_routes_include_demands_pedestrians_and_two_ambulances(self):
        root = ET.parse(ROUTES_PATH).getroot()
        flow_pairs = {(flow.get("from"), flow.get("to")) for flow in root.findall("flow")}
        emergency_trips = [
            trip
            for trip in root.findall("trip")
            if trip.get("type") == "Emergency"
        ]
        person_trips = root.findall(".//personTrip")

        self.assertIn(("E3", "-E0"), flow_pairs)
        self.assertIn(("-E1", "-E0"), flow_pairs)
        self.assertIn(("E0", "-E3"), flow_pairs)
        self.assertEqual(len(emergency_trips), 2)
        self.assertGreaterEqual(len(person_trips), 10)

    def test_sumo_config_uses_tagum_network_and_routes(self):
        text = CONFIG_PATH.read_text(encoding="utf-8")
        self.assertIn('<net-file value="tagum1.net.xml"/>', text)
        self.assertIn('<route-files value="tagum1.rou.xml"/>', text)

    def test_j1_tl_logic_uses_exactly_eighteen_link_states(self):
        root = ET.parse(NET_PATH).getroot()
        tl_logic = root.find(".//tlLogic[@id='J1']")
        connections = root.findall(".//connection[@tl='J1']")
        link_indexes = {int(connection.get("linkIndex")) for connection in connections}

        self.assertIsNotNone(tl_logic)
        self.assertEqual(link_indexes, set(range(18)))
        for phase in tl_logic.findall("phase"):
            self.assertEqual(len(phase.get("state")), 18)


if __name__ == "__main__":
    unittest.main()
