"""
SMARTFLOW — Profile & Settings Page
Manage user settings, landing page, density, and auto-refresh.
"""

from dash import html, dcc, callback, Input, Output, State, ctx
from flask import session
import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_input, create_dropdown, create_button


def layout():
    # If not authenticated, let app.py redirect
    if not auth.is_authenticated():
        return html.Div()
        
    user_id = session.get('user_id')
    user = database.get_user_by_id(user_id)
    if not user:
        return html.Div("User profile not found. Please log in.")
        
    # Get current session preferences or defaults
    refresh_rate = session.get('pref_refresh_rate', '30')
    landing_page = session.get('pref_landing_page', '/dashboard')
    density_pref = session.get('pref_density', 'cozy')
    
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
                                    html.H1(children='Profile & Settings'),
                                    html.P(children='Manage your account information and dashboard preferences.'),
                                ]
                            ),
                            
                            html.Div(
                                id='profile-settings-alert',
                                className='alert alert-info hidden',
                                children=''
                            ),
                            
                            html.Div(
                                style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'},
                                children=[
                                    create_section(
                                        title='Account Information',
                                        icon='fas fa-user',
                                        children=[
                                            html.Div(className='profile-details', children=[
                                                html.Div(style={'marginBottom': '10px'}, children=[
                                                    html.Strong('Full Name: '),
                                                    html.Span(user['full_name'])
                                                ]),
                                                html.Div(style={'marginBottom': '10px'}, children=[
                                                    html.Strong('Username: '),
                                                    html.Span(user['username'])
                                                ]),
                                                html.Div(style={'marginBottom': '10px'}, children=[
                                                    html.Strong('Email: '),
                                                    html.Span(user['email'] or 'None provided')
                                                ]),
                                                html.Div(style={'marginBottom': '10px'}, children=[
                                                    html.Strong('Institution/Dept: '),
                                                    html.Span(user['institution'] or 'N/A')
                                                ]),
                                                html.Div(style={'marginBottom': '15px'}, children=[
                                                    html.Strong('System Role: '),
                                                    html.Span(user['role_name'].upper(), className='status-badge status-active', style={'marginLeft': '5px'})
                                                ]),
                                                dcc.Link(
                                                    create_button('Change Password', className='btn btn-secondary', icon='fas fa-key'),
                                                    href='/change-password'
                                                )
                                            ])
                                        ]
                                    ),
                                    
                                    create_section(
                                        title='Dashboard Preferences',
                                        icon='fas fa-sliders-h',
                                        children=[
                                            html.Div(
                                                className='form-group',
                                                style={'marginBottom': '15px'},
                                                children=[
                                                    html.Label(children='Auto-Refresh Interval (seconds)'),
                                                    create_dropdown(
                                                        id='pref-refresh',
                                                        options=[
                                                            {'label': '10 seconds', 'value': '10'},
                                                            {'label': '30 seconds', 'value': '30'},
                                                            {'label': '60 seconds', 'value': '60'},
                                                            {'label': 'Disabled', 'value': '0'}
                                                        ],
                                                        value=refresh_rate
                                                    )
                                                ]
                                            ),
                                            
                                            html.Div(
                                                className='form-group',
                                                style={'marginBottom': '15px'},
                                                children=[
                                                    html.Label(children='Default Landing Page'),
                                                    create_dropdown(
                                                        id='pref-landing',
                                                        options=[
                                                            {'label': 'Dashboard Overview', 'value': '/dashboard'},
                                                            {'label': 'Simulation Controls', 'value': '/simulation'},
                                                            {'label': 'Scenarios Library', 'value': '/scenarios'}
                                                        ],
                                                        value=landing_page
                                                    )
                                                ]
                                            ),
                                            
                                            html.Div(
                                                className='form-group',
                                                style={'marginBottom': '20px'},
                                                children=[
                                                    html.Label(children='Layout Density'),
                                                    create_dropdown(
                                                        id='pref-density',
                                                        options=[
                                                            {'label': 'Cozy (Default)', 'value': 'cozy'},
                                                            {'label': 'Compact', 'value': 'compact'}
                                                        ],
                                                        value=density_pref
                                                    )
                                                ]
                                            ),
                                            
                                            create_button(
                                                id='save-pref-btn',
                                                text='Save Preferences',
                                                icon='fas fa-check-circle',
                                                className='btn btn-primary'
                                            )
                                        ]
                                    )
                                ]
                            ),
                            dcc.Location(id='profile-settings-redirect', refresh=True)
                        ]
                    )
                ]
            )
        ]
    )


@callback(
    [Output('profile-settings-alert', 'children'),
     Output('profile-settings-alert', 'className'),
     Output('profile-settings-redirect', 'pathname')],
    Input('save-pref-btn', 'n_clicks'),
    [State('pref-refresh', 'value'),
     State('pref-landing', 'value'),
     State('pref-density', 'value')],
    prevent_initial_call=True
)
def handle_save_preferences(n_clicks, refresh, landing, density):
    if not n_clicks:
        return '', 'alert alert-info hidden', None
        
    if not auth.validate_current_session():
        auth.clear_session()
        return 'Session expired. Please log in again.', 'alert alert-error', '/login'
        
    # Save preferences to session
    session['pref_refresh_rate'] = refresh
    session['pref_landing_page'] = landing
    session['pref_density'] = density
    
    # Log audit event
    user_id = session.get('user_id')
    username = session.get('username')
    database.log_audit_event(
        user_id=user_id,
        action='save_preferences',
        target='user_settings',
        details=f"User {username} updated their preferences: Refresh={refresh}s, Landing={landing}, Density={density}"
    )
    
    return 'Preferences saved successfully.', 'alert alert-success', '/profile'
