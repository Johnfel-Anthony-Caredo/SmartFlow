"""
SMARTFLOW — Simulation Control Page
Two-column control-room view with run overview, logs, and controls.
"""

from dash import html
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
                        className='main-content',
                        children=[
                            html.Div(
                                className='page-header',
                                children=[
                                    html.H1('Simulation Control'),
                                    html.P('Monitor, control, and review traffic simulation runs'),
                                ],
                            ),

                            html.Div(className='sim-page-grid', children=[

                                # ── LEFT COLUMN ─────────────────────────
                                html.Div(className='sim-col-left', children=[

                                    # Run Overview card
                                    html.Div(className='card sim-card', children=[
                                        html.Div(className='card-title compact', children=[
                                            html.I(className='fa-solid fa-clock'),
                                            ' Run Overview',
                                        ]),
                                        html.Div(className='sim-overview-grid', children=[
                                            _stat_cell('Elapsed Time', '00:14:32', 'sim-elapsed'),
                                            _stat_cell('Simulation Time', '00:14:32', 'sim-time'),
                                            _stat_cell('Active Scenario', 'None', 'sim-active-scenario'),
                                            _stat_cell('Control Mode', 'Fixed-Time', 'sim-control-mode'),
                                        ]),
                                        html.Div(className='sim-overview-status', children=[
                                            html.Span('Current Status', className='sim-stat-label'),
                                            html.Span('Idle', id='sim-current-status', className='sim-stat-badge idle'),
                                        ]),
                                    ]),

                                    # Simulation Status card
                                    html.Div(className='card sim-card', children=[
                                        html.Div(className='card-title compact', children=[
                                            html.I(className='fa-solid fa-info-circle'),
                                            ' Simulation Status',
                                        ]),
                                        html.Div(className='sim-overview-grid', children=[
                                            _stat_cell('Steps Completed', '0', 'sim-steps'),
                                            _stat_cell('Last Action', '—', id='sim-last-action'),
                                            _stat_cell('Last Error', 'None', id='sim-last-error'),
                                            _stat_cell('Run ID', '—', id='sim-run-id'),
                                        ]),
                                    ]),

                                    # Simulation Log card
                                    html.Div(className='card sim-card sim-log-card', children=[
                                        html.Div(className='analytics-header', children=[
                                            html.Span(className='card-title', children=[
                                                html.I(className='fa-solid fa-list'),
                                                ' Simulation Log',
                                            ]),
                                            html.Span('Clear', className='clear-btn'),
                                        ]),
                                        html.Div(
                                            id='simulation-log',
                                            className='events-feed',
                                            children=[
                                                html.Div(className='event-item info', children=[
                                                    html.Span('--:--:--', className='event-time'),
                                                    html.I(className='fa-solid fa-circle-info event-icon'),
                                                    html.Span('Simulation not started', className='event-text'),
                                                ]),
                                            ],
                                        ),
                                    ]),
                                ]),

                                # ── RIGHT COLUMN ────────────────────────
                                html.Div(className='sim-col-right', children=[

                                    # Simulation Controls card
                                    html.Div(className='card control-card', children=[
                                        html.H3(className='card-title compact', children=[
                                            html.I(className='fa-solid fa-gamepad'),
                                            ' Simulation Controls',
                                        ]),
                                        html.Div(className='control-buttons', children=[
                                            html.Button(id='start-btn', className='ctrl-btn start', children=[
                                                html.I(className='fa-solid fa-play'),
                                                html.Span('Start Simulation'),
                                            ]),
                                            html.Button(id='pause-btn', className='ctrl-btn pause', children=[
                                                html.I(className='fa-solid fa-pause'),
                                                html.Span('Pause'),
                                            ]),
                                            html.Button(id='stop-btn', className='ctrl-btn stop', children=[
                                                html.I(className='fa-solid fa-stop'),
                                                html.Span('Stop Simulation'),
                                            ]),
                                            html.Button(id='reset-btn', className='ctrl-btn reset', children=[
                                                html.I(className='fa-solid fa-redo'),
                                                html.Span('Reset Simulation'),
                                            ]),
                                        ]),
                                    ]),

                                    # Scenario Config card
                                    html.Div(className='card settings-card', children=[
                                        html.H3(className='card-title compact', children=[
                                            html.I(className='fa-solid fa-sliders'),
                                            ' Scenario',
                                        ]),
                                        html.Div(className='setting-group', children=[
                                            html.Label('Traffic Density', className='setting-label'),
                                            html.Select(
                                                id='sim-traffic-density',
                                                className='sim-select',
                                                children=[
                                                    html.Option('Low'),
                                                    html.Option('Medium'),
                                                    html.Option('High', selected=True),
                                                    html.Option('Very High'),
                                                ],
                                            ),
                                        ]),
                                        html.Div(className='setting-group', children=[
                                            html.Label('Control Mode', className='setting-label'),
                                            html.Select(
                                                id='sim-control-mode-select',
                                                className='sim-select',
                                                children=[
                                                    html.Option('Fixed-Time', selected=True),
                                                    html.Option('RL Agent (DQN)'),
                                                    html.Option('RL Agent (PPO)'),
                                                ],
                                            ),
                                        ]),
                                        html.Button(
                                            id='apply-btn',
                                            className='apply-btn',
                                            children=[
                                                html.I(className='fa-solid fa-check'),
                                                ' Apply',
                                            ],
                                        ),
                                    ]),
                                ]),
                            ]),
                        ],
                    ),
                ],
            ),
        ],
    )


def _stat_cell(label, value, id=None):
    return html.Div(className='sim-stat-cell', children=[
        html.Span(label, className='sim-stat-label'),
        html.Span(value, id=id, className='sim-stat-value'),
    ])
