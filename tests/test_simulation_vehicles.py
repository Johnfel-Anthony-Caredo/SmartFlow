import unittest
import math
from simulation import agents, vehicles, network, constants


class TestSimulationVehicles(unittest.TestCase):
    def setUp(self):
        self.network = network.Network()

    def test_agent_base(self):
        a = agents.Agent("test", "vehicle", 10.0, 20.0, 5.0, 0.0, "active")
        self.assertEqual(a.to_dict()["id"], "test")
        self.assertEqual(a.to_dict()["state"], "active")
        self.assertEqual(
            a.distance_to(agents.Agent("b", "x", 13.0, 24.0, 0, 0, "active")),
            5.0
        )

    def test_vehicle_spawning(self):
        v = vehicles.Vehicle.create("north", 0, "straight", self.network)
        self.assertEqual(v.approach, "north")
        self.assertEqual(v.lane, 0)
        self.assertEqual(v.turn, "straight")
        self.assertTrue(v.active)

    def test_vehicle_moves_after_ticks(self):
        v2 = vehicles.Vehicle.create("north", 0, "straight", self.network)
        start_y = v2.y
        for _ in range(20):
            v2.update(constants.DT)
        self.assertLess(v2.y, start_y)
        self.assertGreater(v2.speed, 0)

    def test_vehicle_stops_for_red(self):
        v3 = vehicles.Vehicle.create("north", 0, "straight", self.network)
        v3.signal_state = "red"
        for _ in range(50):
            v3.update(constants.DT)
        sl = self.network.get_stop_line("north")
        dist = math.hypot(v3.x - sl[0], v3.y - sl[1])
        # The vehicle should stop at or before the stop line
        self.assertLessEqual(v3.speed, 0.1)

    def test_vehicle_stops_for_lead_vehicle(self):
        v4 = vehicles.Vehicle.create("north", 0, "straight", self.network)
        v5 = vehicles.Vehicle.create("north", 0, "straight", self.network)
        v4.y = 50.0
        v4.speed = 0.0
        v5.lead_vehicle = v4
        for _ in range(30):
            v5.update(constants.DT)
            v4.update(constants.DT)
        gap = v5.distance_to(v4)
        self.assertLessEqual(v5.speed, 5.6) # should slow down to follow lead car

    def test_complete_trip_despawn(self):
        v6 = vehicles.Vehicle.create("north", 0, "straight", self.network)
        v6.speed = 10.0
        steps = 0
        while v6.active and steps < 500:
            v6.update(constants.DT)
            steps += 1
        self.assertFalse(v6.active)
        self.assertEqual(v6.state, "done")

    def test_vehicle_serialization(self):
        v7 = vehicles.Vehicle.create("east", 1, "right", self.network, vehicle_type="truck", emergency=True)
        d = v7.to_dict()
        self.assertEqual(d["vehicle_type"], "truck")
        self.assertTrue(d["emergency"])
        self.assertEqual(d["approach"], "east")
        self.assertIn("heading_deg", d)
        self.assertIn("wait_time", d)

    def test_id_uniqueness(self):
        ids = set()
        for _ in range(100):
            v = vehicles.Vehicle.create("north", 0, "straight", self.network)
            ids.add(v.id)
        self.assertEqual(len(ids), 100)


if __name__ == "__main__":
    unittest.main()
