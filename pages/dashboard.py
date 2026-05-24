"""
SMARTFLOW — Dashboard Page
Main dashboard showing traffic overview with simulation view, KPIs, charts, and controls.
Mirrors the original SMARTFLOW layout (from layout.py) inside the authenticated multi-page structure.
"""

from dash import html, dcc
from components.header import create_header
from components.sidebar import create_sidebar
from layout import (
    create_simulation_view,
    create_control_panel,
    create_kpi_row,
    create_analytics_section,
    create_footer,
)


def layout():
    return html.Div(
        className='app-layout',
        children=[
            dcc.Interval(id='clock-interval', interval=1000, n_intervals=0),
            dcc.Interval(id='sim-interval', interval=1000, n_intervals=0),
            dcc.Store(
                id='sim-state',
                data={'status': 'running', 'elapsed_seconds': 872, 'phase_seconds': 18},
            ),

            create_header(),

            html.Div(
                className='app-body',
                children=[
                    create_sidebar(),
                    html.Main(
                        className='main-content',
                        children=[
                            html.Div(className='top-row', children=[
                                create_simulation_view(),
                                html.Div(className='right-panel', children=[
                                    create_control_panel(),
                                ]),
                            ]),
                            create_kpi_row(),
                            create_analytics_section(),
                            create_footer(),
                        ]
                    ),
                ]
            ),
        ]
    )
