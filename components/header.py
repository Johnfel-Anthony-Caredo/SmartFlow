"""
SMARTFLOW — Header Component
Top navigation bar combining original SMARTFLOW controls (scenario selector,
simulation status, date/time) with the new authenticated user menu (Profile, Logout).
"""

from dash import html, dcc
from flask import session


def create_header():
    user_name = session.get('full_name', 'User')
    user_role = session.get('role', 'User')
    user_initial = user_name[0].upper() if user_name else 'U'

    return html.Header(
        className='app-header',
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

            # ── Right: date/time + user menu ───────────────────────
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
                html.Div(
                    className='user-menu',
                    children=[
                        html.Div(
                            id='user-menu-trigger',
                            className='user-menu-trigger',
                            children=[
                                html.Div(
                                    className='user-avatar',
                                    children=user_initial,
                                ),
                                html.Div(
                                    className='user-info',
                                    children=[
                                        html.Div(
                                            className='user-name',
                                            children=user_name,
                                        ),
                                        html.Div(
                                            className='user-role',
                                            children=user_role.title(),
                                        ),
                                    ],
                                ),
                                html.I(
                                    className='fa-solid fa-chevron-down',
                                    style={'fontSize': '10px',
                                           'color': 'var(--text-muted)'},
                                ),
                            ],
                        ),
                        html.Div(
                            className='user-dropdown',
                            id='user-dropdown',
                            children=[
                                dcc.Link(
                                    className='dropdown-item',
                                    href='/profile',
                                    children=[
                                        html.I(className='fa-solid fa-user'),
                                        html.Span('Profile'),
                                    ],
                                ),
                                html.Div(className='dropdown-divider'),
                                dcc.Link(
                                    className='dropdown-item logout',
                                    href='/logout',
                                    children=[
                                        html.I(
                                            className='fa-solid '
                                            'fa-right-from-bracket',
                                        ),
                                        html.Span('Logout'),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ]),
        ],
    )
