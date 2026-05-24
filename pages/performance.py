"""
SMARTFLOW — Performance Page
Performance metrics, charts, and analysis.
"""

from dash import html, dcc
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_kpi_card


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
                                    html.H1(children='Performance'),
                                    html.P(children='Traffic performance metrics and analysis'),
                                ]
                            ),
                            
                            html.Div(
                                className='kpi-grid',
                                children=[
                                    create_kpi_card(
                                        id='perf-avg-wait',
                                        icon='fas fa-clock',
                                        title='Avg. Wait Time',
                                        value='-- s',
                                        color='#00e676'
                                    ),
                                    create_kpi_card(
                                        id='perf-max-queue',
                                        icon='fas fa-car',
                                        title='Max Queue',
                                        value='--',
                                        color='#2196f3'
                                    ),
                                    create_kpi_card(
                                        id='perf-throughput',
                                        icon='fas fa-tachometer-alt',
                                        title='Throughput',
                                        value='-- veh/h',
                                        color='#ff9800'
                                    ),
                                    create_kpi_card(
                                        id='perf-efficiency',
                                        icon='fas fa-chart-line',
                                        title='Efficiency',
                                        value='--%',
                                        color='#9c27b0'
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='performance-charts',
                                children=[
                                    create_section(
                                        title='Waiting Time Analysis',
                                        icon='fas fa-hourglass-half',
                                        children=[
                                            dcc.Graph(
                                                id='wait-time-chart',
                                                figure={
                                                    'data': [],
                                                    'layout': {
                                                        'title': 'Average Waiting Time Over Time',
                                                        'xaxis': {'title': 'Time Step'},
                                                        'yaxis': {'title': 'Waiting Time (seconds)'},
                                                        'plot_bgcolor': '#ffffff',
                                                        'paper_bgcolor': '#ffffff',
                                                        'showlegend': True,
                                                    }
                                                },
                                                config={'displayModeBar': True}
                                            ),
                                        ]
                                    ),
                                    
                                    create_section(
                                        title='Queue Length Analysis',
                                        icon='fas fa-car',
                                        children=[
                                            dcc.Graph(
                                                id='queue-length-chart',
                                                figure={
                                                    'data': [],
                                                    'layout': {
                                                        'title': 'Queue Length by Direction',
                                                        'xaxis': {'title': 'Time Step'},
                                                        'yaxis': {'title': 'Queue Length (vehicles)'},
                                                        'plot_bgcolor': '#ffffff',
                                                        'paper_bgcolor': '#ffffff',
                                                        'showlegend': True,
                                                    }
                                                },
                                                config={'displayModeBar': True}
                                            ),
                                        ]
                                    ),
                                    
                                    create_section(
                                        title='Throughput Analysis',
                                        icon='fas fa-tachometer-alt',
                                        children=[
                                            dcc.Graph(
                                                id='throughput-chart',
                                                figure={
                                                    'data': [],
                                                    'layout': {
                                                        'title': 'Vehicle Throughput Over Time',
                                                        'xaxis': {'title': 'Time Step'},
                                                        'yaxis': {'title': 'Vehicles per Hour'},
                                                        'plot_bgcolor': '#ffffff',
                                                        'paper_bgcolor': '#ffffff',
                                                    }
                                                },
                                                config={'displayModeBar': True}
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='comparison-section',
                                children=[
                                    create_section(
                                        title='Control Mode Comparison',
                                        icon='fas fa-balance-scale',
                                        children=[
                                            html.Div(
                                                className='comparison-controls',
                                                children=[
                                                    html.Div(
                                                        className='form-group',
                                                        children=[
                                                            html.Label(children='Compare:'),
                                                            dcc.Dropdown(
                                                                id='comparison-mode',
                                                                options=[
                                                                    {'label': 'Fixed-Time vs AI Agent', 'value': 'both'},
                                                                    {'label': 'Fixed-Time Only', 'value': 'fixed'},
                                                                    {'label': 'AI Agent Only', 'value': 'ai'},
                                                                ],
                                                                value='both',
                                                                clearable=False
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            
                                            dcc.Graph(
                                                id='comparison-chart',
                                                figure={
                                                    'data': [],
                                                    'layout': {
                                                        'title': 'Performance Comparison: Fixed-Time vs AI Agent',
                                                        'xaxis': {'title': 'Metric'},
                                                        'yaxis': {'title': 'Value'},
                                                        'barmode': 'group',
                                                        'plot_bgcolor': '#ffffff',
                                                        'paper_bgcolor': '#ffffff',
                                                        'showlegend': True,
                                                    }
                                                },
                                                config={'displayModeBar': True}
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='metrics-table-section',
                                children=[
                                    create_section(
                                        title='Detailed Metrics',
                                        icon='fas fa-table',
                                        children=[
                                            html.Div(
                                                id='metrics-table',
                                                className='table-container',
                                                children=[
                                                    html.P(
                                                        className='placeholder-text',
                                                        children='Run a simulation to view detailed metrics'
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
        ]
    )
