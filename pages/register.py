"""
SMARTFLOW — Register Page
New user registration form.
"""

from dash import html, dcc, callback, Input, Output, State
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
                            html.H2(className='form-title', children='Create Account'),
                            
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
                            
                            html.Div(
                                className='form-group',
                                children=[
                                    html.Label(
                                        htmlFor='fullname-input',
                                        children='Full Name'
                                    ),
                                    dcc.Input(
                                        id='fullname-input',
                                        type='text',
                                        placeholder='Enter your full name',
                                        className='input-field'
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='form-group',
                                children=[
                                    html.Label(
                                        htmlFor='reg-username-input',
                                        children='Username'
                                    ),
                                    dcc.Input(
                                        id='reg-username-input',
                                        type='text',
                                        placeholder='Choose a username',
                                        className='input-field',
                                        autoComplete='username'
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='form-row',
                                children=[
                                    html.Div(
                                        className='form-group',
                                        children=[
                                            html.Label(
                                                htmlFor='reg-password-input',
                                                children='Password'
                                            ),
                                            dcc.Input(
                                                id='reg-password-input',
                                                type='password',
                                                placeholder='Create a password',
                                                className='input-field',
                                                autoComplete='new-password'
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        className='form-group',
                                        children=[
                                            html.Label(
                                                htmlFor='reg-confirm-input',
                                                children='Confirm Password'
                                            ),
                                            dcc.Input(
                                                id='reg-confirm-input',
                                                type='password',
                                                placeholder='Confirm your password',
                                                className='input-field',
                                                autoComplete='new-password'
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='form-group',
                                children=[
                                    html.Label(
                                        htmlFor='email-input',
                                        children='Email'
                                    ),
                                    dcc.Input(
                                        id='email-input',
                                        type='email',
                                        placeholder='your.email@example.com',
                                        className='input-field',
                                        autoComplete='email'
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
        # Researcher pending role
        pending_role = database.get_role_by_name('researcher_pending')
        role_id = pending_role['id'] if pending_role else 3
        
        password_hash = auth.hash_password(password)
        user_id = database.create_user(
            full_name=fullname.strip(),
            username=username,
            email=email.strip() if email else '',
            password_hash=password_hash,
            role_id=role_id,
            status='pending'
        )
        
        database.log_audit_event(
            user_id=user_id,
            action='register',
            target='auth',
            details=f"New user registered: '{username}' ({fullname}) — awaiting admin approval"
        )
        
        return '', 'alert alert-error hidden', 'Account created successfully. Your registration is pending administrator approval. Once approved, you will be able to log in.', 'alert alert-success', '/login'
    
    except Exception as e:
        return f"Registration failed. Please try again or contact the administrator.", 'alert alert-error', '', 'alert alert-success hidden', None
