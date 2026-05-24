"""
SMARTFLOW — Login Page
User authentication with username/password.
"""

from dash import html, dcc, callback, Input, Output, State
from flask import session
import auth
import database


def layout():
    return html.Div(
        className='auth-page',
        children=[
            html.Div(
                className='auth-container',
                children=[
                    html.Div(
                        className='auth-header',
                        children=[
                            html.Img(
                                src='/assets/logo.svg',
                                className='auth-logo',
                                alt='SMARTFLOW'
                            ),
                            html.H1(className='auth-title', children='SMARTFLOW'),
                            html.P(
                                className='auth-subtitle',
                                children='AI-Driven Traffic Simulation Platform'
                            ),
                        ]
                    ),
                    
                    html.Div(
                        className='auth-form',
                        children=[
                            html.H2(className='form-title', children='Sign In'),
                            
                            html.Div(
                                id='login-error',
                                className='alert alert-error hidden',
                                children=''
                            ),
                            
                            html.Div(
                                className='form-group',
                                children=[
                                    html.Label(
                                        htmlFor='username-input',
                                        children='Username'
                                    ),
                                    dcc.Input(
                                        id='username-input',
                                        type='text',
                                        placeholder='Enter your username',
                                        className='input-field',
                                        autoComplete='username'
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='form-group',
                                children=[
                                    html.Label(
                                        htmlFor='password-input',
                                        children='Password'
                                    ),
                                    dcc.Input(
                                        id='password-input',
                                        type='password',
                                        placeholder='Enter your password',
                                        className='input-field',
                                        autoComplete='current-password'
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='form-group checkbox-group',
                                children=[
                                    dcc.Checklist(
                                        id='remember-me',
                                        options=[
                                            {'label': ' Remember me', 'value': 'remember'}
                                        ],
                                        value=[],
                                        className='checkbox'
                                    ),
                                ]
                            ),
                            
                            html.Button(
                                id='login-btn',
                                className='btn btn-primary btn-full',
                                children='Sign In'
                            ),
                            
                            html.Div(
                                className='auth-footer',
                                children=[
                                    html.Span(children="Don't have an account? "),
                                    dcc.Link(
                                        href='/register',
                                        children='Create account'
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            dcc.Location(id='login-redirect', refresh=True),
        ]
    )


@callback(
    [Output('login-error', 'children'),
     Output('login-error', 'className'),
     Output('login-redirect', 'pathname')],
    Input('login-btn', 'n_clicks'),
    [State('username-input', 'value'),
     State('password-input', 'value'),
     State('remember-me', 'value')],
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password, remember_me):
    if not n_clicks:
        return '', 'alert alert-error hidden', None
    
    if not username or not password:
        return 'Please enter both username and password', 'alert alert-error', None
    
    user = auth.authenticate(username, password)
    
    if not user:
        database.log_audit_event(
            user_id=None,
            action='login_failed',
            target='auth',
            details=f'Failed login attempt for username: {username}'
        )
        return 'Invalid username or password', 'alert alert-error', None
    
    if user['status'] != 'active':
        return 'Your account is not active. Please contact an administrator.', 'alert alert-error', None
    
    auth.create_session(user)
    
    if remember_me and 'remember' in remember_me:
        session.permanent = True
    
    return '', 'alert alert-error hidden', '/dashboard'
