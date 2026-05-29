"""Export the scoped SUMO network geometry for the Three.js dashboard view."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMO_DIR = ROOT / "sumo" / "intersection_1"
SCOPE_PATH = SUMO_DIR / "main_intersection_scope.json"
OUTPUT_PATH = ROOT / "assets" / "generated" / "visual_network.json"


def _parse_shape(value: str | None) -> list[dict[str, float]]:
    if not value:
        return []
    points: list[dict[str, float]] = []
    for token in value.split():
        x_text, y_text = token.split(",", 1)
        points.append({"x": float(x_text), "y": float(y_text)})
    return points


def _scope_visual_bounds(scope: dict[str, object]) -> dict[str, float]:
    center = scope.get("visual_center") or {"x": 0.0, "y": 0.0}
    radius = float(scope.get("visual_radius_m") or 260.0)
    center_x = float(center["x"])
    center_y = float(center["y"])
    return {
        "min_x": center_x - radius,
        "min_y": center_y - radius,
        "max_x": center_x + radius,
        "max_y": center_y + radius,
    }


def _clip_segment_to_bounds(
    start: dict[str, float],
    end: dict[str, float],
    bounds: dict[str, float],
) -> tuple[dict[str, float], dict[str, float]] | None:
    x0, y0 = start["x"], start["y"]
    x1, y1 = end["x"], end["y"]
    dx = x1 - x0
    dy = y1 - y0
    u_min = 0.0
    u_max = 1.0

    checks = (
        (-dx, x0 - bounds["min_x"]),
        (dx, bounds["max_x"] - x0),
        (-dy, y0 - bounds["min_y"]),
        (dy, bounds["max_y"] - y0),
    )
    for p_value, q_value in checks:
        if p_value == 0:
            if q_value < 0:
                return None
            continue
        ratio = q_value / p_value
        if p_value < 0:
            u_min = max(u_min, ratio)
        else:
            u_max = min(u_max, ratio)
        if u_min > u_max:
            return None

    return (
        {"x": round(x0 + u_min * dx, 2), "y": round(y0 + u_min * dy, 2)},
        {"x": round(x0 + u_max * dx, 2), "y": round(y0 + u_max * dy, 2)},
    )


def _same_point(left: dict[str, float], right: dict[str, float]) -> bool:
    return abs(left["x"] - right["x"]) < 0.01 and abs(left["y"] - right["y"]) < 0.01


def _clip_shape_to_bounds(
    points: list[dict[str, float]],
    bounds: dict[str, float],
) -> list[dict[str, float]]:
    clipped: list[dict[str, float]] = []
    for index in range(len(points) - 1):
        segment = _clip_segment_to_bounds(points[index], points[index + 1], bounds)
        if segment is None:
            continue
        start, end = segment
        if not clipped or not _same_point(clipped[-1], start):
            clipped.append(start)
        if not _same_point(clipped[-1], end):
            clipped.append(end)
    return clipped


def _lane_payload(lane: ET.Element, bounds: dict[str, float]) -> dict[str, object]:
    width = float(lane.get("width") or 3.2)
    shape = _clip_shape_to_bounds(_parse_shape(lane.get("shape")), bounds)
    return {
        "id": lane.get("id", ""),
        "index": int(lane.get("index") or 0),
        "width": width,
        "allow": lane.get("allow", ""),
        "disallow": lane.get("disallow", ""),
        "shape": shape,
    }


def _edge_payload(edge: ET.Element, bounds: dict[str, float]) -> dict[str, object]:
    lanes = [
        lane_payload
        for lane in edge.findall("lane")
        for lane_payload in [_lane_payload(lane, bounds)]
        if lane_payload["shape"]
    ]
    lane_shapes = [lane["shape"] for lane in lanes if lane["shape"]]
    return {
        "edge_id": edge.get("id", ""),
        "function": edge.get("function", "normal"),
        "from": edge.get("from", ""),
        "to": edge.get("to", ""),
        "shape": _clip_shape_to_bounds(_parse_shape(edge.get("shape")), bounds) or (lane_shapes[0] if lane_shapes else []),
        "lanes": lanes,
    }


def _edge_references_scope(edge: ET.Element, route_edges: set[str], tls_ids: set[str]) -> bool:
    edge_id = edge.get("id", "")
    if any(edge_id.startswith(f":{tls_id}_") for tls_id in tls_ids):
        return True
    crossing_edges = set((edge.get("crossingEdges") or "").split())
    return bool(crossing_edges & route_edges)


def build_visual_network() -> dict[str, object]:
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    net_path = SUMO_DIR / scope["net_file"]
    route_edges = set(scope["route_edges"])
    tls_ids = set(scope["controlled_tls_ids"])
    root = ET.parse(net_path).getroot()
    bounds = _scope_visual_bounds(scope)

    roads: list[dict[str, object]] = []
    crossings: list[dict[str, object]] = []
    walking_areas: list[dict[str, object]] = []
    for edge in root.findall("edge"):
        edge_id = edge.get("id", "")
        edge_function = edge.get("function", "normal")
        if edge_id in route_edges:
            payload = _edge_payload(edge, bounds)
            if payload["lanes"]:
                roads.append(payload)
        elif edge_function == "crossing" and _edge_references_scope(edge, route_edges, tls_ids):
            payload = _edge_payload(edge, bounds)
            if payload["lanes"]:
                crossings.append(payload)
        elif edge_function == "walkingarea" and _edge_references_scope(edge, route_edges, tls_ids):
            payload = _edge_payload(edge, bounds)
            if payload["lanes"]:
                walking_areas.append(payload)

    junctions = {
        junction.get("id"): junction
        for junction in root.findall("junction")
        if junction.get("id") in tls_ids
    }
    signals = []
    for tls_id in scope["controlled_tls_ids"]:
        junction = junctions.get(tls_id)
        if junction is None:
            continue
        signals.append(
            {
                "id": tls_id,
                "x": float(junction.get("x") or 0.0),
                "y": float(junction.get("y") or 0.0),
                "shape": _parse_shape(junction.get("shape")),
            }
        )

    return {
        "version": 1,
        "scope": {
            "mode": scope["mode"],
            "controlled_tls_ids": scope["controlled_tls_ids"],
        },
        "source_net": scope["net_file"],
        "bounds": bounds,
        "roads": roads,
        "crossings": crossings,
        "walking_areas": walking_areas,
        "signals": signals,
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    network = build_visual_network()
    OUTPUT_PATH.write_text(json.dumps(network, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
