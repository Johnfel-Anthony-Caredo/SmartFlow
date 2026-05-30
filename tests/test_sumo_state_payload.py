import unittest

from simulation.sumo_state import build_state_payload, canonical_signal_states


class TestSumoStatePayload(unittest.TestCase):
    def test_payload_exposes_queue_by_approach_for_renderers(self):
        payload = build_state_payload(
            status="running",
            simulation_time=12.0,
            phase="NS_GREEN",
            phase_remaining=30.0,
            cycle_count=0,
            controller_type="fixed_time",
            vehicles=[],
            pedestrians=[],
            metrics={
                "avg_wait": 2.5,
                "active_vehicle_count": 4,
                "active_pedestrian_count": 2,
                "queue_by_approach": {
                    "north": 3,
                    "south": 1,
                    "east": 0,
                    "west": 4,
                },
            },
            events=[],
            scenario={},
            dashboard={},
            charts={},
            visual={},
        )

        self.assertEqual(
            payload["queues"],
            {
                "north": 3,
                "south": 1,
                "east": 0,
                "west": 4,
            },
        )
        self.assertNotIn("queue_by_approach", payload["metrics"])

    def test_canonical_signal_states_support_j1_phase_names(self):
        self.assertEqual(canonical_signal_states("WEST_GREEN"), ("green", "red"))
        self.assertEqual(canonical_signal_states("EAST_YELLOW"), ("yellow", "red"))
        self.assertEqual(canonical_signal_states("PED_GREEN"), ("green", "red"))
        self.assertEqual(canonical_signal_states("ALL_RED"), ("red", "red"))


if __name__ == "__main__":
    unittest.main()
