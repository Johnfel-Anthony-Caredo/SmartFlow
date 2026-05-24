"""
SMARTFLOW — Change Password Page
Forced password change on first login.
"""

from dash import html, dcc, callback, Input, Output, State
from flask import session
import auth
import database
import config


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
                            html.H2(className='form-title', children='Change Password'),
                            html.P(
                                className='form-description',
                                style={'textAlign': 'center', 'color': '#64748b', 'marginBottom': '20px'},
                                children='You are logging in for the first time. For security reasons, please change your default password.'
                            ),
                            
                            html.Div(
                                id='change-password-error',
                                className='alert alert-error hidden',
                                children=''
                            ),
                            
                            html.Div(
                                id='change-password-success',
                                className='alert alert-success hidden',
                                children=''
                            ),
                            
                            html.Div(
                                className='form-group',
                                children=[
                                    html.Label(
                                        htmlFor='current-password-input',
                                        children='Current Password'
                                    ),
                                    dcc.Input(
                                        id='current-password-input',
                                        type='password',
                                        placeholder='Enter current password',
                                        className='input-field',
                                        autoComplete='current-password'
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='form-group',
                                children=[
                                    html.Label(
                                        htmlFor='new-password-input',
                                        children='New Password'
                                    ),
                                    dcc.Input(
                                        id='new-password-input',
                                        type='password',
                                        placeholder='Enter new password',
                                        className='input-field',
                                        autoComplete='new-password'
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='form-group',
                                children=[
                                    html.Label(
                                        htmlFor='confirm-password-input',
                                        children='Confirm New Password'
                                    ),
                                    dcc.Input(
                                        id='confirm-password-input',
                                        type='password',
                                        placeholder='Confirm new password',
                                        className='input-field',
                                        autoComplete='new-password'
                                    ),
                                ]
                            ),
                            
                            html.Button(
                                id='change-password-btn',
                                className='btn btn-primary btn-full',
                                children='Update Password'
                            ),
                            
                            html.Div(
                                className='auth-footer',
                                children=[
                                    dcc.Link(
                                        href='/logout',
                                        children='Cancel and Sign out'
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            dcc.Location(id='change-password-redirect', refresh=True),
        ]
    )


@callback(
    [Output('change-password-error', 'children'),
     Output('change-password-error', 'className'),
     Output('change-password-success', 'children'),
     Output('change-password-success', 'className'),
     Output('change-password-redirect', 'pathname')],
    Input('change-password-btn', 'n_clicks'),
    [State('current-password-input', 'value'),
     State('new-password-input', 'value'),
     State('confirm-password-input', 'value')],
    prevent_initial_call=True
)
def handle_change_password(n_clicks, current_password, new_password, confirm_password):
    if not n_clicks:
        return '', 'alert alert-error hidden', '', 'alert alert-success hidden', None
        
    user_id = session.get('user_id')
    if not user_id:
        return 'Not authenticated', 'alert alert-error', '', 'alert alert-success hidden', '/login'
        
    if not current_password or not new_password or not confirm_password:
        return 'All fields are required', 'alert alert-error', '', 'alert alert-success hidden', None
        
    # Retrieve user from database
    user = database.get_user_by_id(user_id)
    if not user:
        return 'User not found', 'alert alert-error', '', 'alert alert-success hidden', '/login'
        
    # Verify current password
    if not auth.verify_password(current_password, user['password_hash']):
        return 'Current password is incorrect', 'alert alert-error', '', 'alert alert-success hidden', None
        
    # New password matches confirm
    if new_password != confirm_password:
        return 'New passwords do not match', 'alert alert-error', '', 'alert alert-success hidden', None
        
    # Validate strength
    errors = auth.validate_password_strength(new_password)
    if errors:
        return errors[0], 'alert alert-error', '', 'alert alert-success hidden', None
        
    # Safeguard: cannot reuse the default password or the current password
    if new_password == config.DEFAULT_ADMIN_PASSWORD:
        return 'Cannot reuse the default admin bootstrap password', 'alert alert-error', '', 'alert alert-success hidden', None
        
    if new_password == current_password:
        return 'New password must be different from current password', 'alert alert-error', '', 'alert alert-success hidden', None
        
    # Save the new password
    hashed_pwd = auth.hash_password(new_password)
    database.update_user(user_id, password_hash=hashed_pwd, must_change_password=0)
    
    # Update the session flag
    session['must_change_password'] = False
    
    # Write audit log
    database.log_audit_event(
        user_id=user_id,
        action='change_password',
        target='user',
        details=f"User {user['username']} updated their password on first login"
    )
    
    return '', 'alert alert-error hidden', 'Password updated successfully! Redirecting to dashboard...', 'alert alert-success', '/dashboard'
