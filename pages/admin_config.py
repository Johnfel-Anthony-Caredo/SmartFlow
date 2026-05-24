"""
SMARTFLOW — Admin System Configuration Page
Manage system-wide parameters (session timeouts, registration policies).
"""

from dash import html, dcc, callback, Input, Output, State, ctx
from flask import session
import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_input, create_dropdown, create_button


def _section_group(icon, title, children):
    return html.Div(className='section-group', children=[
        html.Div(className='section-group-header', children=[
            html.I(className=icon),
            html.Span(title, className='section-group-title'),
        ]),
        html.Div(className='section-group-body', children=children),
    ])


def _helper(text):
    return html.Div(text, className='helper-text')


def layout():
    if not auth.is_admin():
        return html.Div(className='app-layout', children=[
            create_header(),
            html.Div(className='app-body', children=[
                create_sidebar(),
                html.Main(className='main-content', children=[
                    html.Div(className='alert alert-error', style={'marginTop': '30px'},
                             children='Access Denied: You do not have permission to access the administrative panel.')
                ])
            ])
        ])

    reg_mode = database.get_setting('registration_mode', 'approval-only')
    sess_timeout = database.get_setting('session_timeout', '3600')
    min_pw_len = database.get_setting('min_password_length', '8')
    app_name = database.get_setting('app_name', 'SmartFlow Traffic')
    maintenance_mode = database.get_setting('maintenance_mode', '0')

    return html.Div(className='app-layout', children=[
        create_header(),
        html.Div(className='app-body', children=[
            create_sidebar(),
            html.Main(className='main-content', children=[
                html.Div(className='page-header', children=[
                    html.H1('System Configuration'),
                    html.P('Manage platform identity, authentication policies, session security, and maintenance states.'),
                ]),

                html.Div(id='admin-config-alert', className='alert alert-info hidden'),

                create_section(
                    title='Global Settings',
                    subtitle='Platform name, authentication policies, and maintenance states',
                    icon='fas fa-sliders-h',
                    children=[
                        _section_group('fas fa-building', 'Platform', [
                            html.Div(className='form-group', children=[
                                html.Label('Platform Name'),
                                create_input(id='config-app-name', value=app_name, placeholder='Enter platform name'),
                                _helper('Displayed in the browser tab, header bar, and system notifications.'),
                            ]),
                        ]),

                        _section_group('fas fa-shield-halved', 'Authentication & User Access', [
                            html.Div(className='form-group', children=[
                                html.Label('Registration Mode'),
                                create_dropdown(id='config-reg-mode', options=[
                                    {'label': 'Approval-Only (Default)', 'value': 'approval-only'},
                                    {'label': 'Open Registration', 'value': 'open'},
                                ], value=reg_mode),
                                _helper('Approval-only requires an admin to activate new accounts. Open allows immediate login after signup.'),
                            ]),
                            html.Div(className='form-row', children=[
                                html.Div(className='form-group', children=[
                                    html.Label('Minimum Password Length'),
                                    create_input(id='config-min-pwd-len', type='number',
                                                 value=min_pw_len, placeholder='e.g., 8'),
                                    _helper('Applies to new accounts and password changes. Range: 6–30.'),
                                ]),
                            ]),
                        ]),

                        _section_group('fas fa-clock', 'Session & Security', [
                            html.Div(className='form-row', children=[
                                html.Div(className='form-group', children=[
                                    html.Label('Session Timeout (seconds)'),
                                    create_input(id='config-sess-timeout', type='number',
                                                 value=sess_timeout, placeholder='e.g., 3600'),
                                    _helper('Users are logged out after this period of inactivity. Minimum: 60 seconds.'),
                                ]),
                            ]),
                        ]),

                        _section_group('fas fa-tools', 'Maintenance', [
                            html.Div(className='form-group', children=[
                                html.Label('Maintenance Mode'),
                                create_dropdown(id='config-maintenance', options=[
                                    {'label': 'Disabled — Platform is live and accessible', 'value': '0'},
                                    {'label': 'Enabled — Show maintenance banner', 'value': '1'},
                                ], value=maintenance_mode),
                                _helper('When enabled, non-admin users see a maintenance notice. Admins retain full access.'),
                            ]),
                        ]),

                        html.Div(className='config-save-footer', children=[
                            create_button(id='save-config-btn', text='Save Configuration',
                                          icon='fas fa-save', className='btn btn-primary')
                        ]),
                    ]
                ),

                dcc.Location(id='admin-config-redirect', refresh=True),
            ])
        ])
    ])


@callback(
    [Output('admin-config-alert', 'children'),
     Output('admin-config-alert', 'className'),
     Output('admin-config-redirect', 'pathname')],
    Input('save-config-btn', 'n_clicks'),
    [State('config-app-name', 'value'),
     State('config-reg-mode', 'value'),
     State('config-sess-timeout', 'value'),
     State('config-min-pwd-len', 'value'),
     State('config-maintenance', 'value')],
    prevent_initial_call=True
)
def handle_save_config(n_clicks, app_name, reg_mode, sess_timeout, min_pwd_len, maintenance):
    if not n_clicks:
        return '', 'alert alert-info hidden', None

    if not auth.is_admin():
        return 'Access Denied: Administrative action not authorized.', 'alert alert-error', '/login'

    try:
        sess_timeout_int = int(sess_timeout)
        if sess_timeout_int < 60:
            return 'Session timeout must be at least 60 seconds.', 'alert alert-error', None
    except ValueError:
        return 'Session timeout must be a valid integer.', 'alert alert-error', None

    try:
        min_pwd_len_int = int(min_pwd_len)
        if min_pwd_len_int < 6 or min_pwd_len_int > 30:
            return 'Minimum password length must be between 6 and 30.', 'alert alert-error', None
    except ValueError:
        return 'Minimum password length must be a valid integer.', 'alert alert-error', None

    if not app_name:
        return 'Platform name cannot be empty.', 'alert alert-error', None

    database.set_setting('app_name', app_name)
    database.set_setting('registration_mode', reg_mode)
    database.set_setting('session_timeout', str(sess_timeout_int))
    database.set_setting('min_password_length', str(min_pwd_len_int))
    database.set_setting('maintenance_mode', maintenance)

    current_admin_id = session.get('user_id')
    current_admin_username = session.get('username')
    database.log_audit_event(user_id=current_admin_id, action='update_config', target='system_settings',
                             details=f"Admin {current_admin_username} updated system config: "
                                     f"Name={app_name}, RegMode={reg_mode}, SessionTimeout={sess_timeout_int}s, "
                                     f"MinPwLen={min_pwd_len_int}, Maintenance={maintenance}")

    return 'Configuration saved successfully.', 'alert alert-success', '/admin/config'
