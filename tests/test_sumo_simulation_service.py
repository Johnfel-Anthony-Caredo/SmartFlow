import unittest

import services.simulation_service as sim
from simulation import sumo_config


class TestSumoSimulationService(unittest.TestCase):
    def tearDown(self):
        try:
            sim.stop()
        except Exception:
            pass
        sim.reset_engine()

    def test_default_runtime_is_sumo_backed_and_exposes_dashboard_state(self):
        runtime = sim.get_engine()
        self.assertIn("sumo", type(runtime).__module__.lower())

        state = sim.get_state()
        self.assertEqual(state["status"], "stopped")
        self.assertEqual(state["controller_type"], "fixed_time")

        expected_top_level = {
            "time",
            "status",
            "phase",
            "phase_remaining",
            "cycle_count",
            "controller_type",
            "vehicles",
            "vehicle_count",
            "pedestrians",
            "pedestrian_count",
            "metrics",
            "events",
            "scenario",
        }
        self.assertTrue(expected_top_level.issubset(state.keys()))

        expected_metrics = {
            "avg_wait",
            "avg_queue",
            "throughput",
            "step_count",
            "total_vehicles_spawned",
            "total_vehicles_completed",
            "total_pedestrians_spawned",
            "total_pedestrians_completed",
        }
        self.assertTrue(expected_metrics.issubset(state["metrics"].keys()))

    def test_service_can_start_step_and_stop_a_sumo_run(self):
        sim.start()
        self.assertEqual(sim.current_status(), "running")

        sim.step(3)
        state = sim.get_state()

        self.assertEqual(state["status"], "running")
        self.assertGreaterEqual(state["time"], 3.0)
        self.assertGreaterEqual(state["metrics"]["step_count"], 3)
        self.assertIn(
            state["phase"],
            {"NS_GREEN", "NS_YELLOW", "ALL_RED", "EW_GREEN", "EW_YELLOW"},
        )

        sim.stop()
        self.assertEqual(sim.current_status(), "stopped")

    def test_service_spawns_pedestrians_when_density_is_enabled(self):
        sim.configure(pedestrian_density="heavy")
        sim.start()
        sim.step(12)
        state = sim.get_state()

        self.assertGreater(state["metrics"]["total_pedestrians_spawned"], 0)
        self.assertGreaterEqual(state["pedestrian_count"], 0)

    def test_runtime_exposes_dashboard_metadata_and_histories(self):
        sim.configure(
            traffic_density="heavy",
            pedestrian_density="medium",
            emergency_mode="enabled",
        )
        sim.start()
        sim.step(6)
        state = sim.get_state()

        self.assertIn("dashboard", state)
        self.assertIn("charts", state)
        self.assertIn("current_scenario_name", state["dashboard"])
        self.assertIn("control_mode_label", state["dashboard"])
        self.assertIn("emergency_active_count", state["dashboard"])
        self.assertIn("last_action", state["dashboard"])
        self.assertIn("last_error", state["dashboard"])
        self.assertIn("run_id", state["dashboard"])
        self.assertGreater(len(state["charts"]["traffic_flow"]), 0)
        self.assertGreater(len(state["charts"]["wait_time"]), 0)
        self.assertGreater(len(state["charts"]["queue_length"]), 0)
        self.assertGreater(len(state["charts"]["throughput"]), 0)

    def test_runtime_exposes_visual_payload_for_scene_rendering(self):
        sim.configure(
            traffic_density="heavy",
            pedestrian_density="medium",
            emergency_mode="enabled",
            road_constraint="Lane Closure",
        )
        sim.start()
        sim.step(10)
        state = sim.get_state()

        self.assertIn("visual", state)
        self.assertIn("constraint_marker", state["visual"])
        if state["vehicles"]:
            self.assertIn("visual_type", state["vehicles"][0])
            self.assertIn("emergency", state["vehicles"][0])

    def test_sumo_controller_uses_main_intersection_tls_only(self):
        self.assertEqual(sumo_config.MAJOR_TLS_IDS, ("7900968103", "7900968104"))
        self.assertEqual(sumo_config.MINOR_TLS_IDS, ("7900968105", "7900968106"))


if __name__ == "__main__":
    unittest.main()
