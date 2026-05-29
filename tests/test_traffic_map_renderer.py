import unittest

from components.traffic_map import build_traffic_map, build_traffic_map_payload, load_visual_network


def _walk(component):
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if hasattr(child, "children"):
            yield from _walk(child)


def _class_names(component):
    return [
        getattr(node, "className", "")
        for node in _walk(component)
        if getattr(node, "className", "")
    ]


def _find_first(component, predicate):
    for node in _walk(component):
        if predicate(node):
            return node
    raise AssertionError("No matching node found")


class TestTrafficMapRenderer(unittest.TestCase):
    def test_visual_network_loads_sumo_geometry_for_svg_base(self):
        network = load_visual_network()

        self.assertEqual(network["source_net"], "inter_ped.net.xml")
        self.assertIn("bounds", network)
        self.assertGreater(len(network["roads"]), 0)
        self.assertGreaterEqual(len(network["crossings"]), 4)
        self.assertGreaterEqual(len(network["walking_areas"]), 4)
        self.assertEqual(len(network["signals"]), 4)

    def test_renderer_maps_live_state_to_svg_layers(self):
        network = load_visual_network()
        state = {
            "status": "running",
            "phase": "NS_GREEN",
            "phase_remaining": 22.0,
            "vehicles": [
                {
                    "id": "veh_1",
                    "x": 522.43,
                    "y": 873.17,
                    "angle": 90,
                    "speed": 6.3,
                    "lane_id": "1337657045#0_0",
                    "edge_id": "1337657045#0",
                    "visual_type": "car",
                    "emergency": False,
                    "wait_time": 0.0,
                },
                {
                    "id": "ev_1",
                    "x": 532.86,
                    "y": 866.44,
                    "angle": 180,
                    "speed": 9.1,
                    "lane_id": "-1337657045#3_0",
                    "edge_id": "-1337657045#3",
                    "visual_type": "ambulance",
                    "emergency": True,
                    "wait_time": 0.0,
                },
            ],
            "pedestrians": [
                {
                    "id": "ped_1",
                    "x": 527.89,
                    "y": 862.03,
                    "speed": 1.2,
                    "lane_id": ":352681772_c1_0",
                    "edge_id": ":352681772_c1",
                }
            ],
            "queues": {"north": 2, "south": 0, "east": 3, "west": 1},
            "visual": {
                "constraint_marker": {
                    "active": True,
                    "label": "Lane Closure",
                    "x": 640.0,
                    "y": 790.0,
                }
            },
            "scenario": {"road_constraint": "Lane Closure"},
        }

        payload = build_traffic_map_payload(state, network)
        component = build_traffic_map(state, network=network)
        classes = " ".join(_class_names(component))

        self.assertEqual(payload["status"], "running")
        self.assertEqual(payload["vehicle_count"], 2)
        self.assertEqual(payload["pedestrian_count"], 1)
        self.assertEqual(payload["queues"]["east"], 3)
        self.assertIn("traffic-map-svg", classes)
        self.assertIn("traffic-map-road", classes)
        self.assertIn("traffic-map-junction-box", classes)
        self.assertIn("traffic-map-sidewalk-zone", classes)
        self.assertIn("traffic-map-crossing", classes)
        self.assertIn("traffic-map-vehicle", classes)
        self.assertIn("traffic-map-vehicle emergency", classes)
        self.assertIn("traffic-map-pedestrian", classes)
        self.assertIn("traffic-map-signal signal-green", classes)
        self.assertIn("traffic-map-queue traffic-map-queue-east", classes)
        self.assertIn("traffic-map-constraint", classes)

    def test_renderer_shows_empty_banner_when_runtime_has_no_entities(self):
        component = build_traffic_map(
            {
                "status": "stopped",
                "phase": "NS_GREEN",
                "phase_remaining": 0,
                "vehicles": [],
                "pedestrians": [],
                "queues": {},
                "visual": {},
                "scenario": {},
            }
        )
        classes = " ".join(_class_names(component))

        self.assertIn("traffic-map-empty-banner", classes)

    def test_renderer_focuses_intersection_and_keeps_overlay_minimal(self):
        network = load_visual_network()
        component = build_traffic_map(
            {
                "status": "stopped",
                "phase": "NS_GREEN",
                "phase_remaining": 0,
                "vehicles": [],
                "pedestrians": [],
                "queues": {},
                "visual": {},
                "scenario": {},
            },
            network=network,
        )

        classes = " ".join(_class_names(component))
        svg_node = _find_first(
            component,
            lambda node: getattr(node, "className", "") == "traffic-map-svg",
        )
        full_width = (network["bounds"]["max_x"] - network["bounds"]["min_x"]) + 36.0
        focused_width = float(svg_node.viewBox.split()[2])

        self.assertLess(focused_width, full_width)
        self.assertIn("traffic-map-empty-banner", classes)
        self.assertNotIn("traffic-map-status-strip", classes)

    def test_renderer_adds_stop_bars_lane_arrows_and_constraint_band(self):
        component = build_traffic_map(
            {
                "status": "running",
                "phase": "NS_GREEN",
                "phase_remaining": 14,
                "vehicles": [],
                "pedestrians": [],
                "queues": {"north": 3, "east": 2},
                "visual": {
                    "constraint_marker": {
                        "active": True,
                        "label": "Lane Closure",
                        "x": 640.0,
                        "y": 790.0,
                    }
                },
                "scenario": {},
            }
        )
        classes = " ".join(_class_names(component))

        self.assertIn("traffic-map-stop-bar", classes)
        self.assertIn("traffic-map-lane-arrow", classes)
        self.assertIn("traffic-map-edge-label", classes)
        self.assertIn("traffic-map-constraint-band", classes)
        self.assertIn("traffic-map-corner-plaza", classes)


if __name__ == "__main__":
    unittest.main()
