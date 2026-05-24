"""
SMARTFLOW — Help & About Page
System guide, metrics explanation, RL vs fixed time details.
"""

from dash import html
import auth
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section


def layout():
    # If not authenticated, let app.py redirect
    if not auth.is_authenticated():
        return html.Div()
        
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
                                    html.H1(children='Help & Documentation'),
                                    html.P(children='Learn how to run traffic simulation experiments, understand key metrics, and configure AI reinforcement learning settings.'),
                                ]
                            ),
                            
                            html.Div(
                                style={'display': 'grid', 'gridTemplateColumns': '2fr 1fr', 'gap': '20px'},
                                children=[
                                    html.Div(children=[
                                        create_section(
                                            title='Getting Started with SMARTFLOW',
                                            icon='fas fa-info-circle',
                                            children=[
                                                html.P('SMARTFLOW is a local simulation-based traffic analysis and decision-support platform designed to evaluate AI-optimized traffic signals against traditional fixed-time controls.'),
                                                html.H4('Quick Start Steps:'),
                                                html.Ol(children=[
                                                    html.Li('Navigate to the Scenarios tab to choose a preset or configure custom traffic/weather conditions.'),
                                                    html.Li('Go to the Simulation Control panel to select either Fixed-Time or AI Agent control modes.'),
                                                    html.Li('Click the Start button to execute the simulation in real time.'),
                                                    html.Li('Observe performance metrics (queue lengths, wait times) in the live telemetry grid and the Performance charts tab.'),
                                                    html.Li('Export reports to PDF or Excel from the Runs & Reports history table.')
                                                ], style={'paddingLeft': '20px', 'lineHeight': '1.6'})
                                            ]
                                        ),
                                        
                                        html.Div(style={'marginTop': '20px'}, children=[
                                            create_section(
                                                title='Traffic Metrics Glossary',
                                                icon='fas fa-chart-line',
                                                children=[
                                                    html.Ul(children=[
                                                        html.Li([
                                                            html.Strong('Average Waiting Time: '),
                                                            html.Span('The average duration (in seconds) a vehicle spends at a complete stop in a queue before crossing the intersection.')
                                                        ], style={'marginBottom': '10px'}),
                                                        html.Li([
                                                            html.Strong('Average Queue Length: '),
                                                            html.Span('The average number of vehicles queued in a lane during a signal phase cycle.')
                                                        ], style={'marginBottom': '10px'}),
                                                        html.Li([
                                                            html.Strong('Maximum Queue Length: '),
                                                            html.Span('The peak count of vehicles waiting in any approach lane during a run, helpful for identify bottle-neck approaches.')
                                                        ], style={'marginBottom': '10px'}),
                                                        html.Li([
                                                            html.Strong('Throughput: '),
                                                            html.Span('The rate of vehicles completing their journey and exiting the network per hour (veh/h).')
                                                        ], style={'marginBottom': '10px'}),
                                                        html.Li([
                                                            html.Strong('Emergency Clearance Status: '),
                                                            html.Span('Indicates if emergency vehicles (ambulances, fire trucks) are successfully prioritized, bypassing standard signal cycles.')
                                                        ], style={'marginBottom': '10px'})
                                                    ], style={'listStyleType': 'square', 'paddingLeft': '20px', 'lineHeight': '1.5'})
                                                ]
                                            )
                                        ]),
                                        
                                        html.Div(style={'marginTop': '20px'}, children=[
                                            create_section(
                                                title='Frequently Asked Questions (FAQ)',
                                                icon='fas fa-question-circle',
                                                children=[
                                                    html.Div(style={'marginBottom': '15px'}, children=[
                                                        html.Strong('Q: How is the AI reinforcement learning model trained?'),
                                                        html.P('A: The AI agent uses Deep Q-Networks (DQN) to select signal phases. It receives a reward based on minimizing total cumulative waiting times and queue lengths at the intersection, learning optimal policies over successive episodes.')
                                                    ]),
                                                    html.Div(style={'marginBottom': '15px'}, children=[
                                                        html.Strong('Q: Can I run multiple simulations at the same time?'),
                                                        html.P('A: SMARTFLOW is designed to execute one live simulation run per session to ensure reliable performance on local engines, but you can compare results of multiple runs side-by-side in the Runs & Reports tab.')
                                                    ]),
                                                    html.Div(style={'marginBottom': '10px'}, children=[
                                                        html.Strong('Q: What happens if a user account is locked or pending?'),
                                                        html.P('A: Default registration puts new accounts in "Pending Approval" state. An administrator must approve the account via the User Management panel before the user can log in.')
                                                    ])
                                                ]
                                            )
                                        ])
                                    ]),
                                    
                                    html.Div(children=[
                                        create_section(
                                            title='About Platform',
                                            icon='fas fa-desktop',
                                            children=[
                                                html.Div(style={'lineHeight': '1.8'}, children=[
                                                    html.Div([
                                                        html.Strong('App Version: '),
                                                        html.Span('1.0.0')
                                                    ]),
                                                    html.Div([
                                                        html.Strong('Engine Interface: '),
                                                        html.Span('SQLite DB + SUMO / TraCI Telemetry Mock')
                                                    ]),
                                                    html.Div([
                                                        html.Strong('Authentication: '),
                                                        html.Span('Secure Werkzeug PBKDF2/scrypt')
                                                    ]),
                                                    html.Div([
                                                        html.Strong('UI Framework: '),
                                                        html.Span('Plotly Dash Native Components')
                                                    ]),
                                                    html.Div([
                                                        html.Strong('Target Area: '),
                                                        html.Span('Tagum City Traffic Analysis Presets')
                                                    ]),
                                                    html.Hr(style={'margin': '15px 0', 'border': 'none', 'borderTop': '1px solid #dee2e6'}),
                                                    html.P('SMARTFLOW Traffic simulation control center was designed to support AI-driven traffic optimization research, facilitating decisions on physical road structures and reinforcement learning algorithms.', style={'fontSize': '13px', 'color': '#64748b'})
                                                ])
                                            ]
                                        )
                                    ])
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )
