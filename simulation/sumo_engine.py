import uuid
from dataclasses import dataclass

import traci

from .sumo_config import (
    APPROACH_LANES,
    CHART_HISTORY_LIMIT,
    CONTROLLED_TLS_IDS,
    DEFAULT_SCENARIO_NAME,
    DENSITY_SCALE,
    EVENT_LIMIT,
    PEDESTRIAN_SAMPLE_LIMIT,
    PEDESTRIAN_ROUTE_TEMPLATES,
    PEDESTRIAN_SPAWN_INTERVALS,
    PHASE_SEQUENCE,
    SUMO_CONFIG_PATH,
    SUMO_STEP_LENGTH,
    TLS_STATE_MAP,
    VEHICLE_SAMPLE_LIMIT,
    get_sumo_binary,
)
from .sumo_state import build_state_payload, pedestrian_snapshot, vehicle_snapshot


@dataclass
class _MetricsAccumulator:
    step_count: int = 0
    total_vehicles_spawned: int = 0
    total_vehicles_completed: int = 0
    total_pedestrians_spawned: int = 0
    total_pedestrians_completed: int = 0
    avg_wait_sum: float = 0.0
    avg_queue_sum: float = 0.0
    avg_ped_delay_sum: float = 0.0
    max_queue: int = 0

    def reset(self):
        self.step_count = 0
        self.total_vehicles_spawned = 0
        self.total_vehicles_completed = 0
        self.total_pedestrians_spawned = 0
        self.total_pedestrians_completed = 0
        self.avg_wait_sum = 0.0
        self.avg_queue_sum = 0.0
        self.avg_ped_delay_sum = 0.0
        self.max_queue = 0

    def record(self, *, wait_times: list[float], queue_counts: dict[str, int], pedestrian_count: int, departed: int, arrived: int, departed_peds: int, arrived_peds: int):
        self.step_count += 1
        self.total_vehicles_spawned += departed
        self.total_vehicles_completed += arrived
        self.total_pedestrians_spawned += departed_peds
        self.total_pedestrians_completed += arrived_peds

        current_avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0.0
        current_avg_queue = sum(queue_counts.values()) / len(queue_counts) if queue_counts else 0.0

        self.avg_wait_sum += current_avg_wait
        self.avg_queue_sum += current_avg_queue
        self.avg_ped_delay_sum += float(pedestrian_count)
        self.max_queue = max(self.max_queue, max(queue_counts.values(), default=0))

    def to_dict(self, *, active_vehicle_count: int, active_pedestrian_count: int, queue_by_approach: dict[str, int]) -> dict:
        step_divisor = self.step_count if self.step_count else 1
        return {
            "avg_wait": round(self.avg_wait_sum / step_divisor, 1) if self.step_count else 0.0,
            "avg_queue": round(self.avg_queue_sum / step_divisor, 1) if self.step_count else 0.0,
            "max_queue": self.max_queue,
            "throughput": self.total_vehicles_completed,
            "avg_ped_delay": round(self.avg_ped_delay_sum / step_divisor, 1) if self.step_count else 0.0,
            "total_vehicles_spawned": self.total_vehicles_spawned,
            "total_vehicles_completed": self.total_vehicles_completed,
            "total_pedestrians_spawned": self.total_pedestrians_spawned,
            "total_pedestrians_completed": self.total_pedestrians_completed,
            "step_count": self.step_count,
            "active_vehicle_count": active_vehicle_count,
            "active_pedestrian_count": active_pedestrian_count,
            "queue_by_approach": queue_by_approach,
        }


class SumoSimulationEngine:
    def __init__(self, seed: int | None = 42):
        self.seed = seed if seed is not None else 42
        self.status = "stopped"
        self.simulation_time = 0.0
        self.traffic_density = "medium"
        self.pedestrian_density = "medium"
        self.emergency_mode = "disabled"
        self.road_constraint = "None"
        self.lane_closure = False
        self.accident = False
        self.flooding = False
        self.construction = False
        self.temp_blockage = False
        self.controller_type = "fixed_time"
        self.control_mode_label = "Fixed-Time (SUMO/TraCI)"
        self.current_scenario_name = DEFAULT_SCENARIO_NAME
        self.events: list[dict] = []
        self.metrics = _MetricsAccumulator()
        self.connection = None
        self.connection_label = None
        self.phase_index = 0
        self.phase = PHASE_SEQUENCE[0][0]
        self.phase_remaining = PHASE_SEQUENCE[0][1]
        self.cycle_count = 0
        self.run_id = "—"
        self.last_action = "Not started"
        self.last_error = "None"
        self._event_counter = 0
        self._last_vehicle_sample: list[dict] = []
        self._last_pedestrian_sample: list[dict] = []
        self._chart_traffic_flow: list[dict] = []
        self._chart_wait_time: list[dict] = []
        self._chart_queue_length: list[dict] = []
        self._chart_throughput: list[dict] = []
        self._emergency_vehicle_ids: set[str] = set()
        self._pedestrian_spawn_elapsed = 0.0
        self._pedestrian_route_index = 0
        self._last_metrics = self.metrics.to_dict(
            active_vehicle_count=0,
            active_pedestrian_count=0,
            queue_by_approach={key: 0 for key in APPROACH_LANES},
        )

    def start(self):
        if self.status == "running":
            return
        if self.status == "paused":
            self.resume()
            return

        self._reset_runtime_state()
        try:
            self._start_connection()
            self._apply_phase()
            self.status = "running"
            self.run_id = f"sumo-{uuid.uuid4().hex[:8]}"
            self._record_action("SUMO simulation started")
            self._refresh_state()
        except Exception as exc:
            self.status = "stopped"
            self.last_error = str(exc)
            self._add_event("warning", f"SUMO startup failed: {exc}")
            self._close_connection()

    def pause(self):
        if self.status == "running":
            self.status = "paused"
            self._record_action("Simulation paused")

    def resume(self):
        if self.status == "paused":
            self.status = "running"
            self._record_action("Simulation resumed")

    def stop(self):
        if self.status in {"running", "paused"}:
            self.status = "stopped"
            self._record_action("Simulation stopped")
        self._close_connection()

    def reset(self):
        self.stop()
        self._reset_runtime_state()
        self._record_action("Simulation reset")

    def step(self, num_ticks: int = 1):
        if self.status != "running" or self.connection is None:
            return

        for _ in range(num_ticks):
            try:
                self._pedestrian_spawn_elapsed += SUMO_STEP_LENGTH
                self._spawn_pedestrian_if_due()
                self.connection.simulationStep()
                self.simulation_time += SUMO_STEP_LENGTH
                self.phase_remaining -= SUMO_STEP_LENGTH
                if self.phase_remaining <= 0:
                    self._advance_phase()
                self._refresh_state()
            except Exception as exc:
                self.last_error = str(exc)
                self._add_event("warning", f"SUMO step failed: {exc}")
                self.stop()
                break

    def configure(self, **kwargs):
        density_fields = {"traffic_density", "pedestrian_density"}
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key in density_fields and isinstance(value, str):
                    setattr(self, key, value.lower())
                else:
                    setattr(self, key, value)
        if kwargs:
            self._record_action("Scenario settings updated for the next run")

    def configure_from_scenario(self, scenario: dict):
        if scenario.get("name"):
            self.current_scenario_name = scenario["name"]
        self.configure(**{
            key: scenario[key]
            for key in (
                "traffic_density",
                "pedestrian_density",
                "emergency_mode",
                "road_constraint",
                "lane_closure",
                "construction",
                "accident",
                "flooding",
                "temp_blockage",
            )
            if key in scenario and scenario[key] is not None
        })

    def to_dict(self) -> dict:
        return build_state_payload(
            status=self.status,
            simulation_time=self.simulation_time,
            phase=self.phase,
            phase_remaining=self.phase_remaining,
            cycle_count=self.cycle_count,
            controller_type=self.controller_type,
            vehicles=self._last_vehicle_sample,
            pedestrians=self._last_pedestrian_sample,
            metrics=self._last_metrics,
            events=self.events[-20:],
            scenario={
                "traffic_density": self.traffic_density,
                "pedestrian_density": self.pedestrian_density,
                "emergency_mode": self.emergency_mode,
                "road_constraint": self.road_constraint,
            },
            dashboard={
                "current_scenario_name": self.current_scenario_name,
                "control_mode_label": self.control_mode_label,
                "emergency_active_count": self._count_active_emergency_vehicles(),
                "last_action": self.last_action,
                "last_error": self.last_error,
                "run_id": self.run_id,
            },
            charts={
                "traffic_flow": self._chart_traffic_flow,
                "wait_time": self._chart_wait_time,
                "queue_length": self._chart_queue_length,
                "throughput": self._chart_throughput,
            },
            visual={
                "constraint_marker": self._build_constraint_marker(),
            },
        )

    def _start_connection(self):
        if not SUMO_CONFIG_PATH.exists():
            raise RuntimeError(f"Missing SUMO config: {SUMO_CONFIG_PATH}")

        self.connection_label = f"smartflow-{uuid.uuid4().hex}"
        args = [
            get_sumo_binary(),
            "-c",
            str(SUMO_CONFIG_PATH),
            "--step-length",
            str(SUMO_STEP_LENGTH),
            "--seed",
            str(self.seed),
            "--no-step-log",
            "true",
            "--duration-log.disable",
            "true",
            "--scale",
            str(DENSITY_SCALE.get(self.traffic_density, 1.0)),
        ]
        traci.start(args, label=self.connection_label)
        self.connection = traci.getConnection(self.connection_label)

    def _close_connection(self):
        if self.connection is None:
            return
        try:
            self.connection.close()
        except Exception:
            pass
        finally:
            self.connection = None
            self.connection_label = None

    def _reset_runtime_state(self):
        self.simulation_time = 0.0
        self.metrics.reset()
        self.phase_index = 0
        self.phase = PHASE_SEQUENCE[0][0]
        self.phase_remaining = PHASE_SEQUENCE[0][1]
        self.cycle_count = 0
        self.events = []
        self._event_counter = 0
        self._last_vehicle_sample = []
        self._last_pedestrian_sample = []
        self._pedestrian_spawn_elapsed = 0.0
        self._pedestrian_route_index = 0
        self.run_id = "—"
        self.last_action = "Not started"
        self.last_error = "None"
        self._chart_traffic_flow = []
        self._chart_wait_time = []
        self._chart_queue_length = []
        self._chart_throughput = []
        self._emergency_vehicle_ids = set()
        self._last_metrics = self.metrics.to_dict(
            active_vehicle_count=0,
            active_pedestrian_count=0,
            queue_by_approach={key: 0 for key in APPROACH_LANES},
        )

    def _advance_phase(self):
        self.phase_index = (self.phase_index + 1) % len(PHASE_SEQUENCE)
        if self.phase_index == 0:
            self.cycle_count += 1
        self.phase, self.phase_remaining = PHASE_SEQUENCE[self.phase_index]
        self._apply_phase()
        self._record_action(f"Phase changed: {self.phase}", kind="signal")

    def _apply_phase(self):
        if self.connection is None:
            return
        state = TLS_STATE_MAP[self.phase]
        for tls_id in CONTROLLED_TLS_IDS:
            self.connection.trafficlight.setRedYellowGreenState(tls_id, state)

    def _refresh_state(self):
        if self.connection is None:
            return

        vehicle_ids = list(self.connection.vehicle.getIDList())
        person_ids = list(self.connection.person.getIDList())
        queue_by_approach = {
            approach: sum(self.connection.lane.getLastStepHaltingNumber(lane_id) for lane_id in lane_ids)
            for approach, lane_ids in APPROACH_LANES.items()
        }
        wait_times = [self.connection.vehicle.getAccumulatedWaitingTime(vehicle_id) for vehicle_id in vehicle_ids]
        departed_ids = list(self.connection.simulation.getDepartedIDList())
        arrived_ids = list(self.connection.simulation.getArrivedIDList())
        self._emergency_vehicle_ids.difference_update(arrived_ids)
        self._assign_emergency_vehicles(departed_ids)

        departed_person_ids = []
        arrived_person_ids = []
        if hasattr(self.connection.simulation, "getDepartedPersonIDList"):
            departed_person_ids = list(self.connection.simulation.getDepartedPersonIDList())
        if hasattr(self.connection.simulation, "getArrivedPersonIDList"):
            arrived_person_ids = list(self.connection.simulation.getArrivedPersonIDList())

        self.metrics.record(
            wait_times=wait_times,
            queue_counts=queue_by_approach,
            pedestrian_count=len(person_ids),
            departed=len(departed_ids),
            arrived=len(arrived_ids),
            departed_peds=len(departed_person_ids),
            arrived_peds=len(arrived_person_ids),
        )

        self._last_vehicle_sample = vehicle_snapshot(
            self.connection,
            vehicle_ids,
            VEHICLE_SAMPLE_LIMIT,
            self._emergency_vehicle_ids,
        )
        self._last_pedestrian_sample = pedestrian_snapshot(self.connection, person_ids, PEDESTRIAN_SAMPLE_LIMIT)
        self._last_metrics = self.metrics.to_dict(
            active_vehicle_count=len(vehicle_ids),
            active_pedestrian_count=len(person_ids),
            queue_by_approach=queue_by_approach,
        )
        self._append_chart_points(queue_by_approach=queue_by_approach, active_vehicle_count=len(vehicle_ids))

        for approach, queue_count in queue_by_approach.items():
            if queue_count >= 5:
                self._add_event("warning", f"High congestion on {approach} approach")

    def _spawn_pedestrian_if_due(self):
        if self.connection is None:
            return

        interval = PEDESTRIAN_SPAWN_INTERVALS.get(self.pedestrian_density, 8.0)
        if interval is None or self._pedestrian_spawn_elapsed < interval:
            return

        template = PEDESTRIAN_ROUTE_TEMPLATES[self._pedestrian_route_index % len(PEDESTRIAN_ROUTE_TEMPLATES)]
        self._pedestrian_route_index += 1
        self._pedestrian_spawn_elapsed = 0.0

        try:
            stages = self.connection.simulation.findIntermodalRoute(
                template["from_edge"],
                template["to_edge"],
            )
        except Exception as exc:
            self._add_event("warning", f"Pedestrian routing failed: {exc}")
            return

        if not stages:
            self._add_event("warning", "Pedestrian routing returned no stages")
            return

        route_edges = tuple(getattr(stages[0], "edges", ()))
        if not route_edges:
            self._add_event("warning", "Pedestrian routing returned an empty walk")
            return

        person_id = f"ped_{int(self.simulation_time)}_{self._pedestrian_route_index}"
        try:
            self.connection.person.add(person_id, route_edges[0], 0.1)
            self.connection.person.appendWalkingStage(person_id, route_edges, -1)
            self._add_event("info", f"Pedestrian spawned on {template['name']} crossing")
        except Exception as exc:
            self.last_error = str(exc)
            self._add_event("warning", f"Pedestrian spawn failed: {exc}")

    def _add_event(self, kind: str, message: str):
        self._event_counter += 1
        self.events.append({
            "id": self._event_counter,
            "time": round(self.simulation_time, 1),
            "kind": kind,
            "message": message,
        })
        if len(self.events) > EVENT_LIMIT:
            self.events = self.events[-EVENT_LIMIT:]

    def _record_action(self, message: str, kind: str = "info"):
        self.last_action = message
        self._add_event(kind, message)

    def _append_chart_points(self, *, queue_by_approach: dict[str, int], active_vehicle_count: int):
        metric_time = round(self.simulation_time, 1)
        self._chart_traffic_flow.append({
            "time": metric_time,
            "north": queue_by_approach.get("north", 0),
            "south": queue_by_approach.get("south", 0),
            "east": queue_by_approach.get("east", 0),
            "west": queue_by_approach.get("west", 0),
            "vehicles": active_vehicle_count,
        })
        self._chart_wait_time.append({
            "time": metric_time,
            "value": self._last_metrics["avg_wait"],
        })
        self._chart_queue_length.append({
            "time": metric_time,
            "value": self._last_metrics["avg_queue"],
        })
        self._chart_throughput.append({
            "time": metric_time,
            "value": self._last_metrics["throughput"],
        })

        for series in (
            self._chart_traffic_flow,
            self._chart_wait_time,
            self._chart_queue_length,
            self._chart_throughput,
        ):
            if len(series) > CHART_HISTORY_LIMIT:
                del series[:-CHART_HISTORY_LIMIT]

    def _count_active_emergency_vehicles(self) -> int:
        return sum(
            1
            for vehicle in self._last_vehicle_sample
            if vehicle.get("emergency")
        )

    def _assign_emergency_vehicles(self, departed_ids: list[str]):
        declared_emergency_ids = {
            vehicle_id
            for vehicle_id in departed_ids
            if self._is_declared_emergency_vehicle(vehicle_id)
        }
        for vehicle_id in declared_emergency_ids:
            if vehicle_id not in self._emergency_vehicle_ids:
                self._emergency_vehicle_ids.add(vehicle_id)
                self._add_event("priority", f"Emergency vehicle detected: {vehicle_id}")

        if self.emergency_mode == "disabled":
            return

        max_active = 1
        if "2" in str(self.emergency_mode):
            max_active = 2

        for vehicle_id in departed_ids:
            if len(self._emergency_vehicle_ids) >= max_active:
                break
            if vehicle_id not in self._emergency_vehicle_ids:
                self._emergency_vehicle_ids.add(vehicle_id)
                self._add_event("priority", f"Emergency vehicle detected: {vehicle_id}")

    def _is_declared_emergency_vehicle(self, vehicle_id: str) -> bool:
        if self.connection is None:
            return False
        try:
            type_id = self.connection.vehicle.getTypeID(vehicle_id).lower()
        except Exception:
            type_id = ""
        try:
            vehicle_class = self.connection.vehicle.getVehicleClass(vehicle_id).lower()
        except Exception:
            vehicle_class = ""
        return type_id == "emergency" or vehicle_class == "emergency"

    def _build_constraint_marker(self) -> dict:
        label = (self.road_constraint or "").strip()
        active = any([
            label and label.lower() != "none",
            self.lane_closure,
            self.accident,
            self.flooding,
            self.construction,
            self.temp_blockage,
        ])
        if not active:
            return {"active": False}

        normalized = label.lower()
        if self.lane_closure or "lane" in normalized:
            x, y, edge_id, text = -18.0, 8.0, "-E1", "Lane Closure"
        elif self.accident or "accident" in normalized:
            x, y, edge_id, text = -24.0, 2.0, "J1", "Accident"
        elif self.flooding or "flood" in normalized:
            x, y, edge_id, text = -28.0, -12.0, "E3", "Flooding"
        elif self.construction or "construct" in normalized:
            x, y, edge_id, text = -24.0, 18.0, "-E2", "Construction"
        elif self.temp_blockage or "block" in normalized:
            x, y, edge_id, text = -30.0, 0.0, "E0", "Temporary Blockage"
        else:
            x, y, edge_id, text = -24.0, 2.0, "J1", label or "Road Constraint"

        return {
            "active": True,
            "label": text,
            "edge_id": edge_id,
            "x": x,
            "y": y,
        }
