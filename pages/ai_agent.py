"""
SMARTFLOW — AI Agent Page
Reinforcement learning agent monitoring and training status.
"""

from dash import html, dcc
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_kpi_card


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
    'showlegend': False,
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
                                    html.H1('AI Agent (RL)'),
                                    html.P('Reinforcement learning agent status and training'),
                                ],
                            ),

                            # ── KPI Summary ──
                            html.Div(
                                className='stats-row',
                                children=[
                                    create_kpi_card(
                                        id='rl-episodes',
                                        icon='fas fa-redo',
                                        title='Episodes',
                                        value='--',
                                        color='var(--accent)',
                                    ),
                                    create_kpi_card(
                                        id='rl-reward',
                                        icon='fas fa-star',
                                        title='Avg. Reward',
                                        value='--',
                                        color='var(--warning)',
                                    ),
                                    create_kpi_card(
                                        id='rl-epsilon',
                                        icon='fas fa-random',
                                        title='Epsilon',
                                        value='--',
                                        color='var(--info)',
                                    ),
                                    create_kpi_card(
                                        id='rl-loss',
                                        icon='fas fa-chart-line',
                                        title='Loss',
                                        value='--',
                                        color='var(--error)',
                                    ),
                                ],
                            ),

                            # ── Agent Status ──
                            create_section(
                                title='Agent Status',
                                icon='fas fa-robot',
                                children=[
                                    html.Div(
                                        className='agent-status-grid',
                                        children=[
                                            html.Div(className='agent-status-card', children=[
                                                html.Span('Status', className='agent-status-label'),
                                                html.Span('Idle', id='agent-status',
                                                          className='agent-status-value idle'),
                                            ]),
                                            html.Div(className='agent-status-card', children=[
                                                html.Span('Model', className='agent-status-label'),
                                                html.Span('DQN', id='agent-model',
                                                          className='agent-status-value'),
                                            ]),
                                            html.Div(className='agent-status-card', children=[
                                                html.Span('Last Action', className='agent-status-label'),
                                                html.Span('--', id='agent-last-action',
                                                          className='agent-status-value'),
                                            ]),
                                            html.Div(className='agent-status-card', children=[
                                                html.Span('Total Steps', className='agent-status-label'),
                                                html.Span('0', id='agent-total-steps',
                                                          className='agent-status-value'),
                                            ]),
                                        ],
                                    ),
                                ],
                            ),

                            # ── Training Charts ──
                            create_section(
                                title='Training Progress',
                                icon='fas fa-chart-area',
                                children=[
                                    dcc.Graph(
                                        id='reward-chart',
                                        figure=_empty_chart(
                                            'Reward per Episode',
                                            'Episode', 'Reward',
                                        ),
                                        config=_GRAPH_CONFIG,
                                    ),
                                ],
                            ),

                            html.Div(className='agent-training-row', children=[
                                create_section(
                                    title='Training Loss',
                                    icon='fas fa-chart-line',
                                    children=[
                                        dcc.Graph(
                                            id='loss-chart',
                                            figure=_empty_chart(
                                                'Training Loss',
                                                'Episode', 'Loss',
                                            ),
                                            config=_GRAPH_CONFIG,
                                        ),
                                    ],
                                ),

                                create_section(
                                    title='Epsilon Decay',
                                    icon='fas fa-chart-area',
                                    children=[
                                        dcc.Graph(
                                            id='epsilon-chart',
                                            figure=_empty_chart(
                                                'Epsilon Decay',
                                                'Episode', 'Epsilon',
                                            ),
                                            config=_GRAPH_CONFIG,
                                        ),
                                    ],
                                ),
                            ]),

                            # ── Training Controls & Hyperparameters ──
                            create_section(
                                title='Training Controls',
                                icon='fas fa-cogs',
                                children=[
                                    html.Div(
                                        className='agent-control-btns',
                                        children=[
                                            html.Button(
                                                id='train-agent-btn',
                                                className='btn btn-success',
                                                children=[
                                                    html.I(className='fas fa-play'),
                                                    ' Start Training',
                                                ],
                                            ),
                                            html.Button(
                                                id='stop-training-btn',
                                                className='btn btn-danger',
                                                children=[
                                                    html.I(className='fas fa-stop'),
                                                    ' Stop Training',
                                                ],
                                            ),
                                            html.Button(
                                                id='save-model-btn',
                                                className='btn btn-primary',
                                                children=[
                                                    html.I(className='fas fa-save'),
                                                    ' Save Model',
                                                ],
                                            ),
                                            html.Button(
                                                id='load-model-btn',
                                                className='btn btn-secondary',
                                                children=[
                                                    html.I(className='fas fa-upload'),
                                                    ' Load Model',
                                                ],
                                            ),
                                        ],
                                    ),

                                    html.Div(className='agent-hyper-header', children=[
                                        html.I(className='fas fa-sliders'),
                                        html.H4('Hyperparameters'),
                                    ]),

                                    html.Div(
                                        className='agent-hyper-grid',
                                        children=[
                                            html.Div(
                                                className='form-group',
                                                style={'marginBottom': 0},
                                                children=[
                                                    html.Label('Learning Rate'),
                                                    dcc.Input(
                                                        id='learning-rate',
                                                        type='number',
                                                        value=0.001,
                                                        step=0.0001,
                                                        min=0.0001,
                                                        max=0.1,
                                                        className='input-field',
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className='form-group',
                                                style={'marginBottom': 0},
                                                children=[
                                                    html.Label('Discount Factor (\u03b3)'),
                                                    dcc.Input(
                                                        id='discount-factor',
                                                        type='number',
                                                        value=0.99,
                                                        step=0.01,
                                                        min=0.5,
                                                        max=1.0,
                                                        className='input-field',
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className='form-group',
                                                style={'marginBottom': 0},
                                                children=[
                                                    html.Label('Batch Size'),
                                                    dcc.Input(
                                                        id='batch-size',
                                                        type='number',
                                                        value=32,
                                                        step=1,
                                                        min=1,
                                                        max=256,
                                                        className='input-field',
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className='form-group',
                                                style={'marginBottom': 0},
                                                children=[
                                                    html.Label('Target Update Freq'),
                                                    dcc.Input(
                                                        id='target-update',
                                                        type='number',
                                                        value=10,
                                                        step=1,
                                                        min=1,
                                                        max=100,
                                                        className='input-field',
                                                    ),
                                                ],
                                            ),
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
