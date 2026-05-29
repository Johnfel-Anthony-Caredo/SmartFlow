"""Dash-native SVG traffic map for the SUMO-backed SMARTFLOW runtime."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

class _FallbackComponent:
    def __init__(self, *children, **props):
        self.children = list(children) if children else props.pop("children", None)
        for key, value in props.items():
            setattr(self, key, value)

class _FallbackHtml:
    def __getattr__(self, _name):
        return _FallbackComponent

try:
    from dash import html
except ImportError:  # pragma: no cover - lets renderer mapping tests run without Dash installed.
    html = _FallbackHtml()

try:
    import dash_svg as svg
except ImportError:  # pragma: no cover
    if isinstance(html, _FallbackHtml):
        svg = _FallbackHtml()
    else:
        raise

from simulation.sumo_config import APPROACH_LANES, MAJOR_TLS_IDS, MINOR_TLS_IDS
from simulation.sumo_state import canonical_signal_states


VISUAL_NETWORK_PATH = Path(__file__).resolve().parents[1] / "assets" / "generated" / "visual_network.json"
MAP_MARGIN = 18.0
FOCUS_MARGIN = 16.0
INTERSECTION_FOCUS_RADIUS = 85.0
TARGET_VIEW_ASPECT = 1.75
VEHICLE_LIMIT = 70
PEDESTRIAN_LIMIT = 50
ROAD_WIDTH_SCALE = 6.5
MIN_ROAD_SURFACE_WIDTH = 18.0
SIDEWALK_BAND_WIDTH = 24.0
CURB_BAND_WIDTH = 7.0
JUNCTION_HALF_DEPTH = 28.0
JUNCTION_SHADOW_SCALE = 1.14
CROSSWALK_OFFSET = 12.0
CROSSWALK_BED_DEPTH = 16.0
CROSSWALK_STRIPE_COUNT = 6
CROSSWALK_STRIPE_SPACING = 4.2
CROSSWALK_STRIPE_WIDTH = 3.1
APPROACH_LABEL_DISTANCE = 72.0
SIGNAL_HOUSING_WIDTH = 16.0
SIGNAL_HOUSING_HEIGHT = 38.0
SIGNAL_POLE_LENGTH = 14.0
SIGNAL_HALO_RADIUS = 18.0
LANE_ARROW_DISTANCE = 56.0
STOP_BAR_DISTANCE = 34.0

APPROACH_LABELS = {
    "north": "NORTH",
    "south": "SOUTH",
    "east": "EAST",
    "west": "WEST",
}


@dataclass(frozen=True)
class MapTransform:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    margin: float = MAP_MARGIN

    @property
    def width(self) -> float:
        return (self.max_x - self.min_x) + (self.margin * 2)

    @property
    def height(self) -> float:
        return (self.max_y - self.min_y) + (self.margin * 2)

    def point(self, raw: dict[str, Any]) -> tuple[float, float]:
        return self.xy(float(raw.get("x", 0.0)), float(raw.get("y", 0.0)))

    def xy(self, x_value: float, y_value: float) -> tuple[float, float]:
        return (
            round((x_value - self.min_x) + self.margin, 2),
            round((self.max_y - y_value) + self.margin, 2),
        )

    def points(self, shape: list[dict[str, Any]]) -> str:
        return " ".join(f"{x},{y}" for x, y in (self.point(point) for point in shape))


@dataclass(frozen=True)
class ApproachLayout:
    name: str
    center_shape: tuple[tuple[float, float], ...]
    lane_shapes: tuple[tuple[tuple[float, float], ...], ...]
    stop_point: tuple[float, float]
    outer_point: tuple[float, float]
    direction: tuple[float, float]
    perpendicular: tuple[float, float]
    road_width: float

    @property
    def lane_count(self) -> int:
        return len(self.lane_shapes)


def load_visual_network(path: Path | str = VISUAL_NETWORK_PATH) -> dict[str, Any]:
    network_path = Path(path)
    return json.loads(network_path.read_text(encoding="utf-8"))


def _transform_for(network: dict[str, Any]) -> MapTransform:
    focused = _focused_transform_for(network)
    if focused is not None:
        return focused

    bounds = network["bounds"]
    return MapTransform(
        min_x=float(bounds["min_x"]),
        min_y=float(bounds["min_y"]),
        max_x=float(bounds["max_x"]),
        max_y=float(bounds["max_y"]),
    )


def _focused_transform_for(network: dict[str, Any]) -> MapTransform | None:
    focus_points = _focus_points_for(network)
    if not focus_points:
        return None

    xs = [point[0] for point in focus_points]
    ys = [point[1] for point in focus_points]
    min_x, max_x, min_y, max_y = _fit_bounds_to_aspect(
        min(xs),
        max(xs),
        min(ys),
        max(ys),
        TARGET_VIEW_ASPECT,
    )
    return MapTransform(
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        margin=FOCUS_MARGIN,
    )


def _focus_points_for(network: dict[str, Any]) -> list[tuple[float, float]]:
    center_x, center_y = _intersection_center(network)
    points: list[tuple[float, float]] = [(center_x, center_y)]

    for signal in network.get("signals", []):
        points.append((float(signal.get("x", center_x)), float(signal.get("y", center_y))))

    for group_name in ("crossings", "walking_areas"):
        for edge in network.get(group_name, []):
            for lane in edge.get("lanes", []):
                points.extend(_shape_points(lane.get("shape", [])))

    lane_lookup = _lane_lookup(network)
    for lane_ids in APPROACH_LANES.values():
        for lane_id in lane_ids:
            lane = lane_lookup.get(lane_id)
            if not lane:
                continue

            clipped = [
                point
                for point in _shape_points(lane.get("shape", []))
                if _distance(point, (center_x, center_y)) <= INTERSECTION_FOCUS_RADIUS
            ]
            points.extend(clipped)

    return points


def _intersection_center(network: dict[str, Any]) -> tuple[float, float]:
    signals = network.get("signals", [])
    if signals:
        return (
            sum(float(signal.get("x", 0.0)) for signal in signals) / len(signals),
            sum(float(signal.get("y", 0.0)) for signal in signals) / len(signals),
        )

    crossing_points = [
        point
        for edge in network.get("crossings", [])
        for lane in edge.get("lanes", [])
        for point in _shape_points(lane.get("shape", []))
    ]
    if crossing_points:
        xs = [point[0] for point in crossing_points]
        ys = [point[1] for point in crossing_points]
        return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)

    bounds = network["bounds"]
    return (
        (float(bounds["min_x"]) + float(bounds["max_x"])) / 2,
        (float(bounds["min_y"]) + float(bounds["max_y"])) / 2,
    )


def _shape_points(shape: list[dict[str, Any]]) -> list[tuple[float, float]]:
    return [
        (float(point.get("x", 0.0)), float(point.get("y", 0.0)))
        for point in shape
    ]


def _fit_bounds_to_aspect(
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    target_aspect: float,
) -> tuple[float, float, float, float]:
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        return min_x, max_x, min_y, max_y

    current_aspect = width / height
    if current_aspect < target_aspect:
        desired_width = height * target_aspect
        horizontal_padding = (desired_width - width) / 2
        return (
            min_x - horizontal_padding,
            max_x + horizontal_padding,
            min_y,
            max_y,
        )

    desired_height = width / target_aspect
    vertical_padding = (desired_height - height) / 2
    return (
        min_x,
        max_x,
        min_y - vertical_padding,
        max_y + vertical_padding,
    )


def _distance(point: tuple[float, float], other: tuple[float, float]) -> float:
    return math.hypot(point[0] - other[0], point[1] - other[1])


def _is_pedestrian_lane(lane: dict[str, Any]) -> bool:
    allow = str(lane.get("allow", ""))
    disallow = str(lane.get("disallow", ""))
    return "pedestrian" in allow and "pedestrian" not in disallow


def _lane_lookup(network: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup = {}
    for group_name in ("roads", "crossings", "walking_areas"):
        for edge in network.get(group_name, []):
            for lane in edge.get("lanes", []):
                lookup[lane.get("id", "")] = lane
    return lookup


def _build_approach_layouts(network: dict[str, Any], center: tuple[float, float]) -> tuple[ApproachLayout, ...]:
    lane_lookup = _lane_lookup(network)
    layouts: list[ApproachLayout] = []

    for name, lane_ids in APPROACH_LANES.items():
        lane_shapes = []
        lane_width_sum = 0.0
        for lane_id in lane_ids:
            lane = lane_lookup.get(lane_id)
            if not lane:
                continue
            points = tuple(_shape_points(lane.get("shape", [])))
            if len(points) < 2:
                continue
            lane_shapes.append(points)
            lane_width_sum += float(lane.get("width", 3.2))

        if not lane_shapes:
            continue

        center_shape = tuple(_average_shape(lane_shapes))
        geometry = _approach_geometry_for_points(list(center_shape), center)
        if geometry is None:
            continue

        stop_point, outer_point, direction = geometry
        layouts.append(
            ApproachLayout(
                name=name,
                center_shape=center_shape,
                lane_shapes=tuple(lane_shapes),
                stop_point=stop_point,
                outer_point=outer_point,
                direction=direction,
                perpendicular=_perpendicular(direction),
                road_width=max(MIN_ROAD_SURFACE_WIDTH, round(lane_width_sum * ROAD_WIDTH_SCALE, 2)),
            )
        )

    return tuple(layouts)


def _signal_color(signal_id: str, phase: str) -> str:
    ns_state, ew_state = canonical_signal_states(phase)
    if signal_id in MAJOR_TLS_IDS:
        return ns_state
    if signal_id in MINOR_TLS_IDS:
        return ew_state
    return "red"


def build_traffic_map_payload(state: dict[str, Any] | None, network: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime = state or {}
    network = network or load_visual_network()
    queues = runtime.get("queues") or _queues_from_chart_history(runtime)
    vehicles = list(runtime.get("vehicles", []))[:VEHICLE_LIMIT]
    pedestrians = list(runtime.get("pedestrians", []))[:PEDESTRIAN_LIMIT]

    return {
        "network_version": network.get("version"),
        "source_net": network.get("source_net"),
        "status": runtime.get("status", "stopped"),
        "phase": runtime.get("phase", "NS_GREEN"),
        "phase_remaining": runtime.get("phase_remaining", 0),
        "vehicle_count": len(vehicles),
        "pedestrian_count": len(pedestrians),
        "queues": queues,
        "vehicles": vehicles,
        "pedestrians": pedestrians,
        "constraint_marker": runtime.get("visual", {}).get("constraint_marker", {"active": False}),
        "scenario": runtime.get("scenario", {}),
    }


def _queues_from_chart_history(state: dict[str, Any]) -> dict[str, int]:
    flow = state.get("charts", {}).get("traffic_flow", [])
    if not flow:
        return {}
    latest = flow[-1]
    return {
        "north": int(latest.get("north", 0)),
        "south": int(latest.get("south", 0)),
        "east": int(latest.get("east", 0)),
        "west": int(latest.get("west", 0)),
    }


def build_traffic_map(
    state: dict[str, Any] | None = None,
    *,
    network: dict[str, Any] | None = None,
    component_id: str | None = None,
    class_name: str = "traffic-map",
):
    network = network or load_visual_network()
    runtime = build_traffic_map_payload(state, network)
    center = _intersection_center(network)
    approaches = _build_approach_layouts(network, center)
    transform = _transform_for(network)
    view_box = f"0 0 {transform.width:.2f} {transform.height:.2f}"

    svg_children = [
        _defs(),
        svg.Rect(x="0", y="0", width=str(transform.width), height=str(transform.height), className="traffic-map-ground"),
        _build_static_layers(network, transform, center, approaches),
        _build_queue_layers(transform, runtime["queues"], approaches),
        _build_crossing_layers(transform, center, approaches),
        _build_stop_bar_layers(transform, center, approaches),
        _build_lane_arrow_layers(transform, center, approaches),
        _build_constraint_layer(network, transform, runtime["constraint_marker"], approaches),
        _build_signal_layers(network, transform, runtime["phase"]),
        _build_vehicle_layers(transform, runtime["vehicles"]),
        _build_pedestrian_layers(transform, runtime["pedestrians"]),
        _build_map_labels(transform, center, approaches),
    ]

    overlay_children = []

    if _is_empty_runtime(runtime):
        overlay_children.append(
            html.Div(
                className="traffic-map-empty-banner",
                children=[
                    html.I(className="fa-solid fa-circle-info", style={"marginRight": "6px", "opacity": "0.5"}),
                    "Waiting for live simulation data",
                ],
            )
        )

    div_props = {"className": class_name}
    if component_id is not None:
        div_props["id"] = component_id

    return html.Div(
        children=[
            svg.Svg(
                className="traffic-map-svg",
                viewBox=view_box,
                preserveAspectRatio="xMidYMid slice",
                role="img",
                children=svg_children,
            ),
            html.Div(className="traffic-map-overlay", children=overlay_children),
        ],
        **div_props
    )


def build_traffic_map_legend(class_name: str = "traffic-map-legend-row"):
    return html.Div(
        className=class_name,
        children=[
            _legend_item("signal-green", "Signals"),
            _legend_item("queue", "Queues"),
            _legend_item("vehicle", "Vehicles"),
            _legend_item("pedestrian", "Pedestrians"),
            _legend_item("hazard", "Constraints"),
        ],
    )


def _defs():
    return svg.Defs(children=[
        svg.Pattern(id="traffic-map-hazard-pattern", width="12", height="12", patternUnits="userSpaceOnUse", patternTransform="rotate(45)", children=[
            svg.Rect(x="0", y="0", width="6", height="12", className="traffic-map-hazard-stripe"),
        ]),
        svg.Filter(id="vehicle-shadow", x="-20%", y="-20%", width="140%", height="140%", children=[
            svg.FeGaussianBlur(stdDeviation="1.5", result="shadow"),
            svg.FeOffset(dx="1", dy="1", result="offsetShadow", children=[]),
            svg.FeMerge(children=[
                svg.FeMergeNode(children=[]),
                svg.FeMergeNode(children=[]),
            ]),
        ]),
        svg.Filter(id="ped-glow", x="-50%", y="-50%", width="200%", height="200%", children=[
            svg.FeGaussianBlur(stdDeviation="2", result="blur"),
            svg.FeMerge(children=[
                svg.FeMergeNode(children=[]),
                svg.FeMergeNode(children=[]),
            ]),
        ]),
    ])


def _build_static_layers(
    network: dict[str, Any],
    transform: MapTransform,
    center: tuple[float, float],
    approaches: tuple[ApproachLayout, ...],
):
    children = []

    for road in _long_vehicle_road_edges(network, center):
        vehicle_lanes = [
            lane
            for lane in road.get("lanes", [])
            if not _is_pedestrian_lane(lane)
        ]
        if not vehicle_lanes:
            continue

        lane_shapes = [tuple(_shape_points(lane.get("shape", []))) for lane in vehicle_lanes]
        center_shape = _average_shape(lane_shapes)
        total_lane_width = sum(float(lane.get("width", 3.2)) for lane in vehicle_lanes)
        road_width = max(MIN_ROAD_SURFACE_WIDTH, round(total_lane_width * ROAD_WIDTH_SCALE, 2))

        children.append(_polyline_points(center_shape, transform, "traffic-map-sidewalk-zone", road_width + SIDEWALK_BAND_WIDTH))
        children.append(_polyline_points(center_shape, transform, "traffic-map-curb-band", road_width + CURB_BAND_WIDTH))
        children.append(_polyline_points(center_shape, transform, "traffic-map-road", road_width))

        if len(lane_shapes) > 1:
            children.append(_polyline_points(center_shape, transform, "traffic-map-lane-divider", 2.2))
        else:
            children.append(_polyline_points(center_shape, transform, "traffic-map-lane-guide", 1.4))

    junction_points = _junction_polygon_points(center, approaches)
    if junction_points:
        children.append(_polygon_points(
            _scaled_polygon_points(junction_points, center, JUNCTION_SHADOW_SCALE),
            transform,
            "traffic-map-junction-shadow",
        ))
        children.append(_polygon_points(junction_points, transform, "traffic-map-junction-box"))

    for area in network.get("walking_areas", []):
        for lane in area.get("lanes", []):
            children.append(_shape(lane, transform, "traffic-map-corner-plaza", polygon=True))

    return svg.G(className="traffic-map-static", children=children)


def _build_crossing_layers(
    transform: MapTransform,
    center: tuple[float, float],
    approaches: tuple[ApproachLayout, ...],
):
    children = []
    stripe_midpoint = (CROSSWALK_STRIPE_COUNT - 1) / 2

    for approach in approaches:
        crossing_center = _offset_point(center, approach.direction, -(JUNCTION_HALF_DEPTH + CROSSWALK_OFFSET))
        road_half = max(10.0, (approach.road_width / 2) - 4.0)

        bed_start = _offset_point(crossing_center, approach.perpendicular, road_half)
        bed_end = _offset_point(crossing_center, approach.perpendicular, -road_half)
        start_x, start_y = transform.xy(*bed_start)
        end_x, end_y = transform.xy(*bed_end)
        children.append(
            svg.Line(
                x1=str(start_x),
                y1=str(start_y),
                x2=str(end_x),
                y2=str(end_y),
                className="traffic-map-crosswalk-bed",
                strokeWidth=str(CROSSWALK_BED_DEPTH),
            )
        )

        for index in range(CROSSWALK_STRIPE_COUNT):
            stripe_center = _offset_point(
                crossing_center,
                approach.direction,
                (index - stripe_midpoint) * CROSSWALK_STRIPE_SPACING,
            )
            stripe_start = _offset_point(stripe_center, approach.perpendicular, road_half - 1.0)
            stripe_end = _offset_point(stripe_center, approach.perpendicular, -(road_half - 1.0))
            start_x, start_y = transform.xy(*stripe_start)
            end_x, end_y = transform.xy(*stripe_end)
            children.append(
                svg.Line(
                    x1=str(start_x),
                    y1=str(start_y),
                    x2=str(end_x),
                    y2=str(end_y),
                    className="traffic-map-crossing",
                    strokeWidth=str(CROSSWALK_STRIPE_WIDTH),
                )
            )

    return svg.G(className="traffic-map-crossings", children=children)


def _polyline(lane: dict[str, Any], transform: MapTransform, class_name: str, scale: float):
    width = max(float(lane.get("width", 2.0)) * scale, 1.0)
    return svg.Polyline(
        points=transform.points(lane.get("shape", [])),
        className=class_name,
        strokeWidth=str(round(width, 2)),
    )


def _polyline_points(
    points: list[tuple[float, float]] | tuple[tuple[float, float], ...],
    transform: MapTransform,
    class_name: str,
    width: float,
):
    return svg.Polyline(
        points=_points_string(points, transform),
        className=class_name,
        strokeWidth=str(round(width, 2)),
    )


def _polygon_points(
    points: list[tuple[float, float]] | tuple[tuple[float, float], ...],
    transform: MapTransform,
    class_name: str,
):
    return svg.Polygon(points=_points_string(points, transform), className=class_name)


def _shape(lane: dict[str, Any], transform: MapTransform, class_name: str, polygon: bool = False):
    points = transform.points(lane.get("shape", []))
    if polygon and len(lane.get("shape", [])) >= 3:
        return svg.Polygon(points=points, className=class_name)
    return svg.Polyline(points=points, className=class_name, strokeWidth=str(float(lane.get("width", 2.0))))


def _points_string(
    points: list[tuple[float, float]] | tuple[tuple[float, float], ...],
    transform: MapTransform,
) -> str:
    return " ".join(
        f"{x},{y}"
        for x, y in (transform.xy(point[0], point[1]) for point in points)
    )


def _average_shape(
    shapes: list[tuple[tuple[float, float], ...]],
) -> list[tuple[float, float]]:
    length = min(len(shape) for shape in shapes)
    averaged = []
    for index in range(length):
        xs = [shape[index][0] for shape in shapes]
        ys = [shape[index][1] for shape in shapes]
        averaged.append((sum(xs) / len(xs), sum(ys) / len(ys)))
    return averaged


def _long_vehicle_road_edges(network: dict[str, Any], center: tuple[float, float]) -> list[dict[str, Any]]:
    edges = []
    for road in network.get("roads", []):
        vehicle_lanes = [
            lane
            for lane in road.get("lanes", [])
            if not _is_pedestrian_lane(lane)
        ]
        if not vehicle_lanes:
            continue

        farthest_distance = 0.0
        longest_length = 0.0
        for lane in vehicle_lanes:
            points = _shape_points(lane.get("shape", []))
            if len(points) < 2:
                continue
            farthest_distance = max(farthest_distance, max(_distance(point, center) for point in points))
            longest_length = max(longest_length, _polyline_length(points))

        if longest_length < 20.0 or farthest_distance < 70.0:
            continue
        edges.append(road)

    return edges


def _polyline_length(points: list[tuple[float, float]]) -> float:
    return sum(
        _distance(points[index], points[index + 1])
        for index in range(len(points) - 1)
    )


def _build_queue_layers(transform: MapTransform, queues: dict[str, Any], approaches: tuple[ApproachLayout, ...]):
    children = []
    for approach in approaches:
        queue_count = int(queues.get(approach.name, 0) or 0)
        if queue_count <= 0:
            continue
        width = min(max(approach.road_width - 8.0, 12.0), 16.0 + queue_count * 2.6)
        opacity = min(0.68, 0.18 + queue_count * 0.08)
        children.append(svg.Polyline(
            points=_points_string(approach.center_shape, transform),
            className=f"traffic-map-queue traffic-map-queue-{approach.name}",
            strokeWidth=str(round(width, 2)),
            opacity=str(round(opacity, 2)),
            children=[html.Title(f"{approach.name.title()} queue: {queue_count} vehicles")],
        ))
    return svg.G(className="traffic-map-queues", children=children)


def _build_stop_bar_layers(
    transform: MapTransform,
    center: tuple[float, float],
    approaches: tuple[ApproachLayout, ...],
):
    children = []

    for approach in approaches:
        bar_center = _offset_point(center, approach.direction, -STOP_BAR_DISTANCE)
        half_width = max(8.0, (approach.road_width / 2) - 4.0)
        start = _offset_point(bar_center, approach.perpendicular, half_width)
        end = _offset_point(bar_center, approach.perpendicular, -half_width)
        start_x, start_y = transform.xy(*start)
        end_x, end_y = transform.xy(*end)
        children.append(
            svg.Line(
                x1=str(start_x),
                y1=str(start_y),
                x2=str(end_x),
                y2=str(end_y),
                className="traffic-map-stop-bar",
            )
        )

    return svg.G(className="traffic-map-stop-bars", children=children)


def _build_lane_arrow_layers(
    transform: MapTransform,
    center: tuple[float, float],
    approaches: tuple[ApproachLayout, ...],
):
    children = []

    for approach in approaches:
        if approach.lane_count < 2:
            continue

        arrow_center = _offset_point(center, approach.direction, -LANE_ARROW_DISTANCE)
        nose = _offset_point(arrow_center, approach.direction, 10.0)
        tail = _offset_point(arrow_center, approach.direction, -10.0)
        wing_base = _offset_point(nose, approach.direction, -7.0)
        wing_left = _offset_point(wing_base, approach.perpendicular, 4.4)
        wing_right = _offset_point(wing_base, approach.perpendicular, -4.4)

        children.append(
            svg.G(
                className="traffic-map-lane-arrow",
                children=[
                    svg.Line(
                        x1=str(transform.xy(*tail)[0]),
                        y1=str(transform.xy(*tail)[1]),
                        x2=str(transform.xy(*nose)[0]),
                        y2=str(transform.xy(*nose)[1]),
                        className="traffic-map-lane-arrow-shaft",
                    ),
                    svg.Polygon(
                        points=" ".join(
                            f"{x},{y}"
                            for x, y in (
                                transform.xy(*nose),
                                transform.xy(*wing_left),
                                transform.xy(*wing_right),
                            )
                        ),
                        className="traffic-map-lane-arrow-head",
                    ),
                ],
            )
        )

    return svg.G(className="traffic-map-lane-arrows", children=children)


def _build_signal_layers(network: dict[str, Any], transform: MapTransform, phase: str):
    children = []
    for signal in network.get("signals", []):
        x, y = transform.xy(float(signal.get("x", 0.0)), float(signal.get("y", 0.0)))
        color = _signal_color(str(signal.get("id", "")), phase)
        children.append(svg.G(
            className=f"traffic-map-signal signal-{color}",
            transform=f"translate({x},{y})",
            children=[
                svg.Circle(cx="0", cy="0", r=str(SIGNAL_HALO_RADIUS), className="traffic-map-signal-halo"),
                svg.Rect(
                    x=str(-(SIGNAL_HOUSING_WIDTH / 2)),
                    y=str(-(SIGNAL_HOUSING_HEIGHT / 2)),
                    width=str(SIGNAL_HOUSING_WIDTH),
                    height=str(SIGNAL_HOUSING_HEIGHT),
                    rx="5",
                    ry="5",
                    className="traffic-map-signal-housing",
                ),
                svg.Circle(cx="0", cy="-11", r="4.5",
                           className=f"traffic-map-signal-light signal-light-red {'active' if color == 'red' else ''}"),
                svg.Circle(cx="0", cy="0", r="4.5",
                           className=f"traffic-map-signal-light signal-light-yellow {'active' if color == 'yellow' else ''}"),
                svg.Circle(cx="0", cy="11", r="4.5",
                           className=f"traffic-map-signal-light signal-light-green {'active' if color == 'green' else ''}"),
                svg.Line(
                    x1="0",
                    y1=str(SIGNAL_HOUSING_HEIGHT / 2),
                    x2="0",
                    y2=str((SIGNAL_HOUSING_HEIGHT / 2) + SIGNAL_POLE_LENGTH),
                    className="traffic-map-signal-pole",
                ),
                html.Title(f"Signal {signal.get('id')}: {color}"),
            ],
        ))
    return svg.G(className="traffic-map-signals", children=children)


def _build_vehicle_layers(transform: MapTransform, vehicles: list[dict[str, Any]]):
    children = []
    for vehicle in vehicles:
        x, y = transform.xy(float(vehicle.get("x", 0.0)), float(vehicle.get("y", 0.0)))
        angle = float(vehicle.get("angle", 0.0)) - 90.0
        visual_type = vehicle.get("visual_type", "car")
        emergency = bool(vehicle.get("emergency"))
        length, width = _vehicle_size(visual_type)
        class_name = f"traffic-map-vehicle {visual_type}"
        if emergency:
            class_name = f"traffic-map-vehicle emergency {visual_type}"
        children.append(svg.G(
            className=class_name,
            transform=f"translate({x},{y}) rotate({round(angle, 2)})",
            children=_build_vehicle_body(visual_type, emergency, length, width) + [
                html.Title(_vehicle_title(vehicle)),
            ],
        ))
    return svg.G(className="traffic-map-vehicles", children=children)


def _build_vehicle_body(visual_type: str, emergency: bool, length: float, width: float) -> list:
    """Build a top-down vehicle silhouette with body, windshield, and wheels."""
    hl = length / 2
    hw = width / 2
    # Wheel dimensions
    wl, ww = length * 0.18, width * 0.18
    # Wheel offset from centre
    wx = hl * 0.55
    wy = hw - ww * 0.3

    parts = [
        # Drop shadow body
        svg.Rect(x=str(-hl + 0.5), y=str(-hw + 0.5), width=str(length), height=str(width),
                 rx="3", ry="3", className="traffic-map-vehicle-shadow"),
        # Main car body
        svg.Rect(x=str(-hl), y=str(-hw), width=str(length), height=str(width),
                 rx="3", ry="3", className="traffic-map-vehicle-body"),
        # Windshield (front window)
        svg.Rect(x=str(hl * 0.15), y=str(-hw + 1.2), width=str(length * 0.22), height=str(width - 2.4),
                 rx="1.5", ry="1.5", className="traffic-map-vehicle-windshield"),
        # Rear window
        svg.Rect(x=str(-hl + 1), y=str(-hw + 1.5), width=str(length * 0.14), height=str(width - 3.0),
                 rx="1", ry="1", className="traffic-map-vehicle-rear-window"),
        # Front-right wheel
        svg.Rect(x=str(wx - wl / 2), y=str(wy - ww / 2), width=str(wl), height=str(ww),
                 rx="0.5", ry="0.5", className="traffic-map-vehicle-wheel"),
        # Front-left wheel
        svg.Rect(x=str(wx - wl / 2), y=str(-wy - ww / 2), width=str(wl), height=str(ww),
                 rx="0.5", ry="0.5", className="traffic-map-vehicle-wheel"),
        # Rear-right wheel
        svg.Rect(x=str(-wx - wl / 2), y=str(wy - ww / 2), width=str(wl), height=str(ww),
                 rx="0.5", ry="0.5", className="traffic-map-vehicle-wheel"),
        # Rear-left wheel
        svg.Rect(x=str(-wx - wl / 2), y=str(-wy - ww / 2), width=str(wl), height=str(ww),
                 rx="0.5", ry="0.5", className="traffic-map-vehicle-wheel"),
        # Headlights (two small circles at front)
        svg.Circle(cx=str(hl - 0.8), cy=str(-hw + 1.8), r="1.2", className="traffic-map-vehicle-headlight"),
        svg.Circle(cx=str(hl - 0.8), cy=str(hw - 1.8), r="1.2", className="traffic-map-vehicle-headlight"),
        # Taillights (two small rects at rear)
        svg.Rect(x=str(-hl), y=str(-hw + 1.0), width="1.5", height="2.0",
                 rx="0.3", ry="0.3", className="traffic-map-vehicle-taillight"),
        svg.Rect(x=str(-hl), y=str(hw - 3.0), width="1.5", height="2.0",
                 rx="0.3", ry="0.3", className="traffic-map-vehicle-taillight"),
    ]

    # Emergency cross marking
    if emergency:
        parts.append(svg.Line(x1=str(-3), y1="0", x2="3", y2="0", className="traffic-map-vehicle-cross"))
        parts.append(svg.Line(x1="0", y1="-3", x2="0", y2="3", className="traffic-map-vehicle-cross"))
        # Siren light bar centered on the roof
        parts.append(svg.Rect(x="-1.5", y="-4.0", width="3.0", height="8.0", rx="1.0", ry="1.0", className="traffic-map-vehicle-siren"))

    # Truck/bus cargo area
    if visual_type in {"truck", "bus"}:
        parts.append(svg.Rect(
            x=str(-hl + 1.5), y=str(-hw + 1.2), width=str(length * 0.45), height=str(width - 2.4),
            rx="1", ry="1", className="traffic-map-vehicle-cargo",
        ))

    return parts


def _vehicle_size(visual_type: str) -> tuple[float, float]:
    if visual_type in {"truck", "bus"}:
        return 32.0, 14.5
    if visual_type == "ambulance":
        return 28.0, 13.0
    return 24.0, 11.5


def _vehicle_title(vehicle: dict[str, Any]) -> str:
    return (
        f"{vehicle.get('id', 'vehicle')} | {vehicle.get('visual_type', 'vehicle')} | "
        f"{vehicle.get('speed', 0)} m/s | wait {vehicle.get('wait_time', 0)}s | "
        f"{vehicle.get('lane_id', 'unknown lane')}"
    )


def _build_pedestrian_layers(transform: MapTransform, pedestrians: list[dict[str, Any]]):
    children = []
    for pedestrian in pedestrians:
        x, y = transform.xy(float(pedestrian.get("x", 0.0)), float(pedestrian.get("y", 0.0)))
        children.append(svg.G(
            className="traffic-map-pedestrian",
            transform=f"translate({x},{y})",
            children=[
                svg.Circle(cx="0", cy="0", r="9", className="traffic-map-ped-glow"),
                svg.Ellipse(cx="0", cy="4", rx="3.4", ry="4.8", className="traffic-map-ped-body"),
                svg.Circle(cx="0", cy="-4.4", r="3.2", className="traffic-map-ped-head"),
                svg.Line(x1="-1", y1="8", x2="-2.8", y2="12", className="traffic-map-ped-limb"),
                svg.Line(x1="1", y1="8", x2="2.8", y2="12", className="traffic-map-ped-limb"),
                svg.Line(x1="-3.2", y1="1", x2="-6.0", y2="4.8", className="traffic-map-ped-limb"),
                svg.Line(x1="3.2", y1="1", x2="6.0", y2="4.8", className="traffic-map-ped-limb"),
                html.Title(
                    f"{pedestrian.get('id', 'pedestrian')} | {pedestrian.get('speed', 0)} m/s | {pedestrian.get('lane_id', 'unknown lane')}"
                ),
            ],
        ))
    return svg.G(className="traffic-map-pedestrians", children=children)


def _build_constraint_layer(
    network: dict[str, Any],
    transform: MapTransform,
    marker: dict[str, Any],
    approaches: tuple[ApproachLayout, ...],
):
    if not marker or not marker.get("active"):
        return svg.G(className="traffic-map-constraints")
    x, y = transform.xy(float(marker.get("x", 0.0)), float(marker.get("y", 0.0)))
    label = marker.get("label", "Road constraint")
    band = _constraint_band(network, transform, marker, approaches)
    return svg.G(
        className="traffic-map-constraints",
        children=[
            band,
            svg.G(className="traffic-map-constraint", transform=f"translate({x},{y})", children=[
                svg.Circle(cx="0", cy="0", r="17", className="traffic-map-constraint-zone"),
                svg.Rect(x="-16", y="-16", width="32", height="32", rx="4", ry="4", className="traffic-map-constraint-fill"),
                svg.Line(x1="-11", y1="-11", x2="11", y2="11", className="traffic-map-constraint-x"),
                svg.Line(x1="11", y1="-11", x2="-11", y2="11", className="traffic-map-constraint-x"),
                html.Title(label),
            ]),
        ],
    )


def _build_map_labels(
    transform: MapTransform,
    center: tuple[float, float],
    approaches: tuple[ApproachLayout, ...],
):
    children = []
    for approach in approaches:
        label_point = _offset_point(center, approach.direction, -APPROACH_LABEL_DISTANCE)
        x, y = transform.xy(*label_point)
        children.append(
            svg.Text(
                x=str(x),
                y=str(y),
                className="traffic-map-edge-label",
                children=APPROACH_LABELS.get(approach.name, approach.name.upper()),
            )
        )
    return svg.G(className="traffic-map-labels", children=children)


def _approach_geometry(
    lane: dict[str, Any] | None,
    center: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None:
    if not lane:
        return None

    points = _shape_points(lane.get("shape", []))
    return _approach_geometry_for_points(points, center)


def _approach_geometry_for_points(
    points: list[tuple[float, float]],
    center: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None:
    if len(points) < 2:
        return None

    first_distance = _distance(points[0], center)
    last_distance = _distance(points[-1], center)
    if first_distance <= last_distance:
        stop_point = points[0]
        reference = points[1]
        outer_point = points[-1]
    else:
        stop_point = points[-1]
        reference = points[-2]
        outer_point = points[0]

    direction = _normalize((stop_point[0] - reference[0], stop_point[1] - reference[1]))
    return stop_point, outer_point, direction


def _offset_point(point: tuple[float, float], direction: tuple[float, float], distance: float) -> tuple[float, float]:
    return (
        point[0] + (direction[0] * distance),
        point[1] + (direction[1] * distance),
    )


def _perpendicular(direction: tuple[float, float]) -> tuple[float, float]:
    return (-direction[1], direction[0])


def _normalize(direction: tuple[float, float]) -> tuple[float, float]:
    length = math.hypot(direction[0], direction[1])
    if length == 0:
        return (1.0, 0.0)
    return (direction[0] / length, direction[1] / length)


def _junction_polygon_points(
    center: tuple[float, float],
    approaches: tuple[ApproachLayout, ...],
) -> list[tuple[float, float]]:
    points = []
    for approach in approaches:
        edge_center = _offset_point(center, approach.direction, -JUNCTION_HALF_DEPTH)
        half_width = max(8.0, (approach.road_width / 2) - 1.5)
        points.append(_offset_point(edge_center, approach.perpendicular, half_width))
        points.append(_offset_point(edge_center, approach.perpendicular, -half_width))

    return sorted(
        points,
        key=lambda point: math.atan2(point[1] - center[1], point[0] - center[0]),
    )


def _scaled_polygon_points(
    points: list[tuple[float, float]],
    center: tuple[float, float],
    scale: float,
) -> list[tuple[float, float]]:
    return [
        (
            center[0] + ((point[0] - center[0]) * scale),
            center[1] + ((point[1] - center[1]) * scale),
        )
        for point in points
    ]


def _constraint_band(
    network: dict[str, Any],
    transform: MapTransform,
    marker: dict[str, Any],
    approaches: tuple[ApproachLayout, ...],
):
    marker_point = (float(marker.get("x", 0.0)), float(marker.get("y", 0.0)))
    nearest_approach = None
    nearest_projection = None
    nearest_distance = None

    for approach in approaches:
        projection = _nearest_point_on_polyline(list(approach.center_shape), marker_point)
        distance = _distance(projection, marker_point)
        if nearest_distance is None or distance < nearest_distance:
            nearest_distance = distance
            nearest_approach = approach
            nearest_projection = projection

    if nearest_approach is None or nearest_projection is None:
        x, y = transform.xy(*marker_point)
        return svg.Circle(cx=str(x), cy=str(y), r="18", className="traffic-map-constraint-band")

    band_start = _offset_point(nearest_projection, nearest_approach.direction, -24.0)
    band_end = _offset_point(nearest_projection, nearest_approach.direction, 24.0)
    start_x, start_y = transform.xy(*band_start)
    end_x, end_y = transform.xy(*band_end)
    return svg.Line(
        x1=str(start_x),
        y1=str(start_y),
        x2=str(end_x),
        y2=str(end_y),
        className="traffic-map-constraint-band",
    )


def _nearest_point_on_polyline(
    points: list[tuple[float, float]],
    target: tuple[float, float],
) -> tuple[float, float]:
    nearest_point = points[0]
    nearest_distance = None

    for index in range(len(points) - 1):
        projected = _project_point_to_segment(points[index], points[index + 1], target)
        distance = _distance(projected, target)
        if nearest_distance is None or distance < nearest_distance:
            nearest_point = projected
            nearest_distance = distance

    return nearest_point


def _project_point_to_segment(
    segment_start: tuple[float, float],
    segment_end: tuple[float, float],
    target: tuple[float, float],
) -> tuple[float, float]:
    dx = segment_end[0] - segment_start[0]
    dy = segment_end[1] - segment_start[1]
    segment_length_squared = (dx * dx) + (dy * dy)
    if segment_length_squared == 0:
        return segment_start

    t = (
        ((target[0] - segment_start[0]) * dx) +
        ((target[1] - segment_start[1]) * dy)
    ) / segment_length_squared
    t = max(0.0, min(1.0, t))
    return (
        segment_start[0] + (dx * t),
        segment_start[1] + (dy * t),
    )


def _legend_item(kind: str, label: str):
    swatch_class = f"traffic-map-legend-swatch {kind}"
    return html.Span(className="traffic-map-legend-item", children=[
        html.Span(className=swatch_class),
        html.Span(label),
    ])


def _is_empty_runtime(payload: dict[str, Any]) -> bool:
    if payload.get("status") == "running":
        return False
    return payload.get("vehicle_count", 0) == 0 and payload.get("pedestrian_count", 0) == 0
