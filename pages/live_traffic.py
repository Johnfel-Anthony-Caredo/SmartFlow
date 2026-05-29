"""SMARTFLOW live traffic page with SUMO-backed 2D map rendering."""

from dash import dcc, html

from components.header import create_header
from components.sidebar import create_sidebar
from components.traffic_map import build_traffic_map, build_traffic_map_legend


def _metric_card(label: str, value_id: str, value: str, icon: str, tone: str):
    return html.Div(className=f"lt-live-metric {tone}", children=[
        html.Div(className="lt-live-metric-icon", children=[html.I(className=icon)]),
        html.Div(className="lt-live-metric-body", children=[
            html.Span(label, className="lt-live-metric-label"),
            html.Strong(value, id=value_id, className="lt-live-metric-value"),
        ]),
    ])


def _panel(title: str, icon: str, children, class_name: str = ""):
    return html.Section(className=f"lt-live-panel {class_name}".strip(), children=[
        html.Div(className="lt-live-panel-header", children=[
            html.I(className=icon),
            html.Span(title),
        ]),
        html.Div(className="lt-live-panel-body", children=children),
    ])


def _empty_chart(graph_id: str):
    return dcc.Graph(
        id=graph_id,
        figure={},
        config={"displayModeBar": False},
        style={"height": "100%", "width": "100%"},
    )


def layout():
    return html.Div(className="app-layout", children=[
        create_header(),
        html.Div(className="app-body", children=[
            create_sidebar(),
            html.Main(className="main-content lt-live-page", children=[
                html.Div(className="lt-live-header", children=[
                    html.Div(children=[
                        html.Div(className="lt-live-eyebrow", children="SUMO live operator map"),
                        html.H1("Live Traffic"),
                    ]),
                    html.Div(className="lt-live-status", children=[
                        html.Span(id="lt-runtime-status", className="status-badge stopped", children=[
                            html.Span(className="status-dot"),
                            " Stopped",
                        ]),
                        html.Span(id="lt-runtime-time", className="lt-live-time", children="00:00:00"),
                    ]),
                ]),

                html.Div(className="lt-live-grid", children=[
                    html.Section(className="lt-live-map-section", children=[
                        html.Div(className="lt-live-map-shell", children=[
                            html.Div(className="lt-live-map-header", children=[
                                html.Div(className="lt-live-map-meta", children=[
                                    html.Span("2D SUMO Network", className="lt-live-map-title"),
                                    html.Span("Focused intersection geometry and live entities from TraCI state", className="lt-live-map-subtitle"),
                                    html.Div(className="lt-live-map-phase", children=[
                                        html.Span("Current phase", className="lt-live-map-phase-label"),
                                        html.Strong(id="lt-phase-name", children="NS GREEN"),
                                        html.Span(id="lt-phase-remaining", children="0s"),
                                    ]),
                                ]),
                                html.Div(className="lt-live-legend", children=build_traffic_map_legend()),
                            ]),
                            html.Div(
                                id="lt-map-container",
                                className="lt-map-container",
                                children=build_traffic_map(),
                            ),
                        ]),
                    ]),

                    html.Aside(className="lt-live-side", children=[
                        _panel("Signal State", "fa-solid fa-traffic-light", [
                            html.Div(id="lt-signal-state-list", className="lt-signal-state-list", children=[
                                html.Div(className="lt-signal-state-row", children=[
                                    html.Span("NS approaches"),
                                    html.Strong("Red", className="signal-red"),
                                ]),
                                html.Div(className="lt-signal-state-row", children=[
                                    html.Span("EW approaches"),
                                    html.Strong("Red", className="signal-red"),
                                ]),
                            ]),
                        ]),
                        _panel("Scenario Overlay", "fa-solid fa-triangle-exclamation", [
                            html.Div(id="lt-scenario-overlay", className="lt-scenario-overlay", children="No active disruption"),
                        ]),
                        _panel("Recent Events", "fa-solid fa-stream", [
                            html.Div(id="lt-event-feed", className="lt-events-feed", children=[
                                html.Div(className="lt-event-item info", children=[
                                    html.Span("--:--", className="lt-event-time"),
                                    html.Span(className="lt-event-icon", children=[html.I(className="fa-solid fa-circle-info")]),
                                    html.Span("No live events yet", className="lt-event-text"),
                                ]),
                            ]),
                        ], class_name="events"),
                    ]),
                ]),

                html.Div(className="lt-live-metrics", children=[
                    _metric_card("Vehicles", "lt-vehicle-count", "0", "fa-solid fa-car", "vehicles"),
                    _metric_card("Pedestrians", "lt-pedestrian-count", "0", "fa-solid fa-person-walking", "pedestrians"),
                    _metric_card("Total Queue", "lt-queue-count", "0", "fa-solid fa-bars-staggered", "queue"),
                    _metric_card("Avg Wait", "lt-wait-time", "0.0s", "fa-solid fa-hourglass-half", "wait"),
                    _metric_card("Emergency", "lt-emergency-count", "0", "fa-solid fa-truck-medical", "emergency"),
                ]),

                html.Div(className="lt-live-chart-row", children=[
                    html.Section(className="lt-live-chart-panel", children=[
                        html.Div(className="lt-live-panel-header", children=[
                            html.I(className="fa-solid fa-chart-area"),
                            html.Span("Queue Pressure"),
                        ]),
                        html.Div(className="lt-live-chart-body", children=[
                            _empty_chart("lt-traffic-flow-chart"),
                        ]),
                    ]),
                    html.Section(className="lt-live-chart-panel", children=[
                        html.Div(className="lt-live-panel-header", children=[
                            html.I(className="fa-solid fa-chart-line"),
                            html.Span("Wait vs Queue"),
                        ]),
                        html.Div(className="lt-live-chart-body", children=[
                            _empty_chart("lt-wait-time-chart"),
                        ]),
                    ]),
                ]),
            ]),
        ]),
    ])
