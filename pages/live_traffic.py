"""
SMARTFLOW — Live Traffic Page
Real-time traffic visualization and monitoring.
"""

from dash import html, dcc
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section


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
                                    html.H1(children='Live Traffic'),
                                    html.P(children='Real-time traffic visualization and monitoring'),
                                ]
                            ),
                            
                            html.Div(
                                className='traffic-grid',
                                children=[
                                    html.Div(
                                        className='traffic-card wide',
                                        children=[
                                            html.H3(children=[
                                                html.I(className='fas fa-road'),
                                                ' Intersection View'
                                            ]),
                                            html.Div(
                                                id='intersection-view',
                                                className='intersection-canvas',
                                                children=[
                                                    html.Div(
                                                        className='placeholder-visualization',
                                                        children=[
                                                            html.I(className='fas fa-video', style={'fontSize': '48px'}),
                                                            html.P(children='Live intersection visualization'),
                                                            html.P(className='placeholder-subtext', 
                                                                   children='Connect simulation engine to display real-time traffic'),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                    
                                    html.Div(
                                        className='traffic-card',
                                        children=[
                                            html.H3(children=[
                                                html.I(className='fas fa-traffic-light'),
                                                ' Signal Status'
                                            ]),
                                            html.Div(
                                                id='signal-status',
                                                className='signal-display',
                                                children=[
                                                    html.Div(
                                                        className='signal-item',
                                                        children=[
                                                            html.Span(className='signal-label', children='North-South:'),
                                                            html.Span(id='ns-signal', className='signal-value red', children='Red'),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='signal-item',
                                                        children=[
                                                            html.Span(className='signal-label', children='East-West:'),
                                                            html.Span(id='ew-signal', className='signal-value green', children='Green'),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='signal-item',
                                                        children=[
                                                            html.Span(className='signal-label', children='Phase Timer:'),
                                                            html.Span(id='phase-timer', className='signal-value', children='--'),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='metrics-grid',
                                children=[
                                    create_section(
                                        title='Queue Lengths',
                                        icon='fas fa-car',
                                        children=[
                                            html.Div(
                                                className='queue-display',
                                                children=[
                                                    html.Div(className='queue-item', children=[
                                                        html.Span(className='direction', children='North'),
                                                        html.Span(id='queue-north', className='queue-value', children='0'),
                                                    ]),
                                                    html.Div(className='queue-item', children=[
                                                        html.Span(className='direction', children='South'),
                                                        html.Span(id='queue-south', className='queue-value', children='0'),
                                                    ]),
                                                    html.Div(className='queue-item', children=[
                                                        html.Span(className='direction', children='East'),
                                                        html.Span(id='queue-east', className='queue-value', children='0'),
                                                    ]),
                                                    html.Div(className='queue-item', children=[
                                                        html.Span(className='direction', children='West'),
                                                        html.Span(id='queue-west', className='queue-value', children='0'),
                                                    ]),
                                                ]
                                            ),
                                        ]
                                    ),
                                    
                                    create_section(
                                        title='Waiting Times (seconds)',
                                        icon='fas fa-clock',
                                        children=[
                                            html.Div(
                                                className='wait-display',
                                                children=[
                                                    html.Div(className='wait-item', children=[
                                                        html.Span(className='direction', children='North'),
                                                        html.Span(id='wait-north', className='wait-value', children='0.0'),
                                                    ]),
                                                    html.Div(className='wait-item', children=[
                                                        html.Span(className='direction', children='South'),
                                                        html.Span(id='wait-south', className='wait-value', children='0.0'),
                                                    ]),
                                                    html.Div(className='wait-item', children=[
                                                        html.Span(className='direction', children='East'),
                                                        html.Span(id='wait-east', className='wait-value', children='0.0'),
                                                    ]),
                                                    html.Div(className='wait-item', children=[
                                                        html.Span(className='direction', children='West'),
                                                        html.Span(id='wait-west', className='wait-value', children='0.0'),
                                                    ]),
                                                ]
                                            ),
                                        ]
                                    ),
                                    
                                    create_section(
                                        title='Active Vehicles',
                                        icon='fas fa-car-side',
                                        children=[
                                            html.Div(
                                                className='vehicle-stats',
                                                children=[
                                                    html.Div(className='vehicle-stat', children=[
                                                        html.Span(className='stat-label', children='Total Vehicles:'),
                                                        html.Span(id='total-vehicles', className='stat-value', children='0'),
                                                    ]),
                                                    html.Div(className='vehicle-stat', children=[
                                                        html.Span(className='stat-label', children='Moving:'),
                                                        html.Span(id='moving-vehicles', className='stat-value', children='0'),
                                                    ]),
                                                    html.Div(className='vehicle-stat', children=[
                                                        html.Span(className='stat-label', children='Stopped:'),
                                                        html.Span(id='stopped-vehicles', className='stat-value', children='0'),
                                                    ]),
                                                    html.Div(className='vehicle-stat', children=[
                                                        html.Span(className='stat-label', children='Emergency:'),
                                                        html.Span(id='emergency-vehicles', className='stat-value highlight', children='0'),
                                                    ]),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='live-charts',
                                children=[
                                    html.H3(children=[
                                        html.I(className='fas fa-chart-line'),
                                        ' Real-Time Charts'
                                    ]),
                                    html.Div(
                                        className='charts-row',
                                        children=[
                                            dcc.Graph(
                                                id='live-queue-chart',
                                                figure={
                                                    'data': [],
                                                    'layout': {
                                                        'title': 'Queue Length Over Time',
                                                        'xaxis': {'title': 'Time'},
                                                        'yaxis': {'title': 'Vehicles'},
                                                        'plot_bgcolor': '#ffffff',
                                                        'paper_bgcolor': '#ffffff',
                                                    }
                                                },
                                                config={'displayModeBar': False}
                                            ),
                                            dcc.Graph(
                                                id='live-wait-chart',
                                                figure={
                                                    'data': [],
                                                    'layout': {
                                                        'title': 'Waiting Time Over Time',
                                                        'xaxis': {'title': 'Time'},
                                                        'yaxis': {'title': 'Seconds'},
                                                        'plot_bgcolor': '#ffffff',
                                                        'paper_bgcolor': '#ffffff',
                                                    }
                                                },
                                                config={'displayModeBar': False}
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            dcc.Interval(id='live-update-interval', interval=1000, n_intervals=0),
        ]
    )
