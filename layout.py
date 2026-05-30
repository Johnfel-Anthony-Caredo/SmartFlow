"""
layout.py — SmartFlow Traffic Dashboard Layout Components
==========================================================
Contains all Dash layout component functions for the SmartFlow Traffic
AI-driven traffic simulation control center. Every function returns a
Dash component tree that mirrors the static HTML reference (index.html)
while using proper Dash-native widgets (dcc.Dropdown, dcc.Graph, etc.).

IMPORTANT: This file uses ONLY `dash.html` and `dash.dcc`.
           No dash-bootstrap-components.
"""

from datetime import datetime, timedelta

import plotly.graph_objects as go
from dash import dcc, html


# ═══════════════════════════════════════════════════════════════════════
# CHART HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def _common_layout_settings() -> dict:
    """Return the shared Plotly layout dict used by every chart."""
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#64748b', size=10),
        margin=dict(l=35, r=10, t=30, b=30),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='center', x=0.5, font=dict(size=10),
        ),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.03)',
            tickfont=dict(size=9), showline=False,
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.03)',
            tickfont=dict(size=9), showline=False,
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(10,15,26,0.95)',
            bordercolor='rgba(255,255,255,0.08)',
            font=dict(family='Inter', size=11, color='#94a3b8'),
        ),
    )


def _generate_time_labels(n: int = 30) -> list[str]:
    """Generate *n* realistic time labels for the last 5 minutes at
    10-second intervals, formatted as HH:MM:SS."""
    now = datetime.now()
    return [
        (now - timedelta(seconds=(n - 1 - i) * 10)).strftime('%H:%M:%S')
        for i in range(n)
    ]


def create_traffic_flow_figure() -> go.Figure:
    """Return a Plotly Figure for the Traffic Flow area chart.

    Four direction traces (NB / SB / EB / WB) with fill='tozeroy'.
    """
    import random
    random.seed(42)  # reproducible demo data

    labels = _generate_time_labels(30)

    # Realistic-ish vehicle-per-interval counts for each direction
    nb = [random.randint(18, 35) for _ in range(30)]
    sb = [random.randint(14, 28) for _ in range(30)]
    eb = [random.randint(10, 22) for _ in range(30)]
    wb = [random.randint(8, 18) for _ in range(30)]

    traces = [
        go.Scatter(
            x=labels, y=nb, name='NB', mode='lines',
            fill='tozeroy',
            line=dict(color='#00e676', width=2),
            fillcolor='rgba(0,230,118,0.15)',
        ),
        go.Scatter(
            x=labels, y=sb, name='SB', mode='lines',
            fill='tozeroy',
            line=dict(color='#42a5f5', width=2),
            fillcolor='rgba(66,165,245,0.15)',
        ),
        go.Scatter(
            x=labels, y=eb, name='EB', mode='lines',
            fill='tozeroy',
            line=dict(color='#ab47bc', width=2),
            fillcolor='rgba(171,71,188,0.15)',
        ),
        go.Scatter(
            x=labels, y=wb, name='WB', mode='lines',
            fill='tozeroy',
            line=dict(color='#ffa726', width=2),
            fillcolor='rgba(255,167,38,0.15)',
        ),
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(**_common_layout_settings())
    return fig


def create_wait_time_figure() -> go.Figure:
    """Return a Plotly Figure for the Average Waiting Time chart.

    Two traces: RL-Optimized (green, filled) vs Fixed Timing Baseline
    (red dashed).
    """
    import random
    random.seed(99)

    labels = _generate_time_labels(30)

    # RL-optimized waiting times trend downwards
    rl = [round(random.uniform(10, 16), 1) for _ in range(30)]
    # Fixed-timing baseline stays elevated
    baseline = [round(random.uniform(18, 28), 1) for _ in range(30)]

    traces = [
        go.Scatter(
            x=labels, y=rl, name='RL-Optimized', mode='lines',
            fill='tozeroy',
            line=dict(color='#00e676', width=2),
            fillcolor='rgba(0,230,118,0.12)',
        ),
        go.Scatter(
            x=labels, y=baseline, name='Fixed Timing Baseline',
            mode='lines',
            line=dict(color='#ef5350', width=2, dash='dash'),
        ),
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(**_common_layout_settings())
    return fig


# ═══════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════

def create_header() -> html.Header:
    """Top header bar with logo, scenario selector, sim status, and
    date/time/notification area."""
    return html.Header(
        id='top-header',
        className='top-header',
        children=[
            # ── Left: logo ──────────────────────────────────────────
            html.Div(className='header-left', children=[
                html.Div(className='logo-group', children=[
                    html.Div(className='logo-icon', children=[
                        html.Img(
                            src='/assets/logo.svg',
                            style={'width': '28px', 'height': '28px'},
                        ),
                    ]),
                    html.Div(className='logo-text', children=[
                        html.Span('SmartFlow', className='logo-name'),
                        html.Span('TRAFFIC', className='logo-sub'),
                    ]),
                ]),
            ]),

            # ── Center: scenario selector + sim status ──────────────
            html.Div(className='header-center', children=[
                html.Div(className='scenario-selector', children=[
                    html.Label('Scenario', className='scenario-label'),
                    dcc.Dropdown(
                        id='scenario-dropdown',
                        options=[
                            {'label': 'Tagum City — Main Intersection',
                             'value': 'tagum-main'},
                            {'label': 'Tagum City — Secondary Route',
                             'value': 'tagum-secondary'},
                            {'label': 'Custom Scenario',
                             'value': 'custom'},
                        ],
                        value='tagum-main',
                        clearable=False,
                        searchable=False,
                        className='dash-dropdown scenario-dropdown-wrap',
                    ),
                ]),
                html.Div(className='header-divider'),
                html.Div(className='sim-status-group', children=[
                    html.Div(className='sim-timer', children=[
                        html.I(className='fa-solid fa-clock'),
                        html.Span('00:14:32', id='sim-timer',
                                  className='timer-value'),
                    ]),
                    html.Div(
                        id='sim-status-badge',
                        className='status-badge running',
                        children=[
                            html.Span(className='status-dot'),
                            'Running',
                        ],
                    ),
                ]),
            ]),

            # ── Right: date/time + action buttons ───────────────────
            html.Div(className='header-right', children=[
                html.Div(className='datetime-display', children=[
                    html.Span(id='current-date', className='date-text'),
                    html.Span(id='current-time', className='time-text'),
                ]),
                html.Div(className='header-divider'),
                html.Button(
                    id='notifications-btn',
                    className='icon-btn',
                    title='Notifications',
                    children=[
                        html.I(className='fa-solid fa-bell'),
                        html.Span(className='notif-dot'),
                    ],
                ),
                html.Button(
                    id='settings-btn',
                    className='icon-btn',
                    title='Settings',
                    children=[
                        html.I(className='fa-solid fa-gear'),
                    ],
                ),
            ]),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════

def create_sidebar() -> html.Aside:
    """Left sidebar with navigation links and a system-status panel."""

    # Navigation items: (id, icon_class, label, is_active)
    nav_items = [
        ('nav-dashboard',   'fa-solid fa-grid-2',          'Dashboard',            True),
        ('nav-simulation',  'fa-solid fa-play-circle',     'Simulation Control',   False),
        ('nav-scenarios',   'fa-solid fa-map',             'Scenarios',            False),
        ('nav-traffic',     'fa-solid fa-car',             'Traffic Overview',     False),
        ('nav-metrics',     'fa-solid fa-chart-line',      'Performance Metrics',  False),
        ('nav-agent',       'fa-solid fa-brain',           'AI Agent (RL)',        False),
        ('nav-reports',     'fa-solid fa-file-lines',      'Reports',              False),
    ]

    bottom_items = [
        ('nav-settings', 'fa-solid fa-sliders',         'Settings', False),
        ('nav-help',     'fa-solid fa-circle-question',  'Help',     False),
    ]

    # Build nav links
    links: list = []
    for item_id, icon, label, active in nav_items:
        links.append(
            html.A(
                id=item_id,
                href='#',
                className='nav-item active' if active else 'nav-item',
                children=[
                    html.I(className=icon),
                    html.Span(label),
                ],
            )
        )

    # Spacer + bottom items
    links.append(html.Div(className='nav-spacer'))
    for item_id, icon, label, _ in bottom_items:
        links.append(
            html.A(
                id=item_id,
                href='#',
                className='nav-item',
                children=[
                    html.I(className=icon),
                    html.Span(label),
                ],
            )
        )

    # System status panel
    status_items_data = [
        ('SUMO Connection', 'Connected'),
        ('RL Agent',        'Active'),
        ('Visualization',   'Streaming'),
        ('Data Logging',    'Recording'),
    ]

    status_items = [
        html.Li(className='status-item', children=[
            html.Span(className='status-indicator active'),
            html.Span(name, className='status-name'),
            html.Span(value, className='status-value active'),
        ])
        for name, value in status_items_data
    ]

    return html.Aside(
        id='left-sidebar',
        className='sidebar',
        children=[
            html.Nav(className='sidebar-nav', children=links),
            html.Div(className='system-status-panel', children=[
                html.H4(className='panel-title', children=[
                    html.I(className='fa-solid fa-server'),
                    ' System Status',
                ]),
                html.Ul(className='status-list', children=status_items),
            ]),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════
# SIMULATION VIEW
# ═══════════════════════════════════════════════════════════════════════

def create_simulation_view() -> html.Div:
    """Large simulation card with viewport, overlays, and stat chips."""
    return html.Div(
        id='simulation-view',
        className='card simulation-card',
        children=[
            # ── Header row ──────────────────────────────────────────
            html.Div(className='sim-header', children=[
                html.Div(className='sim-title-group', children=[
                    html.H2(className='card-title', children=[
                        html.I(className='fa-solid fa-video'),
                        ' Live Simulation View',
                    ]),
                    html.Span(className='live-indicator', children=[
                        html.Span(className='live-dot'),
                        ' LIVE',
                    ]),
                ]),
            ]),

            # ── Viewport ────────────────────────────────────────────
            html.Div(id='sim-viewport', className='sim-viewport', children=[
                html.Div(
                    id='three-container',
                    className='three-container',
                    style={'display': 'block'},
                    children=[
                        html.Div(
                            id='three-loading-msg',
                            style={
                                'position': 'absolute', 'inset': '0',
                                'display': 'flex', 'alignItems': 'center',
                                'justifyContent': 'center',
                                'color': 'var(--text-muted)', 'fontSize': '13px',
                                'zIndex': '1',
                            },
                            children=[
                                html.I(className='fa-solid fa-spinner fa-spin', style={'marginRight': '8px'}),
                                '3D Scene loading — waiting for engine state...',
                            ],
                        ),
                    ],
                ),
                html.Div(id='simulation-overlays', className='simulation-overlays', children=[
                    html.Div(className='sim-overlay overlay-top-left', children=[
                        html.Div('Intersection', className='overlay-label'),
                        html.Div('Tagum City — Pioneer Ave & Apokon Rd',
                                 className='overlay-value'),
                    ]),
                    html.Div(className='sim-overlay overlay-bottom-left', children=[
                        html.Div('Signal Phase', className='overlay-label'),
                        html.Div(className='overlay-value phase-green', id='sim-phase-display', children=[
                            html.I(className='fa-solid fa-traffic-light'),
                            ' Phase 1 — NS Green',
                        ]),
                    ]),
                    html.Div(
                        id='phase-timer',
                        className='sim-overlay overlay-bottom-right',
                        children=[
                            html.Div('Phase Timer', className='overlay-label'),
                            html.Div(
                                className='overlay-value timer-countdown',
                                children=[
                                    html.Span(
                                        '18',
                                        id='phase-timer-seconds',
                                        className='phase-seconds',
                                    ),
                                    html.Span('s', className='phase-unit'),
                                ],
                            ),
                        ],
                    ),
                    html.Div(className='sim-overlay overlay-stats', children=[
                        html.Span(className='stat-chip', children=[
                            html.I(className='fa-solid fa-car'),
                            html.Span(' 0 vehicles', id='stat-vehicles'),
                        ]),
                        html.Span(className='stat-chip', children=[
                            html.I(className='fa-solid fa-person-walking'),
                            html.Span(' 0 peds', id='stat-pedestrians'),
                        ]),
                        html.Span(className='stat-chip emergency', children=[
                            html.I(className='fa-solid fa-truck-medical'),
                            html.Span(' 0 EV', id='stat-emergency'),
                        ]),
                    ]),
                ]),
            ]),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════
# CONTROL PANEL (right panel)
# ═══════════════════════════════════════════════════════════════════════

def create_control_panel() -> html.Div:
    """Right-hand panel with simulation controls and scenario settings."""

    # ── Simulation Controls card ────────────────────────────────────
    sim_controls = html.Div(
        id='sim-controls',
        className='card control-card',
        children=[
            html.H3(className='card-title compact', children=[
                html.I(className='fa-solid fa-gamepad'),
                ' Simulation Controls',
            ]),
            html.Div(className='control-buttons', children=[
                html.Button(
                    id='btn-start', className='ctrl-btn start',
                    title='Start Simulation',
                    children=[html.I(className='fa-solid fa-play'),
                              html.Span('Start Simulation')],
                ),
                html.Button(
                    id='btn-pause', className='ctrl-btn pause',
                    title='Pause Simulation',
                    children=[html.I(className='fa-solid fa-pause'),
                              html.Span('Pause')],
                ),
                html.Button(
                    id='btn-stop', className='ctrl-btn stop',
                    title='Stop Simulation',
                    children=[html.I(className='fa-solid fa-stop'),
                              html.Span('Stop Simulation')],
                ),
                html.Button(
                    id='btn-reset', className='ctrl-btn reset',
                    title='Reset Simulation',
                    children=[html.I(className='fa-solid fa-rotate-right'),
                              html.Span('Reset Simulation')],
                ),
            ]),
        ],
    )

    # ── Scenario Settings card ──────────────────────────────────────
    scenario_settings = html.Div(
        id='scenario-settings',
        className='card settings-card',
        children=[
            html.H3(className='card-title compact', children=[
                html.I(className='fa-solid fa-sliders'),
                ' Scenario Settings',
            ]),
            # Traffic Density
            html.Div(className='setting-group', children=[
                html.Label('Traffic Density', className='setting-label'),
                dcc.Dropdown(
                    id='traffic-density-dropdown',
                    options=[
                        {'label': 'Low',       'value': 'Low'},
                        {'label': 'Medium',    'value': 'Medium'},
                        {'label': 'High',      'value': 'High'},
                        {'label': 'Very High', 'value': 'Very High'},
                    ],
                    value='High',
                    clearable=False,
                    searchable=False,
                    className='dash-dropdown dropdown-small setting-dropdown',
                ),
            ]),
            # Pedestrian Density
            html.Div(className='setting-group', children=[
                html.Label('Pedestrian Density', className='setting-label'),
                dcc.Dropdown(
                    id='pedestrian-density-dropdown',
                    options=[
                        {'label': 'None',   'value': 'None'},
                        {'label': 'Low',    'value': 'Low'},
                        {'label': 'Medium', 'value': 'Medium'},
                        {'label': 'High',   'value': 'High'},
                    ],
                    value='Medium',
                    clearable=False,
                    searchable=False,
                    className='dash-dropdown dropdown-small setting-dropdown',
                ),
            ]),
            # Emergency Vehicle
            html.Div(className='setting-group', children=[
                html.Label('Emergency Vehicle', className='setting-label'),
                dcc.Dropdown(
                    id='emergency-vehicle-dropdown',
                    options=[
                        {'label': 'Disabled',
                         'value': 'Disabled'},
                        {'label': 'Enabled (1 Ambulance)',
                         'value': 'Enabled (1 Ambulance)'},
                        {'label': 'Enabled (2 Vehicles)',
                         'value': 'Enabled (2 Vehicles)'},
                    ],
                    value='Enabled (1 Ambulance)',
                    clearable=False,
                    searchable=False,
                    className='dash-dropdown dropdown-small setting-dropdown',
                ),
            ]),
            # Road Constraint
            html.Div(className='setting-group', children=[
                html.Label('Road Constraint', className='setting-label'),
                dcc.Dropdown(
                    id='road-constraint-dropdown',
                    options=[
                        {'label': 'None', 'value': 'None'},
                        {'label': 'Weight Limit', 'value': 'Weight Limit'},
                        {'label': 'Height Restriction', 'value': 'Height Restriction'},
                        {'label': 'One-Way', 'value': 'One-Way'},
                        {'label': 'Narrow Road', 'value': 'Narrow Road'},
                        {'label': 'School Zone', 'value': 'School Zone'},
                        {'label': 'No Overtaking', 'value': 'No Overtaking'},
                        {'label': 'Speed Bump', 'value': 'Speed Bump'},
                    ],
                    value='None',
                    clearable=False,
                    searchable=False,
                    className='dash-dropdown dropdown-small setting-dropdown',
                ),
            ]),
            # Apply button
            html.Button(
                id='btn-apply-scenario',
                className='apply-btn',
                children=[
                    html.I(className='fa-solid fa-check'),
                    ' Apply Scenario',
                ],
            ),
        ],
    )

    return html.Div(
        className='control-panel-wrapper',
        children=[sim_controls, scenario_settings]
    )


# ═══════════════════════════════════════════════════════════════════════
# KPI METRICS ROW
# ═══════════════════════════════════════════════════════════════════════

def create_kpi_row() -> html.Div:
    """Five KPI metric cards displayed in a horizontal grid."""

    kpis = [
        {
            'id': 'kpi-wait-time',
            'value_id': 'kpi-wait-time-value',
            'color': '#00e676',
            'icon': 'fa-solid fa-hourglass-half',
            'label': 'Avg. Waiting Time',
            'value': '0.0',
            'unit': 's',
            'change_class': 'kpi-change',
            'change_icon': '',
            'change_text': '',
        },
        {
            'id': 'kpi-queue-length',
            'value_id': 'kpi-queue-length-value',
            'color': '#42a5f5',
            'icon': 'fa-solid fa-bars-staggered',
            'label': 'Avg. Queue Length',
            'value': '0.0',
            'unit': 'veh',
            'change_class': 'kpi-change',
            'change_icon': '',
            'change_text': '',
        },
        {
            'id': 'kpi-throughput',
            'value_id': 'kpi-throughput-value',
            'color': '#ab47bc',
            'icon': 'fa-solid fa-gauge-high',
            'label': 'Throughput',
            'value': '0',
            'unit': 'veh/h',
            'change_class': 'kpi-change',
            'change_icon': '',
            'change_text': '',
        },
        {
            'id': 'kpi-pedestrians',
            'value_id': 'kpi-pedestrians-value',
            'color': '#ffa726',
            'icon': 'fa-solid fa-person-walking',
            'label': 'Pedestrians Crossed',
            'value': '0',
            'unit': None,
            'change_class': 'kpi-change',
            'change_icon': '',
            'change_text': '',
        },
        {
            'id': 'kpi-emergency',
            'value_id': 'kpi-emergency-value',
            'color': '#ef5350',
            'icon': 'fa-solid fa-truck-medical',
            'label': 'Emergency Vehicles',
            'value': '0',
            'unit': 'active',
            'change_class': 'kpi-change',
            'change_icon': '',
            'change_text': '',
        },
    ]

    cards: list = []
    for kpi in kpis:
        # Build value children (number + optional unit span)
        value_children: list = [
            html.Span(kpi['value'], id=kpi.get('value_id'), className='kpi-number')
        ]
        if kpi['unit']:
            value_children.append(
                html.Span(kpi['unit'], className='kpi-unit')
            )

        cards.append(
            html.Div(
                id=kpi['id'],
                className='kpi-card',
                children=[
                    html.Div(
                        className='kpi-icon-wrap',
                        style={'--kpi-color': kpi['color']},
                        children=[html.I(className=kpi['icon'])],
                    ),
                    html.Div(className='kpi-content', children=[
                        html.Span(kpi['label'], className='kpi-label'),
                        html.Span(className='kpi-value',
                                  children=value_children),
                        html.Span(
                            className=kpi['change_class'],
                            id=f"{kpi['id']}-change",
                            children=[
                                html.I(className=kpi['change_icon']),
                                kpi['change_text'],
                            ],
                        ),
                    ]),
                ],
            )
        )

    return html.Div(id='kpi-metrics', className='kpi-row', children=cards)


# ═══════════════════════════════════════════════════════════════════════
# ANALYTICS SECTION
# ═══════════════════════════════════════════════════════════════════════

def _time_range_pills() -> html.Div:
    """Reusable 5m / 15m / 1h pill button group."""
    return html.Div(className='time-range-pills', children=[
        html.Button('5m', className='pill active'),
        html.Button('15m', className='pill'),
        html.Button('1h', className='pill'),
    ])


def create_analytics_section() -> html.Div:
    """Bottom analytics row: Traffic Flow chart, Wait Time chart,
    RL Agent Status, and Recent Events feed."""

    # ── 1. Traffic Flow chart ───────────────────────────────────────
    traffic_flow_card = html.Div(
        id='traffic-flow-card',
        className='card analytics-card',
        children=[
            html.Div(className='analytics-header', children=[
                html.H3(className='card-title compact', children=[
                    html.I(className='fa-solid fa-chart-area'),
                    ' Traffic Flow',
                ]),
                _time_range_pills(),
            ]),
            html.Div(className='chart-container', children=[
                dcc.Graph(
                    id='traffic-flow-chart',
                    figure=create_traffic_flow_figure(),
                    config={'displayModeBar': False},
                    style={'height': '100%', 'width': '100%'},
                ),
            ]),
        ],
    )

    # ── 2. Average Waiting Time chart ───────────────────────────────
    wait_time_card = html.Div(
        id='wait-time-card',
        className='card analytics-card',
        children=[
            html.Div(className='analytics-header', children=[
                html.H3(className='card-title compact', children=[
                    html.I(className='fa-solid fa-chart-line'),
                    ' Avg. Waiting Time',
                ]),
                _time_range_pills(),
            ]),
            html.Div(className='chart-container', children=[
                dcc.Graph(
                    id='wait-time-chart',
                    figure=create_wait_time_figure(),
                    config={'displayModeBar': False},
                    style={'height': '100%', 'width': '100%'},
                ),
            ]),
        ],
    )

    # ── 3. RL Agent Status ──────────────────────────────────────────
    rl_card = html.Div(
        id='rl-agent-card',
        className='card analytics-card rl-card',
        children=[
            html.Div(className='analytics-header', children=[
                html.H3(className='card-title compact', children=[
                    html.I(className='fa-solid fa-brain'),
                    ' RL Agent Status',
                ]),
                html.Span(className='agent-badge active', children=[
                    html.I(className='fa-solid fa-circle'),
                    ' Learning',
                ]),
            ]),
            html.Div(className='rl-stats', children=[
                # Learning Progress bar
                html.Div(className='rl-stat-item', children=[
                    html.Span('Learning Progress',
                              className='rl-stat-label'),
                    html.Div(className='progress-bar-wrap', children=[
                        html.Div(className='progress-bar',
                                 style={'width': '68%'}),
                    ]),
                    html.Span('68%', className='rl-stat-value'),
                ]),
                # Epsilon bar
                html.Div(className='rl-stat-item', children=[
                    html.Span('Epsilon (Exploration)',
                              className='rl-stat-label'),
                    html.Div(className='progress-bar-wrap epsilon',
                             children=[
                                 html.Div(className='progress-bar',
                                          style={'width': '22%'}),
                             ]),
                    html.Span('0.22', className='rl-stat-value'),
                ]),
                # Metric boxes — row 1
                html.Div(className='rl-stat-row', children=[
                    html.Div(className='rl-metric', children=[
                        html.Span('Total Episodes',
                                  className='rl-metric-label'),
                        html.Span('1,247',
                                  className='rl-metric-value'),
                    ]),
                    html.Div(className='rl-metric', children=[
                        html.Span('Total Reward',
                                  className='rl-metric-label'),
                        html.Span('+3,842',
                                  className='rl-metric-value positive'),
                    ]),
                ]),
                # Metric boxes — row 2
                html.Div(className='rl-stat-row', children=[
                    html.Div(className='rl-metric', children=[
                        html.Span('Algorithm',
                                  className='rl-metric-label'),
                        html.Span('DQN',
                                  className='rl-metric-value mono'),
                    ]),
                    html.Div(className='rl-metric', children=[
                        html.Span('Learning Rate',
                                  className='rl-metric-label'),
                        html.Span('0.001',
                                  className='rl-metric-value mono'),
                    ]),
                ]),
            ]),
        ],
    )

    # ── 4. Recent Events feed ───────────────────────────────────────
    events_data = [
        ('priority', '15:34:48', 'fa-solid fa-truck-medical',
         'Emergency vehicle detected — priority signal activated on NS corridor'),
        ('signal',   '15:34:30', 'fa-solid fa-traffic-light',
         'Signal phase changed: EW Red → NS Green (RL decision)'),
        ('warning',  '15:33:15', 'fa-solid fa-triangle-exclamation',
         'High congestion detected on eastbound approach — queue length 14 veh'),
        ('info',     '15:32:50', 'fa-solid fa-person-walking',
         'Pedestrian crossing activated — north crosswalk (8 pedestrians queued)'),
        ('signal',   '15:32:02', 'fa-solid fa-traffic-light',
         'Signal phase changed: NS Red → EW Green (RL decision)'),
        ('info',     '15:31:40', 'fa-solid fa-chart-simple',
         'RL agent reward update: +12.4 (episode 1,247 completed)'),
        ('warning',  '15:30:55', 'fa-solid fa-triangle-exclamation',
         'Queue threshold exceeded on southbound lane — adaptive timing applied'),
    ]

    event_items = [
        html.Div(className=f'event-item {evt_class}', children=[
            html.Span(time, className='event-time'),
            html.Span(className='event-icon', children=[
                html.I(className=icon),
            ]),
            html.Span(text, className='event-text'),
        ])
        for evt_class, time, icon, text in events_data
    ]

    events_card = html.Div(
        id='recent-events-card',
        className='card analytics-card events-card',
        children=[
            html.Div(className='analytics-header', children=[
                html.H3(className='card-title compact', children=[
                    html.I(className='fa-solid fa-stream'),
                    ' Recent Events',
                ]),
                html.Button('Clear', id='btn-clear-events',
                            className='clear-btn'),
            ]),
            html.Div(
                id='events-feed',
                className='events-feed',
                children=event_items,
            ),
        ],
    )

    return html.Div(
        id='analytics-section',
        className='analytics-row',
        children=[
            traffic_flow_card,
            wait_time_card,
            rl_card,
            events_card,
        ],
    )


# ═══════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════

def create_footer() -> html.Footer:
    """Dashboard footer with product info and build version."""
    return html.Footer(
        id='dashboard-footer',
        className='dashboard-footer',
        children=[
            html.Span(
                ('SmartFlow Traffic v1.0 — Designed for research and '
                 'academic use. Powered by SUMO · TraCI · '
                 'Reinforcement Learning'),
                className='footer-text',
            ),
            html.Span(className='footer-right', children=[
                html.Span('Build 2026.05.22',
                          className='footer-version'),
            ]),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════
# MAIN LAYOUT ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════

def create_layout() -> html.Div:
    """Assemble the complete SmartFlow Traffic dashboard layout.

    Includes dcc.Interval timers, dcc.Store for simulation state,
    the header, sidebar, main content area (simulation view, control
    panel, KPI row, analytics section), and footer.
    """
    return html.Div([
        # ── Hidden state / interval components ──────────────────────
        dcc.Interval(id='clock-interval', interval=1000, n_intervals=0),
        dcc.Interval(id='sim-interval', interval=1000, n_intervals=0),
        dcc.Store(
            id='sim-state',
            data={
                'status': 'running',
                'elapsed_seconds': 872,
                'phase_seconds': 18,
            },
        ),

        # ── Header ──────────────────────────────────────────────────
        create_header(),

        # ── Body: sidebar + main content ────────────────────────────
        html.Div(className='app-layout', children=[
            create_sidebar(),
            html.Main(className='main-content', children=[
                # Top row: simulation view + right control panel
                html.Div(className='top-row', children=[
                    create_simulation_view(),
                    html.Div(className='right-panel', children=[
                        create_control_panel(),
                    ]),
                ]),
                # KPI metrics
                create_kpi_row(),
                # Analytics charts + events
                create_analytics_section(),
                # Footer
                create_footer(),
            ]),
        ]),
    ])
