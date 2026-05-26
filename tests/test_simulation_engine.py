import unittest
import math
from simulation import agents, vehicles, network, constants, pedestrians
from simulation import traffic_light, controllers, metrics, engine


class TestSimulationEngine(unittest.TestCase):
    def setUp(self):
        self.network = network.Network()

    def test_traffic_light_lifecycle(self):
        tl = traffic_light.TrafficLight()
        self.assertEqual(tl.phase, "NS_GREEN")
        self.assertEqual(tl.ns_state, "green")
        self.assertEqual(tl.ew_state, "red")
        self.assertEqual(tl.signal_for_approach("north"), "green")
        self.assertEqual(tl.signal_for_approach("south"), "green")
        self.assertEqual(tl.signal_for_approach("east"), "red")
        self.assertEqual(tl.signal_for_approach("west"), "red")
        self.assertGreater(tl.remaining, 0)

        # Transition
        tl2 = traffic_light.TrafficLight(initial_idx=0)
        tl2.remaining = 0.001
        tl2.update(0.01)
        self.assertEqual(tl2.phase, "NS_YELLOW")
        self.assertEqual(tl2.ns_state, "yellow")

        # Full Cycle
        tl3 = traffic_light.TrafficLight(initial_idx=0)
        for p in ["NS_GREEN", "NS_YELLOW", "ALL_RED", "EW_GREEN", "EW_YELLOW"]:
            self.assertEqual(tl3.phase, p)
            tl3.remaining = 0.001
            tl3.update(0.01)

        # Wrap
        tl4 = traffic_light.TrafficLight(initial_idx=4)
        tl4.remaining = 0.001
        tl4.update(0.01)
        self.assertEqual(tl4.phase, "NS_GREEN")
        self.assertEqual(tl4.cycle_count, 1)

        # Dict/Reset
        d = tl4.to_dict()
        self.assertEqual(d["phase"], "NS_GREEN")
        self.assertEqual(d["ns_state"], "green")
        self.assertIn("remaining", d)
        self.assertIn("cycle_count", d)

        tl4.reset()
        self.assertEqual(tl4.phase, "NS_GREEN")
        self.assertEqual(tl4.cycle_count, 0)

    def test_controllers(self):
        ctrl = controllers.FixedTimeController()
        self.assertEqual(ctrl.phase, "NS_GREEN")
        state = {"clock": 0, "vehicles": 0, "queues": {}, "phase": "NS_GREEN"}
        ctrl.step(state, 0.01)

        ctrl2 = controllers.create_controller("fixed_time")
        self.assertTrue(isinstance(ctrl2, controllers.FixedTimeController))

        ctrl3 = controllers.create_controller("rl")
        self.assertTrue(isinstance(ctrl3, controllers.RLController))

        self.assertEqual(ctrl.signal_for_approach("north"), "green")
        self.assertEqual(ctrl.signal_for_approach("east"), "red")

    def test_pedestrians(self):
        ped = pedestrians.Pedestrian.create("north", self.network)
        self.assertTrue(ped.id.startswith("P_"))
        self.assertEqual(ped.state, "waiting")
        self.assertTrue(ped.active)
        self.assertEqual(ped.crosswalk_side, "north")
        self.assertTrue(ped.compliant)

        # Compliant waits and crosses
        ped.update(constants.DT)
        self.assertEqual(ped.state, "waiting")
        ped._wait_timer = 10.0
        ped.update(constants.DT)
        self.assertEqual(ped.state, "crossing")

        # Completes crossing
        while ped.active and ped.state == "crossing":
            ped.update(constants.DT)
        self.assertFalse(ped.active)
        self.assertEqual(ped.state, "done")

        # Non-compliant crosses early
        ped2 = pedestrians.Pedestrian.create("south", self.network, compliance="non-compliant")
        self.assertFalse(ped2.compliant)
        ped2._wait_timer = 2.0
        ped2.update(constants.DT)
        self.assertEqual(ped2.state, "crossing")

        # Serialization & Unique IDs
        d = ped.to_dict()
        self.assertEqual(d["type"], "pedestrian")
        self.assertEqual(d["crosswalk_side"], "north")
        self.assertEqual(d["state"], "done")
        self.assertIn("delay", d)

        ids = set()
        for _ in range(50):
            p = pedestrians.Pedestrian.create("east", self.network)
            ids.add(p.id)
        self.assertEqual(len(ids), 50)

    def test_metrics_collector(self):
        mc = metrics.MetricsCollector()
        self.assertEqual(mc.avg_wait, 0.0)
        self.assertEqual(mc.avg_queue, 0.0)
        self.assertEqual(mc.throughput, 0)

        mc.record_spawn(count=5)
        self.assertEqual(mc.total_vehicles_spawned, 5)

        mc.record_completion(count=2)
        self.assertEqual(mc.total_vehicles_completed, 2)
        self.assertEqual(mc.throughput, 2)

        mc.reset()
        self.assertEqual(mc.total_vehicles_spawned, 0)
        self.assertEqual(mc.total_vehicles_completed, 0)

        mc.record_spawn(count=10)
        mc.record_completion(count=3)
        mc.record_spawn(count=0, peds=2)
        d = mc.to_dict()
        self.assertEqual(d["total_vehicles_spawned"], 10)
        self.assertEqual(d["total_vehicles_completed"], 3)
        self.assertEqual(d["total_pedestrians_spawned"], 2)

    def test_simulation_engine(self):
        eng = engine.SimulationEngine(seed=42)
        self.assertEqual(eng.status, "stopped")
        self.assertEqual(eng.clock, 0.0)

        eng.start()
        self.assertEqual(eng.status, "running")
        self.assertEqual(len(eng.vehicles), 0)

        eng.step(num_ticks=20)
        self.assertGreater(eng.clock, 0)
        self.assertGreater(eng.simulation_time, 0)
        self.assertGreater(eng.metrics.step_count, 0)
        self.assertIn(eng.controller.phase, ("NS_GREEN", "NS_YELLOW", "ALL_RED", "EW_GREEN", "EW_YELLOW"))

        # Check vehicle spawning under heavy density
        eng2 = engine.SimulationEngine(seed=42, controller_mode="fixed_time")
        eng2.traffic_density = "heavy"
        eng2.start()
        eng2.step(num_ticks=200)
        self.assertTrue(len(eng2.vehicles) > 0 or eng2.metrics.total_vehicles_spawned > 0)

        # Pause / resume
        eng3 = engine.SimulationEngine(seed=1)
        eng3.start()
        eng3.step(num_ticks=10)
        eng3.pause()
        self.assertEqual(eng3.status, "paused")
        t_before = eng3.clock
        eng3.step(num_ticks=10)
        t_after = eng3.clock
        self.assertEqual(t_after, t_before)

        eng3.resume()
        self.assertEqual(eng3.status, "running")
        eng3.step(num_ticks=5)
        self.assertGreater(eng3.clock, t_before)

        # Stop / Reset
        eng4 = engine.SimulationEngine(seed=1)
        eng4.start()
        eng4.step(num_ticks=10)
        eng4.stop()
        self.assertEqual(eng4.status, "stopped")
        eng4.reset()
        self.assertEqual(eng4.clock, 0.0)
        self.assertEqual(len(eng4.vehicles), 0)

        # Serialization
        eng5 = engine.SimulationEngine(seed=42)
        eng5.configure(traffic_density="heavy")
        eng5.start()
        eng5.step(num_ticks=50)
        d = eng5.to_dict()
        self.assertTrue(isinstance(d["time"], float))
        self.assertEqual(d["status"], "running")
        self.assertIn("vehicles", d)
        self.assertIn("pedestrians", d)
        self.assertIn("metrics", d)
        self.assertIn("events", d)

        # Configure
        eng6 = engine.SimulationEngine(seed=42)
        eng6.configure(traffic_density="heavy", pedestrian_density="low", emergency_mode="enabled")
        self.assertEqual(eng6.traffic_density, "heavy")
        self.assertEqual(eng6.pedestrian_density, "low")
        self.assertEqual(eng6.emergency_mode, "enabled")

        # RL controller
        eng7 = engine.SimulationEngine(controller_mode="rl", seed=42)
        self.assertTrue(isinstance(eng7.controller, controllers.RLController))
        eng7.start()
        eng7.step(num_ticks=20)
        self.assertGreater(eng7.clock, 0)


if __name__ == "__main__":
    unittest.main()
