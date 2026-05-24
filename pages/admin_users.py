"""
SMARTFLOW — Admin User Management Page
Approval workflows, role assignments, safeguards, and auditing.
"""

import json
from dash import html, dcc, callback, Input, Output, State, ALL, ctx
from flask import session

import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_button, create_section, create_status_badge, create_alert


def layout():
    # Enforce admin role check at layout render time
    if not auth.is_admin():
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
                                    className='alert alert-error',
                                    style={'marginTop': '30px'},
                                    children='Access Denied: You do not have permission to access the administrative panel.'
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        
    users = database.list_users()
    pending_users = [u for u in users if u['status'] == 'pending' or u['role_name'] == 'researcher_pending']
    active_users = [u for u in users if u not in pending_users]
    
    # ── Pending Approvals Section ─────────────────────────────────────
    pending_elements = []
    if not pending_users:
        pending_elements.append(
            html.Div(
                className='empty-state',
                style={'padding': '20px', 'textAlign': 'center', 'color': '#64748b'},
                children='No pending registrations.'
            )
        )
    else:
        pending_rows = []
        for u in pending_users:
            pending_rows.append(
                html.Tr(children=[
                    html.Td(u['full_name']),
                    html.Td(u['username']),
                    html.Td(u['email'] or 'N/A'),
                    html.Td(u['created_at']),
                    html.Td(create_status_badge('pending')),
                    html.Td(children=[
                        html.Button(
                            'Approve',
                            id={'type': 'approve-btn', 'index': u['id']},
                            className='btn btn-success btn-sm',
                            style={'marginRight': '8px'}
                        ),
                        html.Button(
                            'Reject',
                            id={'type': 'reject-btn', 'index': u['id']},
                            className='btn btn-danger btn-sm'
                        )
                    ])
                ])
            )
        
        pending_elements.append(
            html.Table(
                className='data-table',
                children=[
                    html.Thead(children=[
                        html.Tr(children=[
                            html.Th('Full Name'),
                            html.Th('Username'),
                            html.Th('Email'),
                            html.Th('Registered Date'),
                            html.Th('Status'),
                            html.Th('Actions')
                        ])
                    ]),
                    html.Tbody(children=pending_rows)
                ]
            )
        )
        
    # ── Registered Users Section ──────────────────────────────────────
    registered_rows = []
    current_user_id = session.get('user_id')
    for u in active_users:
        is_self = (u['id'] == current_user_id)
        role_label = u['role_name'].upper()
        
        actions = []
        # Activate/Deactivate actions
        if u['status'] == 'active':
            if not (u['role_name'] == 'admin' and database.count_active_admins() <= 1):
                actions.append(
                    html.Button(
                        'Deactivate',
                        id={'type': 'deactivate-btn', 'index': u['id']},
                        className='btn btn-warning btn-sm',
                        style={'marginRight': '8px'}
                    )
                )
        else:
            actions.append(
                html.Button(
                    'Activate',
                    id={'type': 'activate-btn', 'index': u['id']},
                    className='btn btn-success btn-sm',
                    style={'marginRight': '8px'}
                )
            )
            
        # Promote action
        if u['role_name'] != 'admin':
            actions.append(
                html.Button(
                    'Promote to Admin',
                    id={'type': 'promote-btn', 'index': u['id']},
                    className='btn btn-secondary btn-sm',
                    style={'marginRight': '8px'}
                )
            )
            
        # Delete action (cannot delete self)
        if not is_self:
            actions.append(
                html.Button(
                    'Delete',
                    id={'type': 'delete-btn', 'index': u['id']},
                    className='btn btn-danger btn-sm'
                )
            )
            
        registered_rows.append(
            html.Tr(children=[
                html.Td(u['full_name'] + (' (You)' if is_self else '')),
                html.Td(u['username']),
                html.Td(u['email'] or 'N/A'),
                html.Td(role_label),
                html.Td(create_status_badge(u['status'])),
                html.Td(u['last_login_at'] or 'Never'),
                html.Td(children=actions)
            ])
        )
        
    registered_elements = [
        html.Table(
            className='data-table',
            children=[
                html.Thead(children=[
                    html.Tr(children=[
                        html.Th('Full Name'),
                        html.Th('Username'),
                        html.Th('Email'),
                        html.Th('Role'),
                        html.Th('Status'),
                        html.Th('Last Login'),
                        html.Th('Actions')
                    ])
                ]),
                html.Tbody(children=registered_rows)
            ]
        )
    ]
    
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
                                    html.H1(children='User Management'),
                                    html.P(children='Approve registration workflows, assign system access permissions, and manage user accounts.'),
                                ]
                            ),
                            
                            html.Div(
                                id='admin-users-alert',
                                className='alert alert-info hidden',
                                children=''
                            ),
                            
                            html.Div(style={'marginBottom': '30px'}, children=[
                                create_section(
                                    title='Pending Registrations',
                                    icon='fas fa-user-plus',
                                    children=pending_elements
                                )
                            ]),
                            
                            html.Div(children=[
                                create_section(
                                    title='Registered System Users',
                                    icon='fas fa-users',
                                    children=registered_elements
                                )
                            ]),
                            dcc.Location(id='admin-users-redirect', refresh=True)
                        ]
                    )
                ]
            )
        ]
    )


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
    
    # Verify the current user is still authorized as admin
    if not auth.is_admin():
        return 'Access Denied: Administrative action not authorized.', 'alert alert-error', '/login'
        
    # Get details of the target user
    user = database.get_user_by_id(target_user_id)
    if not user:
        return 'Target user not found.', 'alert alert-error', None
        
    # Handle Approve
    if action_type == 'approve-btn':
        database.update_user(target_user_id, role_id=2, status='active')  # 2 is researcher
        database.log_audit_event(
            user_id=current_admin_id,
            action='approve_user',
            target='users',
            details=f"Admin {current_admin_username} approved registration for user '{user['username']}'"
        )
        return f"User '{user['username']}' approved successfully.", 'alert alert-success', '/admin/users'
        
    # Handle Reject (Delete pending user)
    elif action_type == 'reject-btn':
        database.delete_user(target_user_id)
        database.log_audit_event(
            user_id=current_admin_id,
            action='reject_user',
            target='users',
            details=f"Admin {current_admin_username} rejected and deleted pending user '{user['username']}'"
        )
        return f"Pending user '{user['username']}' was rejected.", 'alert alert-success', '/admin/users'
        
    # Handle Activate
    elif action_type == 'activate-btn':
        database.update_user(target_user_id, status='active')
        database.log_audit_event(
            user_id=current_admin_id,
            action='activate_user',
            target='users',
            details=f"Admin {current_admin_username} activated account for user '{user['username']}'"
        )
        return f"User '{user['username']}' activated successfully.", 'alert alert-success', '/admin/users'
        
    # Handle Deactivate
    elif action_type == 'deactivate-btn':
        # Safeguard: cannot deactivate last active admin
        if user['role_name'] == 'admin':
            active_admins = database.count_active_admins()
            if active_admins <= 1:
                return "Safeguard Triggered: Cannot deactivate the last active administrator.", 'alert alert-error', None
                
        database.update_user(target_user_id, status='inactive')
        database.log_audit_event(
            user_id=current_admin_id,
            action='deactivate_user',
            target='users',
            details=f"Admin {current_admin_username} deactivated account for user '{user['username']}'"
        )
        return f"User '{user['username']}' deactivated successfully.", 'alert alert-success', '/admin/users'
        
    # Handle Promote to Admin
    elif action_type == 'promote-btn':
        # Promotion safeguard: promote user MUST write audit log in the same step
        database.update_user(target_user_id, role_id=1)  # 1 is admin
        database.log_audit_event(
            user_id=current_admin_id,
            action='promote_user',
            target='users',
            details=f"Admin {current_admin_username} promoted user '{user['username']}' to Admin role"
        )
        return f"User '{user['username']}' promoted to Admin.", 'alert alert-success', '/admin/users'
        
    # Handle Delete
    elif action_type == 'delete-btn':
        # Safeguard: cannot delete yourself
        if target_user_id == current_admin_id:
            return "Safeguard Triggered: You cannot delete your own account while logged in.", 'alert alert-error', None
            
        # Safeguard: cannot delete last active admin
        if user['role_name'] == 'admin':
            active_admins = database.count_active_admins()
            if active_admins <= 1:
                return "Safeguard Triggered: Cannot delete the last active administrator.", 'alert alert-error', None
                
        database.delete_user(target_user_id)
        database.log_audit_event(
            user_id=current_admin_id,
            action='delete_user',
            target='users',
            details=f"Admin {current_admin_username} permanently deleted user '{user['username']}'"
        )
        return f"User '{user['username']}' permanently deleted.", 'alert alert-success', '/admin/users'
        
    return '', 'alert alert-info hidden', None
