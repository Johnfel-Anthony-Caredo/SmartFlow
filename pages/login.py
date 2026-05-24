"""
SMARTFLOW — Login Page
User authentication with username/password.
"""

from dash import html, dcc, callback, Input, Output, State
import auth


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
     State('password-input', 'value')],
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not n_clicks:
        return '', 'alert alert-error hidden', None
    
    if not username or not password:
        return 'Please enter both username and password.', 'alert alert-error', None
    
    user, reason = auth.authenticate(username, password)
    
    if reason == 'locked':
        return 'Too many failed attempts. Please wait a few minutes and try again.', 'alert alert-error', None
    
    if reason == 'pending':
        return 'Your account is pending administrator approval. You will be able to log in once an admin activates your account.', 'alert alert-warning', None
    
    if reason == 'disabled':
        return 'Your account has been disabled. Please contact the system administrator.', 'alert alert-error', None
    
    if reason == 'invalid' or not user:
        return 'Invalid username or password. Please check your credentials and try again.', 'alert alert-error', None
    
    auth.create_session(user)
    
    if user.get('must_change_password'):
        return '', 'alert alert-error hidden', '/change-password'
    
    return '', 'alert alert-error hidden', '/dashboard'
