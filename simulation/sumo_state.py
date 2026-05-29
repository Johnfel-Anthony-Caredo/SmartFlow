from typing import Iterable


def canonical_signal_states(phase: str) -> tuple[str, str]:
    if phase == "NS_GREEN":
        return "green", "red"
    if phase == "NS_YELLOW":
        return "yellow", "red"
    if phase == "EW_GREEN":
        return "red", "green"
    if phase == "EW_YELLOW":
        return "red", "yellow"
    return "red", "red"


def _vehicle_visual_type(vehicle_id: str, emergency: bool) -> str:
    if emergency:
        return "ambulance"
    types = ("car", "suv", "taxi", "pickup", "truck", "bus")
    return types[sum(ord(ch) for ch in vehicle_id) % len(types)]


def vehicle_snapshot(connection, vehicle_ids: Iterable[str], limit: int, emergency_ids: set[str] | None = None) -> list[dict]:
    snapshot = []
    emergency_ids = emergency_ids or set()
    for vehicle_id in list(vehicle_ids)[:limit]:
        x, y = connection.vehicle.getPosition(vehicle_id)
        emergency = vehicle_id in emergency_ids
        snapshot.append({
            "id": vehicle_id,
            "type": "vehicle",
            "x": round(x, 2),
            "y": round(y, 2),
            "speed": round(connection.vehicle.getSpeed(vehicle_id), 2),
            "angle": round(connection.vehicle.getAngle(vehicle_id), 2),
            "edge_id": connection.vehicle.getRoadID(vehicle_id),
            "lane_id": connection.vehicle.getLaneID(vehicle_id),
            "wait_time": round(connection.vehicle.getAccumulatedWaitingTime(vehicle_id), 1),
            "state": "active",
            "visual_type": _vehicle_visual_type(vehicle_id, emergency),
            "emergency": emergency,
        })
    return snapshot


def pedestrian_snapshot(connection, person_ids: Iterable[str], limit: int) -> list[dict]:
    snapshot = []
    for person_id in list(person_ids)[:limit]:
        x, y = connection.person.getPosition(person_id)
        snapshot.append({
            "id": person_id,
            "type": "pedestrian",
            "x": round(x, 2),
            "y": round(y, 2),
            "speed": round(connection.person.getSpeed(person_id), 2),
            "edge_id": connection.person.getRoadID(person_id),
            "lane_id": connection.person.getLaneID(person_id),
            "state": "active",
            "visual_type": "pedestrian",
        })
    return snapshot


def build_state_payload(
    *,
    status: str,
    simulation_time: float,
    phase: str,
    phase_remaining: float,
    cycle_count: int,
    controller_type: str,
    vehicles: list[dict],
    pedestrians: list[dict],
    metrics: dict,
    events: list[dict],
    scenario: dict,
    dashboard: dict,
    charts: dict,
    visual: dict,
) -> dict:
    return {
        "time": round(simulation_time, 1),
        "status": status,
        "phase": phase,
        "phase_remaining": round(max(phase_remaining, 0.0), 1),
        "cycle_count": cycle_count,
        "controller_type": controller_type,
        "vehicles": vehicles,
        "vehicle_count": len(vehicles) if metrics.get("active_vehicle_count") is None else metrics["active_vehicle_count"],
        "pedestrians": pedestrians,
        "pedestrian_count": len(pedestrians) if metrics.get("active_pedestrian_count") is None else metrics["active_pedestrian_count"],
        "queues": metrics.get("queue_by_approach", {}),
        "metrics": {
            key: value
            for key, value in metrics.items()
            if key not in {"active_vehicle_count", "active_pedestrian_count", "queue_by_approach"}
        },
        "events": events,
        "scenario": scenario,
        "dashboard": dashboard,
        "charts": charts,
        "visual": visual,
    }
