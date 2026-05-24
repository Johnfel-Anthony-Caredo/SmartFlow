"""
SMARTFLOW — Admin User Management Page
Approval workflows, role assignments, safeguards, and auditing.
"""

from dash import html, dcc, callback, Input, Output, State, ALL, ctx
from flask import session

import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_button, create_section, create_status_badge, create_mini_stat


ROLE_OPTIONS = [
    {'label': 'All Roles', 'value': 'all'},
    {'label': 'Admin', 'value': 'admin'},
    {'label': 'Researcher', 'value': 'researcher'},
    {'label': 'Pending', 'value': 'researcher_pending'},
    {'label': 'Disabled', 'value': 'disabled'},
]

STATUS_OPTIONS = [
    {'label': 'All Statuses', 'value': 'all'},
    {'label': 'Active', 'value': 'active'},
    {'label': 'Inactive', 'value': 'inactive'},
    {'label': 'Pending', 'value': 'pending'},
]


def _role_badge(role_name):
    role = (role_name or '').upper()
    cls = 'status-badge'
    if role == 'ADMIN':
        cls += ' status-error'
    elif role == 'RESEARCHER':
        cls += ' status-active'
    elif role == 'RESEARCHER_PENDING':
        cls += ' status-pending'
    elif role == 'DISABLED':
        cls += ' status-inactive'
    else:
        cls += ' status-inactive'
    return html.Span(role, className=cls)


def _build_pending_table(pending_users):
    if not pending_users:
        return html.Div(className='empty-state', children=[
            html.I(className='fas fa-check-circle'),
            html.P('No pending registrations'),
            html.P('All new accounts have been reviewed and processed.', className='empty-state-hint'),
        ])

    rows = []
    for u in pending_users:
        rows.append(html.Tr([
            html.Td(u['full_name']),
            html.Td(u['username']),
            html.Td(u['email'] or 'N/A'),
            html.Td(u['created_at']),
            html.Td(create_status_badge('pending')),
            html.Td(html.Div(className='actions-cell', children=[
                html.Button('Approve', id={'type': 'approve-btn', 'index': u['id']},
                            className='btn btn-success btn-sm'),
                html.Button('Reject', id={'type': 'reject-btn', 'index': u['id']},
                            className='btn btn-danger btn-sm'),
            ]))
        ]))

    return html.Table(className='data-table', children=[
        html.Thead([html.Tr([
            html.Th('Full Name'), html.Th('Username'), html.Th('Email'),
            html.Th('Registered'), html.Th('Status'), html.Th('Actions')
        ])]),
        html.Tbody(rows)
    ])


def _build_registered_table(users, current_user_id):
    if not users:
        return html.Div(className='empty-state', children=[
            html.I(className='fas fa-users-slash'),
            html.P('No registered users'),
            html.P('No accounts match the current search or filter criteria.', className='empty-state-hint'),
        ])

    rows = []
    for u in users:
        is_self = (u['id'] == current_user_id)
        name_cell = u['full_name'] + (' (You)' if is_self else '')

        actions = []
        if u['status'] == 'active':
            if not (u['role_name'] == 'admin' and database.count_active_admins() <= 1):
                actions.append(html.Button('Deactivate',
                    id={'type': 'deactivate-btn', 'index': u['id']},
                    className='btn btn-warning btn-sm'))
        else:
            actions.append(html.Button('Activate',
                id={'type': 'activate-btn', 'index': u['id']},
                className='btn btn-success btn-sm'))

        if u['role_name'] != 'admin':
            actions.append(html.Button('Promote',
                id={'type': 'promote-btn', 'index': u['id']},
                className='btn btn-secondary btn-sm'))

        if not is_self:
            actions.append(html.Button('Delete',
                id={'type': 'delete-btn', 'index': u['id']},
                className='btn btn-danger btn-sm'))

        rows.append(html.Tr([
            html.Td(name_cell),
            html.Td(u['username']),
            html.Td(u['email'] or 'N/A'),
            html.Td(_role_badge(u['role_name'])),
            html.Td(create_status_badge(u['status'])),
            html.Td(u['last_login_at'] or 'Never'),
            html.Td(html.Div(className='actions-cell', children=actions))
        ]))

    return html.Table(className='data-table', children=[
        html.Thead([html.Tr([
            html.Th('Full Name'), html.Th('Username'), html.Th('Email'),
            html.Th('Role'), html.Th('Status'), html.Th('Last Login'), html.Th('Actions')
        ])]),
        html.Tbody(rows)
    ])


def layout():
    if not auth.is_admin():
        return html.Div(className='app-layout', children=[
            create_header(),
            html.Div(className='app-body', children=[
                create_sidebar(),
                html.Main(className='main-content', children=[
                    html.Div(className='alert alert-error', style={'marginTop': '30px'},
                             children='Access Denied')
                ])
            ])
        ])

    all_users = database.list_users()
    pending = [u for u in all_users if u['status'] == 'pending' or u['role_name'] == 'researcher_pending']
    registered = [u for u in all_users if u not in pending]
    current_user_id = session.get('user_id')
    total = len(all_users)
    active = sum(1 for u in all_users if u['status'] == 'active')
    admins = sum(1 for u in all_users if u['role_name'] == 'admin' and u['status'] == 'active')

    return html.Div(className='app-layout', children=[
        create_header(),
        html.Div(className='app-body', children=[
            create_sidebar(),
            html.Main(className='main-content', children=[
                html.Div(className='page-header', children=[
                    html.H1('User Management'),
                    html.P('Approve registrations, assign roles, and manage user accounts across the platform.'),
                ]),

                html.Div(className='stats-row', children=[
                    create_mini_stat('Total Users', str(total), 'fas fa-users', 'var(--info)'),
                    create_mini_stat('Pending', str(len(pending)), 'fas fa-user-clock', 'var(--warning)'),
                    create_mini_stat('Active', str(active), 'fas fa-user-check', 'var(--success)'),
                    create_mini_stat('Admins', str(admins), 'fas fa-shield-halved', 'var(--error)'),
                ]),

                html.Div(id='admin-users-alert', className='alert alert-info hidden'),

                html.Div(style={'marginBottom': '24px'}, children=[
                    create_section(
                        title='Pending Registrations',
                        subtitle='Review and approve or reject new account requests',
                        icon='fas fa-user-plus',
                        children=[_build_pending_table(pending)]
                    )
                ]),

                html.Div(children=[
                    html.Div(className='section', children=[
                        html.Div(className='section-header', children=[
                            html.I(className='fas fa-users'),
                            html.H3(className='section-title', children=[
                                html.Span('Registered System Users', className='section-title-text'),
                                html.Small('Search, filter, and manage active user accounts', className='section-subtitle'),
                            ]),
                        ]),
                        html.Div(className='filter-toolbar', children=[
                            html.Div(className='filter-group filter-group-wide', children=[
                                html.Label('Search', className='filter-label'),
                                dcc.Input(id='users-search', type='text', placeholder='Name, username, or email...',
                                          className='filter-input', debounce=True),
                            ]),
                            html.Div(className='filter-group', children=[
                                html.Label('Role', className='filter-label'),
                                dcc.Dropdown(id='users-role-filter', options=ROLE_OPTIONS, value='all',
                                             clearable=False, searchable=False,
                                             className='dash-dropdown dropdown-small'),
                            ]),
                            html.Div(className='filter-group', children=[
                                html.Label('Status', className='filter-label'),
                                dcc.Dropdown(id='users-status-filter', options=STATUS_OPTIONS, value='all',
                                             clearable=False, searchable=False,
                                             className='dash-dropdown dropdown-small'),
                            ]),
                            html.Div(className='filter-spacer'),
                            html.Button(
                                id='create-user-btn',
                                className='btn btn-primary btn-sm',
                                children=[html.I(className='fas fa-plus'), html.Span('Create User')]
                            ),
                        ]),
                        html.Div(id='users-table-container', className='section-content', children=[
                            _build_registered_table(registered, current_user_id)
                        ]),
                    ]),
                ]),

                dcc.Location(id='admin-users-redirect', refresh=True),
            ])
        ])
    ])


@callback(
    Output('users-table-container', 'children'),
    [Input('users-search', 'value'),
     Input('users-role-filter', 'value'),
     Input('users-status-filter', 'value')]
)
def filter_users_table(search, role_filter, status_filter):
    current_user_id = session.get('user_id')
    all_users = database.list_users()
    pending = {u['id'] for u in all_users if u['status'] == 'pending' or u['role_name'] == 'researcher_pending'}
    registered = [u for u in all_users if u['id'] not in pending]

    if search:
        q = search.lower()
        registered = [u for u in registered if
                      q in (u['full_name'] or '').lower() or
                      q in (u['username'] or '').lower() or
                      q in (u['email'] or '').lower()]

    if role_filter and role_filter != 'all':
        registered = [u for u in registered if u['role_name'] == role_filter]

    if status_filter and status_filter != 'all':
        registered = [u for u in registered if u['status'] == status_filter]

    return _build_registered_table(registered, current_user_id)


@callback(
    [Output('admin-users-alert', 'children'),
     Output('admin-users-alert', 'className'),
     Output('admin-users-redirect', 'pathname')],
    [Input({'type': 'approve-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'reject-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'activate-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'deactivate-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'promote-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'delete-btn', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def handle_user_actions(approve_clicks, reject_clicks, activate_clicks, deactivate_clicks, promote_clicks, delete_clicks):
    triggered_id = ctx.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict):
        return '', 'alert alert-info hidden', None

    action_type = triggered_id.get('type')
    target_user_id = triggered_id.get('index')
    current_admin_id = session.get('user_id')
    current_admin_username = session.get('username', 'admin')

    if not auth.is_admin():
        return 'Access Denied: Administrative action not authorized.', 'alert alert-error', '/login'

    user = database.get_user_by_id(target_user_id)
    if not user:
        return 'Target user not found.', 'alert alert-error', None

    if action_type == 'approve-btn':
        database.update_user(target_user_id, role_id=2, status='active')
        database.log_audit_event(user_id=current_admin_id, action='approve_user', target='users',
                                 details=f"Admin {current_admin_username} approved registration for user '{user['username']}'")
        return f"User '{user['username']}' approved successfully.", 'alert alert-success', '/admin/users'

    elif action_type == 'reject-btn':
        database.delete_user(target_user_id)
        database.log_audit_event(user_id=current_admin_id, action='reject_user', target='users',
                                 details=f"Admin {current_admin_username} rejected and deleted pending user '{user['username']}'")
        return f"Pending user '{user['username']}' was rejected.", 'alert alert-success', '/admin/users'

    elif action_type == 'activate-btn':
        database.update_user(target_user_id, status='active')
        database.log_audit_event(user_id=current_admin_id, action='activate_user', target='users',
                                 details=f"Admin {current_admin_username} activated account for user '{user['username']}'")
        return f"User '{user['username']}' activated successfully.", 'alert alert-success', '/admin/users'

    elif action_type == 'deactivate-btn':
        if user['role_name'] == 'admin':
            if database.count_active_admins() <= 1:
                return "Safeguard: Cannot deactivate the last active administrator.", 'alert alert-error', None
        database.update_user(target_user_id, status='inactive')
        database.log_audit_event(user_id=current_admin_id, action='deactivate_user', target='users',
                                 details=f"Admin {current_admin_username} deactivated account for user '{user['username']}'")
        return f"User '{user['username']}' deactivated successfully.", 'alert alert-success', '/admin/users'

    elif action_type == 'promote-btn':
        database.update_user(target_user_id, role_id=1)
        database.log_audit_event(user_id=current_admin_id, action='promote_user', target='users',
                                 details=f"Admin {current_admin_username} promoted user '{user['username']}' to Admin role")
        return f"User '{user['username']}' promoted to Admin.", 'alert alert-success', '/admin/users'

    elif action_type == 'delete-btn':
        if target_user_id == current_admin_id:
            return "Safeguard: You cannot delete your own account while logged in.", 'alert alert-error', None
        if user['role_name'] == 'admin':
            if database.count_active_admins() <= 1:
                return "Safeguard: Cannot delete the last active administrator.", 'alert alert-error', None
        database.delete_user(target_user_id)
        database.log_audit_event(user_id=current_admin_id, action='delete_user', target='users',
                                 details=f"Admin {current_admin_username} permanently deleted user '{user['username']}'")
        return f"User '{user['username']}' permanently deleted.", 'alert alert-success', '/admin/users'

    return '', 'alert alert-info hidden', None
