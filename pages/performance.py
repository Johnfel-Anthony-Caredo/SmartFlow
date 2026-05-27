"""
SMARTFLOW — Performance Page
Performance metrics, charts, and analysis.
"""

from dash import html, dcc
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_kpi_card, create_mini_stat


# ─── Chart Theme Defaults ──────────────────────────────────────────

_LAYOUT = {
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'font': {'family': 'Inter, sans-serif', 'color': '#94a3b8', 'size': 11},
    'margin': {'l': 48, 'r': 16, 't': 36, 'b': 40},
    'xaxis': {
        'gridcolor': 'rgba(255,255,255,0.03)',
        'zerolinecolor': 'rgba(255,255,255,0.06)',
        'tickfont': {'size': 10, 'color': '#64748b'},
        'title': {'font': {'size': 11, 'color': '#64748b'}},
    },
    'yaxis': {
        'gridcolor': 'rgba(255,255,255,0.03)',
        'zerolinecolor': 'rgba(255,255,255,0.06)',
        'tickfont': {'size': 10, 'color': '#64748b'},
        'title': {'font': {'size': 11, 'color': '#64748b'}},
    },
    'legend': {
        'font': {'size': 11, 'color': '#94a3b8'},
        'bgcolor': 'rgba(0,0,0,0)',
        'bordercolor': 'rgba(255,255,255,0.06)',
    },
    'showlegend': True,
}

_GRAPH_CONFIG = {'displayModeBar': False, 'responsive': True}


def _empty_chart(title, xaxis_title, yaxis_title, **overrides):
    """Return a dark-themed empty figure."""
    layout = {**_LAYOUT}
    layout['title'] = {'text': title, 'font': {'size': 13, 'color': '#f1f5f9'}, 'x': 0.02, 'xanchor': 'left'}
    layout['xaxis'] = {**layout['xaxis'], 'title': {'text': xaxis_title, 'font': {'size': 11, 'color': '#64748b'}}}
    layout['yaxis'] = {**layout['yaxis'], 'title': {'text': yaxis_title, 'font': {'size': 11, 'color': '#64748b'}}}
    layout.update(overrides)
    return {'data': [], 'layout': layout}


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
                                    html.H1('Performance'),
                                    html.P('Traffic performance metrics and analysis'),
                                ],
                            ),

                            # ── KPI Summary ──
                            html.Div(
                                className='stats-row',
                                children=[
                                    create_kpi_card(
                                        id='perf-avg-wait',
                                        icon='fas fa-clock',
                                        title='Avg. Wait Time',
                                        value='-- s',
                                        color='var(--accent)',
                                    ),
                                    create_kpi_card(
                                        id='perf-max-queue',
                                        icon='fas fa-car',
                                        title='Max Queue',
                                        value='--',
                                        color='var(--info)',
                                    ),
                                    create_kpi_card(
                                        id='perf-throughput',
                                        icon='fas fa-tachometer-alt',
                                        title='Throughput',
                                        value='-- veh/h',
                                        color='var(--warning)',
                                    ),
                                    create_kpi_card(
                                        id='perf-efficiency',
                                        icon='fas fa-chart-line',
                                        title='Efficiency',
                                        value='--%',
                                        color='var(--purple)',
                                    ),
                                ],
                            ),

                            # ── Charts ──
                            create_section(
                                title='Waiting Time Analysis',
                                icon='fas fa-hourglass-half',
                                children=[
                                    dcc.Graph(
                                        id='wait-time-chart',
                                        figure=_empty_chart(
                                            'Average Waiting Time Over Time',
                                            'Time Step', 'Waiting Time (seconds)',
                                        ),
                                        config=_GRAPH_CONFIG,
                                    ),
                                ],
                            ),

                            html.Div(className='perf-charts-row', children=[
                                create_section(
                                    title='Queue Length Analysis',
                                    icon='fas fa-car',
                                    children=[
                                        dcc.Graph(
                                            id='queue-length-chart',
                                            figure=_empty_chart(
                                                'Queue Length by Direction',
                                                'Time Step', 'Queue Length (vehicles)',
                                            ),
                                            config=_GRAPH_CONFIG,
                                        ),
                                    ],
                                ),

                                create_section(
                                    title='Throughput Analysis',
                                    icon='fas fa-tachometer-alt',
                                    children=[
                                        dcc.Graph(
                                            id='throughput-chart',
                                            figure=_empty_chart(
                                                'Vehicle Throughput Over Time',
                                                'Time Step', 'Vehicles per Hour',
                                            ),
                                            config=_GRAPH_CONFIG,
                                        ),
                                    ],
                                ),
                            ]),

                            # ── Comparison ──
                            create_section(
                                title='Control Mode Comparison',
                                icon='fas fa-balance-scale',
                                children=[
                                    html.Div(
                                        className='perf-comparison-controls',
                                        children=[
                                            html.Div(
                                                className='form-group',
                                                style={'marginBottom': 0, 'minWidth': '220px'},
                                                children=[
                                                    html.Label('Compare'),
                                                    dcc.Dropdown(
                                                        id='comparison-mode',
                                                        options=[
                                                            {'label': 'Fixed-Time vs AI Agent', 'value': 'both'},
                                                            {'label': 'Fixed-Time Only', 'value': 'fixed'},
                                                            {'label': 'AI Agent Only', 'value': 'ai'},
                                                        ],
                                                        value='both',
                                                        clearable=False,
                                                        className='dash-dropdown',
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dcc.Graph(
                                        id='comparison-chart',
                                        figure=_empty_chart(
                                            'Performance Comparison: Fixed-Time vs AI Agent',
                                            'Metric', 'Value',
                                            barmode='group',
                                        ),
                                        config=_GRAPH_CONFIG,
                                    ),
                                ],
                            ),

                            # ── Detailed Metrics ──
                            create_section(
                                title='Detailed Metrics',
                                icon='fas fa-table',
                                children=[
                                    html.Div(
                                        id='metrics-table',
                                        className='perf-placeholder',
                                        children=[
                                            html.I(className='fas fa-chart-bar'),
                                            html.P('Run a simulation to view detailed metrics'),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
