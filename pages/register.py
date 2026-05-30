"""
SMARTFLOW — Register Page
New user registration form.
"""

from dash import html, dcc, callback, Input, Output, State
import auth
import database


def _auth_field(input_id, label, placeholder, input_type='text', auto_complete=None, hint=''):
    input_props = {
        'id': input_id,
        'type': input_type,
        'placeholder': placeholder,
        'className': 'input-field',
    }

    if auto_complete:
        input_props['autoComplete'] = auto_complete

    children = [
        html.Label(htmlFor=input_id, children=label),
        html.Div(
            className='auth-field-shell',
            children=dcc.Input(**input_props)
        )
    ]
    if hint:
        children.append(html.Div(className='auth-field-hint', children=hint))

    return html.Div(
        className='auth-field form-group',
        children=children
    )


def _auth_section(title, children):
    return html.Div(
        className='auth-form-section',
        children=[
            html.Div(className='auth-section-label', children=title),
            html.Div(className='auth-section-fields', children=children),
        ]
    )


def layout():
    return html.Div(
        className='auth-page auth-page-register',
        children=[
            html.Div(
                className='auth-shell auth-shell-register',
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
                                                    html.Span('Research Lab Access', className='auth-brand-subline'),
                                                ]
                                            ),
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
                                    html.P(className='auth-kicker', children='Simulation workspace'),
                                    html.H2(children='Join the team improving adaptive traffic control.'),
                                    html.P(
                                        children='Create an account for scenario experiments, SUMO runs, performance reports, and RL controller analysis.'
                                    ),
                                ]
                            ),
                            html.Div(
                                className='auth-proof-row auth-proof-row-inline',
                                children=[
                                    html.Div(className='auth-proof-inline-item', children=[html.Span('SUMO'), html.Strong('Connected')]),
                                    html.Div(className='auth-proof-inline-item', children=[html.Span('TraCI'), html.Strong('Live bridge')]),
                                    html.Div(className='auth-proof-inline-item', children=[html.Span('RL'), html.Strong('Ready')]),
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
                                            html.Div(className='auth-form-eyebrow', children='Request workspace access'),
                                            html.H1(className='auth-form-title', children='Create account'),
                                            html.P(
                                                className='auth-form-description',
                                                children='Set up your SmartFlow profile. Admins can adjust roles after registration.'
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        className='auth-form-content',
                                        children=[
                                            html.Div(
                                                id='register-error',
                                                className='alert alert-error hidden',
                                                children=''
                                            ),
                                            html.Div(
                                                id='register-success',
                                                className='alert alert-success hidden',
                                                children=''
                                            ),
                                            _auth_section(
                                                'Identity',
                                                [
                                                    html.Div(
                                                        className='form-row',
                                                        children=[
                                                            _auth_field(
                                                                'fullname-input',
                                                                'Full Name',
                                                                'Enter your full name',
                                                                auto_complete='name',
                                                                hint=''
                                                            ),
                                                            _auth_field(
                                                                'email-input',
                                                                'Email',
                                                                'your.email@example.com',
                                                                input_type='email',
                                                                auto_complete='email',
                                                                hint=''
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            _auth_section(
                                                'Account',
                                                [
                                                    _auth_field(
                                                        'reg-username-input',
                                                        'Username',
                                                        'Choose a username',
                                                        auto_complete='username',
                                                        hint=''
                                                    ),
                                                ]
                                            ),
                                            _auth_section(
                                                'Security',
                                                [
                                                    html.Div(
                                                        className='form-row',
                                                        children=[
                                                            _auth_field(
                                                                'reg-password-input',
                                                                'Password',
                                                                'Create a password',
                                                                input_type='password',
                                                                auto_complete='new-password',
                                                                hint='Use a strong password for lab access.'
                                                            ),
                                                            _auth_field(
                                                                'reg-confirm-input',
                                                                'Confirm Password',
                                                                'Confirm your password',
                                                                input_type='password',
                                                                auto_complete='new-password',
                                                                hint='Must match the password above.'
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            html.Button(
                                                id='register-btn',
                                                className='btn btn-primary btn-full',
                                                children='Create Account'
                                            ),
                                            html.Div(
                                                className='auth-footer',
                                                children=[
                                                    html.Span(children='Already have an account? '),
                                                    dcc.Link(
                                                        href='/login',
                                                        children='Sign in'
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
            dcc.Location(id='register-redirect', refresh=True),
        ]
    )


@callback(
    [Output('register-error', 'children'),
     Output('register-error', 'className'),
     Output('register-success', 'children'),
     Output('register-success', 'className'),
     Output('register-redirect', 'pathname')],
    Input('register-btn', 'n_clicks'),
    [State('fullname-input', 'value'),
     State('reg-username-input', 'value'),
     State('reg-password-input', 'value'),
     State('reg-confirm-input', 'value'),
     State('email-input', 'value')],
    prevent_initial_call=True
)
def handle_register(n_clicks, fullname, username, password, confirm, email):
    if not n_clicks:
        return '', 'alert alert-error hidden', '', 'alert alert-success hidden', None
    
    # Validate required fields
    if not fullname or not username or not password or not confirm:
        return 'Please fill in all required fields (full name, username, password).', 'alert alert-error', '', 'alert alert-success hidden', None
    
    # Trim and validate username
    username = username.strip()
    if len(username) < 3:
        return 'Username must be at least 3 characters.', 'alert alert-error', '', 'alert alert-success hidden', None
    
    if not username.replace('_', '').replace('-', '').isalnum():
        return 'Username may only contain letters, numbers, underscores, and hyphens.', 'alert alert-error', '', 'alert alert-success hidden', None
    
    # Password validation
    if password != confirm:
        return 'Passwords do not match.', 'alert alert-error', '', 'alert alert-success hidden', None
    
    password_errors = auth.validate_password_strength(password)
    if password_errors:
        return password_errors[0], 'alert alert-error', '', 'alert alert-success hidden', None
    
    # Check uniqueness
    if database.get_user_by_username(username):
        return 'This username is already taken. Please choose another.', 'alert alert-error', '', 'alert alert-success hidden', None
    
    if email and database.get_user_by_email(email.strip()):
        return 'This email address is already registered.', 'alert alert-error', '', 'alert alert-success hidden', None
    
    try:
        user_role = database.get_role_by_name('user')
        role_id = user_role['id'] if user_role else 2
        
        password_hash = auth.hash_password(password)
        user_id = database.create_user(
            full_name=fullname.strip(),
            username=username,
            email=email.strip() if email else '',
            password_hash=password_hash,
            role_id=role_id,
            status='active'
        )
        
        database.log_audit_event(
            user_id=user_id,
            action='register',
            target='auth',
            details=f"New user registered: '{username}' ({fullname})"
        )
        
        return '', 'alert alert-error hidden', 'Account created successfully. You can now log in.', 'alert alert-success', '/login'
    
    except Exception as e:
        return f"Registration failed. Please try again or contact the administrator.", 'alert alert-error', '', 'alert alert-success hidden', None
