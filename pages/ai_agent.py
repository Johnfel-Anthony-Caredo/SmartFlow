"""
SMARTFLOW — AI Agent Page
Reinforcement learning agent monitoring and training status.
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
                                    html.H1(children='AI Agent (RL)'),
                                    html.P(children='Reinforcement learning agent status and training'),
                                ]
                            ),
                            
                            html.Div(
                                className='kpi-grid',
                                children=[
                                    create_kpi_card(
                                        id='rl-episodes',
                                        icon='fas fa-redo',
                                        title='Episodes',
                                        value='--',
                                        color='#00e676'
                                    ),
                                    create_kpi_card(
                                        id='rl-reward',
                                        icon='fas fa-star',
                                        title='Avg. Reward',
                                        value='--',
                                        color='#ffc107'
                                    ),
                                    create_kpi_card(
                                        id='rl-epsilon',
                                        icon='fas fa-random',
                                        title='Epsilon',
                                        value='--',
                                        color='#2196f3'
                                    ),
                                    create_kpi_card(
                                        id='rl-loss',
                                        icon='fas fa-chart-line',
                                        title='Loss',
                                        value='--',
                                        color='#f44336'
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='agent-status-section',
                                children=[
                                    create_section(
                                        title='Agent Status',
                                        icon='fas fa-robot',
                                        children=[
                                            html.Div(
                                                className='status-grid',
                                                children=[
                                                    html.Div(
                                                        className='status-card',
                                                        children=[
                                                            html.Div(className='status-label', children='Status'),
                                                            html.Div(id='agent-status', className='status-large idle', children='Idle'),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='status-card',
                                                        children=[
                                                            html.Div(className='status-label', children='Model'),
                                                            html.Div(id='agent-model', className='status-large', children='DQN'),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='status-card',
                                                        children=[
                                                            html.Div(className='status-label', children='Last Action'),
                                                            html.Div(id='agent-last-action', className='status-large', children='--'),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='status-card',
                                                        children=[
                                                            html.Div(className='status-label', children='Total Steps'),
                                                            html.Div(id='agent-total-steps', className='status-large', children='0'),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='training-charts',
                                children=[
                                    create_section(
                                        title='Training Progress',
                                        icon='fas fa-chart-area',
                                        children=[
                                            dcc.Graph(
                                                id='reward-chart',
                                                figure={
                                                    'data': [],
                                                    'layout': {
                                                        'title': 'Reward per Episode',
                                                        'xaxis': {'title': 'Episode'},
                                                        'yaxis': {'title': 'Reward'},
                                                        'plot_bgcolor': '#ffffff',
                                                        'paper_bgcolor': '#ffffff',
                                                    }
                                                },
                                                config={'displayModeBar': True}
                                            ),
                                        ]
                                    ),
                                    
                                    create_section(
                                        title='Loss and Epsilon',
                                        icon='fas fa-chart-line',
                                        children=[
                                            html.Div(
                                                className='charts-row',
                                                children=[
                                                    dcc.Graph(
                                                        id='loss-chart',
                                                        figure={
                                                            'data': [],
                                                            'layout': {
                                                                'title': 'Training Loss',
                                                                'xaxis': {'title': 'Episode'},
                                                                'yaxis': {'title': 'Loss'},
                                                                'plot_bgcolor': '#ffffff',
                                                                'paper_bgcolor': '#ffffff',
                                                            }
                                                        },
                                                        config={'displayModeBar': False}
                                                    ),
                                                    dcc.Graph(
                                                        id='epsilon-chart',
                                                        figure={
                                                            'data': [],
                                                            'layout': {
                                                                'title': 'Epsilon Decay',
                                                                'xaxis': {'title': 'Episode'},
                                                                'yaxis': {'title': 'Epsilon'},
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
                            
                            html.Div(
                                className='agent-controls-section',
                                children=[
                                    create_section(
                                        title='Training Controls',
                                        icon='fas fa-cogs',
                                        children=[
                                            html.Div(
                                                className='control-buttons',
                                                children=[
                                                    html.Button(
                                                        id='train-agent-btn',
                                                        className='btn btn-success',
                                                        children=[
                                                            html.I(className='fas fa-play'),
                                                            ' Start Training'
                                                        ]
                                                    ),
                                                    html.Button(
                                                        id='stop-training-btn',
                                                        className='btn btn-danger',
                                                        children=[
                                                            html.I(className='fas fa-stop'),
                                                            ' Stop Training'
                                                        ]
                                                    ),
                                                    html.Button(
                                                        id='save-model-btn',
                                                        className='btn btn-primary',
                                                        children=[
                                                            html.I(className='fas fa-save'),
                                                            ' Save Model'
                                                        ]
                                                    ),
                                                    html.Button(
                                                        id='load-model-btn',
                                                        className='btn btn-secondary',
                                                        children=[
                                                            html.I(className='fas fa-upload'),
                                                            ' Load Model'
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            
                                            html.Div(
                                                className='training-config',
                                                children=[
                                                    html.H4(children='Hyperparameters'),
                                                    html.Div(
                                                        className='config-grid',
                                                        children=[
                                                            html.Div(
                                                                className='form-group',
                                                                children=[
                                                                    html.Label(children='Learning Rate'),
                                                                    dcc.Input(
                                                                        id='learning-rate',
                                                                        type='number',
                                                                        value=0.001,
                                                                        step=0.0001,
                                                                        min=0.0001,
                                                                        max=0.1,
                                                                        className='input-field'
                                                                    ),
                                                                ]
                                                            ),
                                                            html.Div(
                                                                className='form-group',
                                                                children=[
                                                                    html.Label(children='Discount Factor (γ)'),
                                                                    dcc.Input(
                                                                        id='discount-factor',
                                                                        type='number',
                                                                        value=0.99,
                                                                        step=0.01,
                                                                        min=0.5,
                                                                        max=1.0,
                                                                        className='input-field'
                                                                    ),
                                                                ]
                                                            ),
                                                            html.Div(
                                                                className='form-group',
                                                                children=[
                                                                    html.Label(children='Batch Size'),
                                                                    dcc.Input(
                                                                        id='batch-size',
                                                                        type='number',
                                                                        value=32,
                                                                        step=1,
                                                                        min=1,
                                                                        max=256,
                                                                        className='input-field'
                                                                    ),
                                                                ]
                                                            ),
                                                            html.Div(
                                                                className='form-group',
                                                                children=[
                                                                    html.Label(children='Target Update Freq'),
                                                                    dcc.Input(
                                                                        id='target-update',
                                                                        type='number',
                                                                        value=10,
                                                                        step=1,
                                                                        min=1,
                                                                        max=100,
                                                                        className='input-field'
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
                    ),
                ]
            ),
        ]
    )
