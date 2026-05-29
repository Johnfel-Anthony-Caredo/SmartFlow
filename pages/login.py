"""
SMARTFLOW — Login Page
User authentication with username/password.
"""

from dash import html, dcc, callback, Input, Output, State
import auth


def _auth_field(input_id, label, placeholder, input_type='text', auto_complete=None, hint=''):
    input_props = {
        'id': input_id,
        'type': input_type,
        'placeholder': placeholder,
        'className': 'input-field',
    }

    if auto_complete:
        input_props['autoComplete'] = auto_complete

    return html.Div(
        className='auth-field form-group',
        children=[
            html.Label(htmlFor=input_id, children=label),
            html.Div(
                className='auth-field-shell',
                children=dcc.Input(**input_props)
            ),
            html.Div(className='auth-field-hint', children=hint),
        ]
    )


def layout():
    return html.Div(
        className='auth-page auth-page-login',
        children=[
            html.Div(
                className='auth-shell auth-shell-login',
                children=[
                    html.Section(
                        className='auth-visual-panel',
                        children=[
                            html.Div(
                                className='auth-visual-nav',
                                children=[
                                    html.Div(
                                        className='auth-brand-lockup',
                                        children=[
                                            html.Img(src='/assets/logo.svg', className='auth-brand-mark', alt='SMARTFLOW'),
                                            html.Div(
                                                children=[
                                                    html.Span('SMARTFLOW', className='auth-brand-name'),
                                                    html.Span('Traffic Intelligence', className='auth-brand-subline'),
                                                ]
                                            ),
                                        ]
                                    ),
                                    dcc.Link(
                                        href='/dashboard',
                                        className='auth-back-link',
                                        children=[
                                            html.Span('Open dashboard'),
                                            html.I(className='fas fa-arrow-right'),
                                        ]
                                    ),
                                ]
                            ),
                            html.Div(
                                className='auth-traffic-scene',
                                children=[
                                    html.Div(className='scene-grid'),
                                    html.Div(className='scene-road scene-road-east-west'),
                                    html.Div(className='scene-road scene-road-north-south'),
                                    html.Div(className='scene-road scene-road-diagonal'),
                                    html.Div(className='scene-intersection-core'),
                                    html.Div(className='scene-crosswalk scene-crosswalk-north'),
                                    html.Div(className='scene-crosswalk scene-crosswalk-east'),
                                    html.Div(className='scene-car scene-car-green'),
                                    html.Div(className='scene-car scene-car-amber'),
                                    html.Div(className='scene-car scene-car-white'),
                                    html.Div(className='scene-signal scene-signal-a'),
                                    html.Div(className='scene-signal scene-signal-b'),
                                    html.Div(className='scene-pulse scene-pulse-one'),
                                    html.Div(className='scene-pulse scene-pulse-two'),
                                ]
                            ),
                            html.Div(
                                className='auth-visual-copy',
                                children=[
                                    html.P(className='auth-kicker', children='Tagum City main intersection'),
                                    html.H2(children='Coordinate live SUMO traffic with confidence.'),
                                    html.P(
                                        children='Monitor queues, signal phases, pedestrians, and emergency priority from one research-grade control room.'
                                    ),
                                ]
                            ),
                            html.Div(
                                className='auth-proof-row',
                                children=[
                                    html.Div(className='auth-proof-pill', children=[html.Span('SUMO'), html.Strong('Connected')]),
                                    html.Div(className='auth-proof-pill', children=[html.Span('TraCI'), html.Strong('Live bridge')]),
                                    html.Div(className='auth-proof-pill', children=[html.Span('RL'), html.Strong('Ready')]),
                                ]
                            ),
                        ]
                    ),
                    html.Section(
                        className='auth-form-panel',
                        children=[
                            html.Div(
                                className='auth-form-card',
                                children=[
                                    html.Div(
                                        className='auth-form-header',
                                        children=[
                                            html.Div(className='auth-form-eyebrow', children='Secure access'),
                                            html.H1(className='auth-form-title', children='Welcome back'),
                                            html.P(
                                                className='auth-form-description',
                                                children='Sign in to continue managing the SmartFlow simulation dashboard.'
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        className='auth-form-content',
                                        children=[
                                            html.Div(
                                                id='login-error',
                                                className='alert alert-error hidden',
                                                children=''
                                            ),
                                            _auth_field(
                                                'username-input',
                                                'Username',
                                                'Enter your username',
                                                auto_complete='username',
                                                hint='Use the account assigned to your SMARTFLOW workspace.'
                                            ),
                                            _auth_field(
                                                'password-input',
                                                'Password',
                                                'Enter your password',
                                                input_type='password',
                                                auto_complete='current-password',
                                                hint='Password is case-sensitive.'
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
    
    if reason == 'inactive':
        return 'Your account has been deactivated. Please contact the system administrator.', 'alert alert-error', None
    
    if reason == 'invalid' or not user:
        return 'Invalid username or password. Please check your credentials and try again.', 'alert alert-error', None
    
    auth.create_session(user)
    
    if user.get('must_change_password'):
        return '', 'alert alert-error hidden', '/change-password'
    
    return '', 'alert alert-error hidden', '/dashboard'
