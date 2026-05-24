"""
SMARTFLOW — Live Traffic Operations Monitor
Real-time intersection visualization, signal states, and live metrics.
Designed as the primary "what is happening right now" screen.
"""

from dash import html, dcc
from components.header import create_header
from components.sidebar import create_sidebar


def layout():
    return html.Div(
        className='app-layout',
        children=[
            create_header(),
            html.Div(
                className='app-body',
                children=[
                    create_sidebar(),
                    html.Main(
                        className='lt-main',
                        children=[
                            # ── Top KPI Row ────────────────────────────────
                            html.Div(
                                className='lt-kpi-row',
                                children=[
                                    html.Div(className='lt-kpi-card', children=[
                                        html.Div(className='lt-kpi-left', children=[
                                            html.I(className='fa-solid fa-car', style={'color': '#42a5f5'}),
                                        ]),
                                        html.Div(className='lt-kpi-body', children=[
                                            html.Span('Total Vehicles', className='lt-kpi-label'),
                                            html.Div(className='lt-kpi-value-row', children=[
                                                html.Span('187', id='lt-total-vehicles', className='lt-kpi-value'),
                                                html.Span(className='lt-kpi-trend up', children=[
                                                    html.I(className='fa-solid fa-arrow-up'),
                                                    '12%',
                                                ]),
                                            ]),
                                        ]),
                                    ]),
                                    html.Div(className='lt-kpi-card', children=[
                                        html.Div(className='lt-kpi-left', children=[
                                            html.I(className='fa-solid fa-hourglass-half', style={'color': '#00e676'}),
                                        ]),
                                        html.Div(className='lt-kpi-body', children=[
                                            html.Span('Avg Wait Time', className='lt-kpi-label'),
                                            html.Div(className='lt-kpi-value-row', children=[
                                                html.Span('12.4', id='lt-avg-wait', className='lt-kpi-value'),
                                                html.Span('s', className='lt-kpi-unit'),
                                                html.Span(className='lt-kpi-trend down', children=[
                                                    html.I(className='fa-solid fa-arrow-down'),
                                                    '18%',
                                                ]),
                                            ]),
                                        ]),
                                    ]),
                                    html.Div(className='lt-kpi-card', children=[
                                        html.Div(className='lt-kpi-left', children=[
                                            html.I(className='fa-solid fa-bars-staggered', style={'color': '#ab47bc'}),
                                        ]),
                                        html.Div(className='lt-kpi-body', children=[
                                            html.Span('Max Queue', className='lt-kpi-label'),
                                            html.Div(className='lt-kpi-value-row', children=[
                                                html.Span('14', id='lt-max-queue', className='lt-kpi-value'),
                                                html.Span('veh', className='lt-kpi-unit'),
                                                html.Span(className='lt-kpi-trend neutral', children=[
                                                    html.I(className='fa-solid fa-minus'),
                                                ]),
                                            ]),
                                        ]),
                                    ]),
                                    html.Div(className='lt-kpi-card', children=[
                                        html.Div(className='lt-kpi-left', children=[
                                            html.I(className='fa-solid fa-gauge-high', style={'color': '#ffa726'}),
                                        ]),
                                        html.Div(className='lt-kpi-body', children=[
                                            html.Span('Throughput', className='lt-kpi-label'),
                                            html.Div(className='lt-kpi-value-row', children=[
                                                html.Span('842', id='lt-throughput', className='lt-kpi-value'),
                                                html.Span('/h', className='lt-kpi-unit'),
                                                html.Span(className='lt-kpi-trend up', children=[
                                                    html.I(className='fa-solid fa-arrow-up'),
                                                    '24%',
                                                ]),
                                            ]),
                                        ]),
                                    ]),
                                    html.Div(className='lt-kpi-card emergency', children=[
                                        html.Div(className='lt-kpi-left', children=[
                                            html.I(className='fa-solid fa-truck-medical', style={'color': '#ef5350'}),
                                        ]),
                                        html.Div(className='lt-kpi-body', children=[
                                            html.Span('Emergency', className='lt-kpi-label'),
                                            html.Div(className='lt-kpi-value-row', children=[
                                                html.Span('1', id='lt-emergency', className='lt-kpi-value'),
                                                html.Span('active', className='lt-kpi-unit'),
                                                html.Span(className='lt-kpi-trend alert', children=[
                                                    html.I(className='fa-solid fa-bolt'),
                                                    'Priority',
                                                ]),
                                            ]),
                                        ]),
                                    ]),
                                ],
                            ),

                            # ── Main content: Viewport + Right Panel ─────────
                            html.Div(
                                className='lt-main-row',
                                children=[
                                    # ── Intersection Viewport ────────────────
                                    html.Div(
                                        className='lt-viewport-card',
                                        children=[
                                            html.Div(className='lt-viewport-header', children=[
                                                html.Div(className='lt-viewport-title', children=[
                                                    html.I(className='fa-solid fa-road'),
                                                    'Tagum City — Pioneer Ave & Apokon Rd',
                                                ]),
                                                html.Div(className='lt-viewport-badges', children=[
                                                    html.Span(className='lt-badge live', children=[
                                                        html.Span(className='lt-badge-dot'),
                                                        'LIVE',
                                                    ]),
                                                    html.Span(className='lt-badge phase', children=[
                                                        'Phase 2',
                                                    ]),
                                                ]),
                                            ]),
                                            html.Div(
                                                className='lt-intersection',
                                                children=[
                                                    # ── Intersection Visualization ──
                                                    html.Div(className='lt-intersection-bg'),

                                                    # Approach labels
                                                    html.Div(className='lt-approach-label lt-ap-n', children='N'),
                                                    html.Div(className='lt-approach-label lt-ap-s', children='S'),
                                                    html.Div(className='lt-approach-label lt-ap-e', children='E'),
                                                    html.Div(className='lt-approach-label lt-ap-w', children='W'),

                                                    # Queue bars (grow from approach toward center)
                                                    html.Div(className='lt-queue-bar lt-qb-n', id='lt-qb-n',
                                                             style={'height': '40%'}),
                                                    html.Div(className='lt-queue-bar lt-qb-s', id='lt-qb-s',
                                                             style={'height': '25%'}),
                                                    html.Div(className='lt-queue-bar lt-qb-e', id='lt-qb-e',
                                                             style={'height': '60%'}),
                                                    html.Div(className='lt-queue-bar lt-qb-w', id='lt-qb-w',
                                                             style={'height': '35%'}),

                                                    # Queue value labels
                                                    html.Div(className='lt-queue-label lt-ql-n', children='12'),
                                                    html.Div(className='lt-queue-label lt-ql-s', children='7'),
                                                    html.Div(className='lt-queue-label lt-ql-e', children='18'),
                                                    html.Div(className='lt-queue-label lt-ql-w', children='10'),

                                                    # Traffic lights per direction
                                                    html.Div(className='lt-traffic-light lt-tl-n', children=[
                                                        html.Span(className='lt-light red active'),
                                                        html.Span(className='lt-light yellow'),
                                                        html.Span(className='lt-light green'),
                                                    ]),
                                                    html.Div(className='lt-traffic-light lt-tl-s', children=[
                                                        html.Span(className='lt-light red active'),
                                                        html.Span(className='lt-light yellow'),
                                                        html.Span(className='lt-light green'),
                                                    ]),
                                                    html.Div(className='lt-traffic-light lt-tl-e', children=[
                                                        html.Span(className='lt-light red'),
                                                        html.Span(className='lt-light yellow'),
                                                        html.Span(className='lt-light green active'),
                                                    ]),
                                                    html.Div(className='lt-traffic-light lt-tl-w', children=[
                                                        html.Span(className='lt-light red'),
                                                        html.Span(className='lt-light yellow'),
                                                        html.Span(className='lt-light green active'),
                                                    ]),

                                                    # Center intersection
                                                    html.Div(className='lt-center', children=[
                                                        html.Div(className='lt-center-phase', children=[
                                                            html.Span('NS', className='lt-center-direction'),
                                                            html.Span('Green', className='lt-center-color green'),
                                                        ]),
                                                        html.Div(className='lt-center-timer', children=[
                                                            html.Span(id='lt-phase-countdown', className='lt-center-seconds', children='18'),
                                                            html.Span('s', className='lt-center-unit'),
                                                        ]),
                                                        html.Div(className='lt-center-bar', children=[
                                                            html.Div(className='lt-center-bar-fill', id='lt-phase-bar',
                                                                     style={'width': '60%'}),
                                                        ]),
                                                    ]),

                                                    # Vehicle dots on approaches
                                                    html.Div(className='lt-vehicles lt-veh-n'),
                                                    html.Div(className='lt-vehicles lt-veh-s'),
                                                    html.Div(className='lt-vehicles lt-veh-e'),
                                                    html.Div(className='lt-vehicles lt-veh-w'),

                                                    # Emergency overlay
                                                    html.Div(className='lt-emergency-overlay', id='lt-emergency-overlay',
                                                             children=[
                                                        html.I(className='fa-solid fa-truck-medical'),
                                                        html.Span('Emergency Vehicle Approaching — NS Corridor',
                                                                  className='lt-emergency-text'),
                                                    ]),
                                                ],
                                            ),
                                        ],
                                    ),

                                    # ── Right Status Panel ──────────────────
                                    html.Div(
                                        className='lt-right-panel',
                                        children=[
                                            # Live Signal States
                                            html.Div(className='lt-panel-card', children=[
                                                html.Div(className='lt-panel-card-header', children=[
                                                    html.I(className='fa-solid fa-traffic-light'),
                                                    'Signal States',
                                                ]),
                                                html.Div(className='lt-signal-list', children=[
                                                    html.Div(className='lt-signal-row active-red', children=[
                                                        html.Span('North-South', className='lt-signal-dir'),
                                                        html.Span(className='lt-signal-badge red', children=[
                                                            html.Span(className='lt-signal-dot'),
                                                            'Red',
                                                        ]),
                                                        html.Span('24s', className='lt-signal-time'),
                                                    ]),
                                                    html.Div(className='lt-signal-row active-green', children=[
                                                        html.Span('East-West', className='lt-signal-dir'),
                                                        html.Span(className='lt-signal-badge green', children=[
                                                            html.Span(className='lt-signal-dot'),
                                                            'Green',
                                                        ]),
                                                        html.Span('18s', className='lt-signal-time'),
                                                    ]),
                                                    html.Div(className='lt-signal-row', children=[
                                                        html.Span('Pedestrian', className='lt-signal-dir'),
                                                        html.Span(className='lt-signal-badge red', children=[
                                                            html.Span(className='lt-signal-dot'),
                                                            'Don\'t Walk',
                                                        ]),
                                                        html.Span('24s', className='lt-signal-time'),
                                                    ]),
                                                ]),
                                            ]),

                                            # Phase Timer
                                            html.Div(className='lt-panel-card', children=[
                                                html.Div(className='lt-panel-card-header', children=[
                                                    html.I(className='fa-solid fa-clock'),
                                                    'Phase Timer',
                                                ]),
                                                html.Div(className='lt-phase-display', children=[
                                                    html.Div(className='lt-phase-ring-wrap', children=[
                                                        html.Svg(
                                                            className='lt-phase-ring',
                                                            viewBox='0 0 100 100',
                                                            children=[
                                                                html.Circle(
                                                                    cx='50', cy='50', r='42',
                                                                    fill='none',
                                                                    stroke='rgba(255,255,255,0.05)',
                                                                    strokeWidth='6',
                                                                ),
                                                                html.Circle(
                                                                    id='lt-ring-progress',
                                                                    cx='50', cy='50', r='42',
                                                                    fill='none',
                                                                    stroke='#00e676',
                                                                    strokeWidth='6',
                                                                    strokeLinecap='round',
                                                                    strokeDasharray='263.89',
                                                                    strokeDashoffset='105.56',
                                                                    transform='rotate(-90 50 50)',
                                                                    style={'transition': 'stroke-dashoffset 1s linear'},
                                                                ),
                                                            ],
                                                        ),
                                                        html.Div(className='lt-phase-ring-text', children=[
                                                            html.Span('18', id='lt-ring-seconds',
                                                                      className='lt-phase-ring-seconds'),
                                                            html.Span('s', className='lt-phase-ring-unit'),
                                                        ]),
                                                    ]),
                                                    html.Div(className='lt-phase-info', children=[
                                                        html.Div(className='lt-phase-info-row', children=[
                                                            html.Span('Current', className='lt-phase-info-label'),
                                                            html.Span('Phase 2 — NS Green',
                                                                      className='lt-phase-info-value'),
                                                        ]),
                                                        html.Div(className='lt-phase-info-row', children=[
                                                            html.Span('Next', className='lt-phase-info-label'),
                                                            html.Span('Phase 3 — EW Yellow',
                                                                      className='lt-phase-info-value next'),
                                                        ]),
                                                        html.Div(className='lt-phase-info-row', children=[
                                                            html.Span('Cycle', className='lt-phase-info-label'),
                                                            html.Span('90s total', className='lt-phase-info-value'),
                                                        ]),
                                                    ]),
                                                ]),
                                            ]),

                                            # Direction Breakdown
                                            html.Div(className='lt-panel-card', children=[
                                                html.Div(className='lt-panel-card-header', children=[
                                                    html.I(className='fa-solid fa-chart-simple'),
                                                    'Direction Breakdown',
                                                ]),
                                                html.Div(className='lt-breakdown-list', children=[
                                                    html.Div(className='lt-breakdown-row', children=[
                                                        html.Span('N', className='lt-breakdown-dir'),
                                                        html.Div(className='lt-breakdown-bar-wrap', children=[
                                                            html.Div(className='lt-breakdown-bar',
                                                                     style={'width': '65%', 'background': '#42a5f5'}),
                                                        ]),
                                                        html.Span('12', className='lt-breakdown-val'),
                                                        html.Span('veh', className='lt-breakdown-unit'),
                                                    ]),
                                                    html.Div(className='lt-breakdown-row', children=[
                                                        html.Span('S', className='lt-breakdown-dir'),
                                                        html.Div(className='lt-breakdown-bar-wrap', children=[
                                                            html.Div(className='lt-breakdown-bar',
                                                                     style={'width': '40%', 'background': '#00e676'}),
                                                        ]),
                                                        html.Span('7', className='lt-breakdown-val'),
                                                        html.Span('veh', className='lt-breakdown-unit'),
                                                    ]),
                                                    html.Div(className='lt-breakdown-row', children=[
                                                        html.Span('E', className='lt-breakdown-dir'),
                                                        html.Div(className='lt-breakdown-bar-wrap', children=[
                                                            html.Div(className='lt-breakdown-bar',
                                                                     style={'width': '85%', 'background': '#ab47bc'}),
                                                        ]),
                                                        html.Span('18', className='lt-breakdown-val'),
                                                        html.Span('veh', className='lt-breakdown-unit'),
                                                    ]),
                                                    html.Div(className='lt-breakdown-row', children=[
                                                        html.Span('W', className='lt-breakdown-dir'),
                                                        html.Div(className='lt-breakdown-bar-wrap', children=[
                                                            html.Div(className='lt-breakdown-bar',
                                                                     style={'width': '50%', 'background': '#ffa726'}),
                                                        ]),
                                                        html.Span('10', className='lt-breakdown-val'),
                                                        html.Span('veh', className='lt-breakdown-unit'),
                                                    ]),
                                                ]),
                                            ]),

                                            # System Status
                                            html.Div(className='lt-panel-card', children=[
                                                html.Div(className='lt-panel-card-header', children=[
                                                    html.I(className='fa-solid fa-server'),
                                                    'System Status',
                                                ]),
                                                html.Div(className='lt-sys-status', children=[
                                                    html.Div(className='lt-sys-row', children=[
                                                        html.Span('Simulation', className='lt-sys-label'),
                                                        html.Span(className='lt-sys-indicator on'),
                                                        html.Span('Running', className='lt-sys-state'),
                                                    ]),
                                                    html.Div(className='lt-sys-row', children=[
                                                        html.Span('RL Agent', className='lt-sys-label'),
                                                        html.Span(className='lt-sys-indicator on'),
                                                        html.Span('Active', className='lt-sys-state'),
                                                    ]),
                                                    html.Div(className='lt-sys-row', children=[
                                                        html.Span('Data Feed', className='lt-sys-label'),
                                                        html.Span(className='lt-sys-indicator on'),
                                                        html.Span('Streaming', className='lt-sys-state'),
                                                    ]),
                                                    html.Div(className='lt-sys-row', children=[
                                                        html.Span('SUMO Conn', className='lt-sys-label'),
                                                        html.Span(className='lt-sys-indicator on'),
                                                        html.Span('Connected', className='lt-sys-state'),
                                                    ]),
                                                ]),
                                            ]),
                                        ],
                                    ),
                                ],
                            ),

                            # ── Bottom Section: Charts + Events ───────────
                            html.Div(
                                className='lt-bottom-row',
                                children=[
                                    # Queue Trend Chart
                                    html.Div(className='lt-chart-card', children=[
                                        html.Div(className='lt-chart-header', children=[
                                            html.Span(className='lt-chart-title', children=[
                                                html.I(className='fa-solid fa-chart-area'),
                                                ' Queue Length Trend',
                                            ]),
                                            html.Div(className='lt-chart-pills', children=[
                                                html.Button('5m', className='lt-pill active'),
                                                html.Button('15m', className='lt-pill'),
                                                html.Button('1h', className='lt-pill'),
                                            ]),
                                        ]),
                                        html.Div(className='lt-chart-body', children=[
                                            dcc.Graph(
                                                id='lt-queue-chart',
                                                config={'displayModeBar': False},
                                                style={'height': '100%', 'width': '100%'},
                                            ),
                                        ]),
                                    ]),

                                    # Wait Time Trend Chart
                                    html.Div(className='lt-chart-card', children=[
                                        html.Div(className='lt-chart-header', children=[
                                            html.Span(className='lt-chart-title', children=[
                                                html.I(className='fa-solid fa-chart-line'),
                                                ' Waiting Time Trend',
                                            ]),
                                            html.Div(className='lt-chart-pills', children=[
                                                html.Button('5m', className='lt-pill active'),
                                                html.Button('15m', className='lt-pill'),
                                                html.Button('1h', className='lt-pill'),
                                            ]),
                                        ]),
                                        html.Div(className='lt-chart-body', children=[
                                            dcc.Graph(
                                                id='lt-wait-chart',
                                                config={'displayModeBar': False},
                                                style={'height': '100%', 'width': '100%'},
                                            ),
                                        ]),
                                    ]),

                                    # Live Events Feed
                                    html.Div(className='lt-events-card', children=[
                                        html.Div(className='lt-chart-header', children=[
                                            html.Span(className='lt-chart-title', children=[
                                                html.I(className='fa-solid fa-bolt'),
                                                ' Live Events',
                                            ]),
                                            html.Span(id='lt-event-count', className='lt-event-counter', children='7'),
                                        ]),
                                        html.Div(className='lt-events-feed', id='lt-events-feed', children=[
                                            html.Div(className='lt-event-item priority', children=[
                                                html.Span('15:34:48', className='lt-event-time'),
                                                html.I(className='fa-solid fa-truck-medical lt-event-icon'),
                                                html.Span('Emergency vehicle — priority signal on NS corridor',
                                                          className='lt-event-text'),
                                            ]),
                                            html.Div(className='lt-event-item signal', children=[
                                                html.Span('15:34:30', className='lt-event-time'),
                                                html.I(className='fa-solid fa-traffic-light lt-event-icon'),
                                                html.Span('Signal phase: EW Red → NS Green (RL decision)',
                                                          className='lt-event-text'),
                                            ]),
                                            html.Div(className='lt-event-item warning', children=[
                                                html.Span('15:33:15', className='lt-event-time'),
                                                html.I(className='fa-solid fa-triangle-exclamation lt-event-icon'),
                                                html.Span('High congestion E-bound — queue 14 veh',
                                                          className='lt-event-text'),
                                            ]),
                                            html.Div(className='lt-event-item info', children=[
                                                html.Span('15:32:50', className='lt-event-time'),
                                                html.I(className='fa-solid fa-person-walking lt-event-icon'),
                                                html.Span('Pedestrian crossing activated — north crosswalk',
                                                          className='lt-event-text'),
                                            ]),
                                            html.Div(className='lt-event-item signal', children=[
                                                html.Span('15:32:02', className='lt-event-time'),
                                                html.I(className='fa-solid fa-traffic-light lt-event-icon'),
                                                html.Span('Signal phase: NS Red → EW Green (RL decision)',
                                                          className='lt-event-text'),
                                            ]),
                                            html.Div(className='lt-event-item info', children=[
                                                html.Span('15:31:40', className='lt-event-time'),
                                                html.I(className='fa-solid fa-chart-simple lt-event-icon'),
                                                html.Span('RL reward update: +12.4 (episode 1,247)',
                                                          className='lt-event-text'),
                                            ]),
                                            html.Div(className='lt-event-item warning', children=[
                                                html.Span('15:30:55', className='lt-event-time'),
                                                html.I(className='fa-solid fa-triangle-exclamation lt-event-icon'),
                                                html.Span('Queue threshold exceeded S-bound — adaptive timing',
                                                          className='lt-event-text'),
                                            ]),
                                        ]),
                                    ]),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Interval(id='lt-update-interval', interval=1000, n_intervals=0),
        ],
    )