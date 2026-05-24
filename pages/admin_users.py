"""
SMARTFLOW — Admin User Management Page
Phoenix-inspired dark enterprise dashboard for user administration.
"""

import json
import secrets
from datetime import datetime
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
from flask import session

import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_status_badge


# ─── Helpers ───────────────────────────────────────────────────────

AVATAR_COLORS = ['green', 'blue', 'purple', 'amber', 'gray']


def _avatar_color(username):
    return AVATAR_COLORS[abs(hash(username or '')) % len(AVATAR_COLORS)]


def _pill_badge(label, variant):
    css_map = {
        'admin': 'pill-admin', 'researcher': 'pill-researcher',
        'researcher_pending': 'pill-pending', 'disabled': 'pill-disabled',
        'active': 'pill-status-active', 'inactive': 'pill-status-inactive',
        'pending': 'pill-status-pending',
    }
    cls = css_map.get(variant, '')
    return html.Span(label.replace('_', ' ').title(), className=f'pill-badge {cls}')


def _role_badge(role_name):
    return _pill_badge(role_name or '', (role_name or '').lower())


def _status_badge(status):
    return _pill_badge(status or '', (status or '').lower())


def _initials(name):
    parts = (name or '').strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return (name or 'U')[0].upper()


def _fmt_date(iso_str):
    if not iso_str:
        return None
    try:
        d = datetime.fromisoformat(iso_str)
        return d.strftime('%b %d, %Y  %I:%M %p')
    except (ValueError, TypeError):
        return iso_str


def _build_kpi_row(total, pending, active, admins):
    kpis = [
        ('fas fa-users', str(total), 'Total Users', 'var(--info)'),
        ('fas fa-user-clock', str(pending), 'Pending Registrations', 'var(--warning)'),
        ('fas fa-user-check', str(active), 'Active Users', 'var(--success)'),
        ('fas fa-shield-halved', str(admins), 'Admin Users', 'var(--purple)'),
    ]
    return html.Div(className='kpi-row-4', children=[
        html.Div(className='kpi-card-compact', children=[
            html.Div(className='kpi-icon-wrap',
                     style={'background': f'color-mix(in srgb, {color} 12%, transparent)',
                            'border': f'1px solid color-mix(in srgb, {color} 20%, transparent)'},
                     children=[html.I(className=icon, style={'color': color})]),
            html.Div(className='kpi-content', children=[
                html.Span(value, className='kpi-value'),
                html.Span(label, className='kpi-label'),
            ]),
        ]) for icon, value, label, color in kpis
    ])


def _build_pending_list(pending_users):
    if not pending_users:
        return html.Div(className='empty-state', children=[
            html.I(className='fas fa-check-circle'),
            html.P('All Clear'),
            html.P('No pending registrations. All accounts have been reviewed.',
                   className='empty-state-hint'),
        ])

    cards = []
    for u in pending_users:
        created = u.get('created_at', '')
        try:
            d = datetime.fromisoformat(created)
            date_str = d.strftime('%b %d, %Y')
        except (ValueError, TypeError):
            date_str = created or 'N/A'

        cards.append(
            html.Div(className='pending-card', children=[
                html.Div(
                    className=f'pending-avatar amber',
                    children=_initials(u['full_name']),
                ),
                html.Div(className='pending-info', children=[
                    html.Span(u['full_name'], className='pending-name'),
                    html.Div(className='pending-detail', children=[
                        html.Span([html.I(className='fas fa-user'), u['username']]),
                        html.Span([html.I(className='fas fa-envelope'), u.get('email', 'N/A')]),
                        html.Span([html.I(className='fas fa-calendar'), date_str]),
                    ]),
                ]),
                html.Div(className='pending-actions', children=[
                    html.Button('Approve',
                                id={'type': 'approve-btn', 'index': u['id']},
                                className='btn btn-success btn-sm'),
                    html.Button('Reject',
                                id={'type': 'reject-btn', 'index': u['id']},
                                className='btn btn-danger btn-sm'),
                    html.Button([html.I(className='fas fa-eye')],
                                id={'type': 'view-detail-btn', 'index': f"pending:{u['id']}"},
                                className='btn btn-secondary btn-sm',
                                title='View Details'),
                ]),
            ])
        )
    return html.Div(className='pending-grid', children=cards)


def _user_cell(user, is_self=False):
    color = _avatar_color(user['username'])
    name = user['full_name'] + (' (You)' if is_self else '')
    return html.Div(className='user-cell', children=[
        html.Div(className=f'user-cell-avatar {color}',
                 children=_initials(user['full_name'])),
        html.Div(children=[
            html.Div(name, className='user-cell-name'),
            html.Div(user['username'], className='user-cell-sub'),
        ]),
    ])


def _last_login_cell(last_login_at):
    if not last_login_at:
        return html.Span('Never', className='last-login-cell')
    try:
        d = datetime.fromisoformat(last_login_at)
        now = datetime.now()
        if d.date() == now.date():
            val = d.strftime('Today, %I:%M %p')
        else:
            val = d.strftime('%b %d, %Y')
        return html.Span(val, className='last-login-cell')
    except (ValueError, TypeError):
        return html.Span(last_login_at, className='last-login-cell')


def _build_registered_table(users, current_user_id):
    if not users:
        return html.Div(className='empty-state', children=[
            html.I(className='fas fa-users-slash'),
            html.P('No users found'),
            html.P('Try adjusting your search or filter criteria.',
                   className='empty-state-hint'),
        ])

    rows = []
    for u in users:
        is_self = (u['id'] == current_user_id)
        actions = [
            html.Button(html.I(className='fas fa-eye'),
                        id={'type': 'view-user-btn', 'index': u['id']},
                        className='icon-btn-sm edit', title='View Details'),
        ]
        if u['status'] == 'active':
            safeg = u['role_name'] == 'admin' and database.count_active_admins() <= 1
            if not safeg:
                actions.append(html.Button(html.I(className='fas fa-pause'),
                                           id={'type': 'deactivate-btn', 'index': u['id']},
                                           className='icon-btn-sm deactivate',
                                           title='Deactivate'))
        else:
            actions.append(html.Button(html.I(className='fas fa-play'),
                                       id={'type': 'activate-btn', 'index': u['id']},
                                       className='icon-btn-sm activate',
                                       title='Activate'))

        if u['role_name'] != 'admin':
            actions.append(html.Button(html.I(className='fas fa-arrow-up'),
                                       id={'type': 'promote-btn', 'index': u['id']},
                                       className='icon-btn-sm edit',
                                       title='Promote to Admin'))

        if not is_self:
            actions.append(html.Button(html.I(className='fas fa-key'),
                                       id={'type': 'reset-pw-btn', 'index': u['id']},
                                       className='icon-btn-sm reset-pw',
                                       title='Reset Password'))

        if not is_self:
            actions.append(html.Div(className='action-sep'))
            actions.append(html.Button(html.I(className='fas fa-trash'),
                                       id={'type': 'delete-btn', 'index': u['id']},
                                       className='icon-btn-sm danger',
                                       title='Delete User'))

        rows.append(html.Tr([
            html.Td(_user_cell(u, is_self)),
            html.Td(u['email'] or 'N/A'),
            html.Td(_role_badge(u['role_name'])),
            html.Td(_status_badge(u['status'])),
            html.Td(_last_login_cell(u.get('last_login_at'))),
            html.Td(html.Div(className='actions-inline', children=actions)),
        ]))

    return html.Div(className='table-scroll users-table', children=[
        html.Table(className='data-table', children=[
            html.Thead(html.Tr([
                html.Th('User'),
                html.Th('Email'),
                html.Th('Role'),
                html.Th('Status'),
                html.Th('Last Login'),
                html.Th('Actions'),
            ])),
            html.Tbody(rows),
        ])
    ])


# ─── Layout ─────────────────────────────────────────────────────────

def layout():
    if not auth.is_admin():
        return html.Div(className='app-layout', children=[
            create_header(),
            html.Div(className='app-body', children=[
                create_sidebar(),
                html.Main(className='main-content', children=[
                    html.Div(className='alert alert-error', style={'marginTop': '30px'},
                             children='Access Denied: You do not have permission.'),
                ]),
            ]),
        ])

    all_users = database.list_users()
    pending = [u for u in all_users
               if u['status'] == 'pending' or u['role_name'] == 'researcher_pending']
    registered = [u for u in all_users if u not in pending]
    current_user_id = session.get('user_id')
    total = len(all_users)
    active = sum(1 for u in all_users if u['status'] == 'active')
    admins = sum(1 for u in all_users
                 if u['role_name'] == 'admin' and u['status'] == 'active')

    return html.Div(className='app-layout', children=[
        create_header(),
        html.Div(className='app-body', children=[
            create_sidebar(),

            html.Main(className='main-content', children=[
                # ── Page Header ──
                html.Div(className='page-header', children=[
                    html.H1('User Management'),
                    html.P('Approve new registrations, assign roles, manage accounts, and '
                           'review user activity across the SMARTFLOW platform.'),
                ]),

                # ── Alert Banner (hidden by default, shown only by JS after action) ──
                html.Div(id='admin-users-alert',
                         className='alert alert-info hidden',
                         children='', style={'display': 'none'}),

                # ── KPI Row ──
                _build_kpi_row(total, len(pending), active, admins),

                # ── Registered Users (primary, table-first) ──
                html.Div(children=[
                    html.Div(className='section', children=[
                        html.Div(className='section-header', children=[
                            html.I(className='fas fa-users'),
                            html.H3(className='section-title', children=[
                                html.Span('Registered Users'),
                                html.Small('Search, filter, and manage all platform accounts',
                                           className='section-subtitle'),
                            ]),
                        ]),
                        html.Div(className='filter-toolbar', children=[
                            html.Div(className='filter-group filter-group-wide', children=[
                                html.Label('Search', className='filter-label'),
                                dcc.Input(id='users-search', type='text',
                                          placeholder='Name, username, or email...',
                                          className='filter-input', debounce=True),
                            ]),
                            html.Div(className='filter-group', children=[
                                html.Label('Role', className='filter-label'),
                                dcc.Dropdown(
                                    id='users-role-filter',
                                    options=[
                                        {'label': 'All Roles', 'value': 'all'},
                                        {'label': 'Admin', 'value': 'admin'},
                                        {'label': 'Researcher', 'value': 'researcher'},
                                        {'label': 'Pending', 'value': 'researcher_pending'},
                                        {'label': 'Disabled', 'value': 'disabled'},
                                    ],
                                    value='all', clearable=False, searchable=False,
                                    className='dash-dropdown dropdown-small'),
                            ]),
                            html.Div(className='filter-group', children=[
                                html.Label('Status', className='filter-label'),
                                dcc.Dropdown(
                                    id='users-status-filter',
                                    options=[
                                        {'label': 'All Statuses', 'value': 'all'},
                                        {'label': 'Active', 'value': 'active'},
                                        {'label': 'Inactive', 'value': 'inactive'},
                                        {'label': 'Pending', 'value': 'pending'},
                                    ],
                                    value='all', clearable=False, searchable=False,
                                    className='dash-dropdown dropdown-small'),
                            ]),
                            html.Div(className='filter-spacer'),
                        ]),
                        html.Div(id='users-table-container', className='section-content',
                                 children=[_build_registered_table(registered, current_user_id)]),
                    ]),
                ]),

                # ── Pending Registrations (at the bottom) ──
                html.Div(id='pending-section', style={'marginTop': '20px'}, children=[
                    html.Div(className='section', children=[
                        html.Div(className='section-header', children=[
                            html.I(className='fas fa-user-plus'),
                            html.H3(className='section-title', children=[
                                html.Span('Pending Registrations'),
                                html.Small(f' {len(pending)} request{"s" if len(pending) != 1 else ""} '
                                           'awaiting review',
                                           className='section-subtitle'),
                            ]),
                        ]),
                        html.Div(className='section-content',
                                 children=[_build_pending_list(pending)]),
                    ]),
                ]),

                # ── Hidden stores ──
                dcc.Store(id='selected-user-id', data=None),
            ]),
        ]),

        # ── User Details Modal ──
        html.Div(id='user-modal-overlay', className='modal-overlay hidden', children=[
            html.Div(className='modal', style={'width': 'min(520px, 92vw)'}, children=[
                html.Div(className='modal-header', children=[
                    html.H2(id='user-modal-title', children='User Details'),
                    html.Button('×', id='user-modal-close', className='modal-close'),
                ]),
                html.Div(id='user-modal-body', className='modal-body'),
            ]),
        ]),
    ])


# ─── Callbacks ──────────────────────────────────────────────────────

@callback(
    Output('users-table-container', 'children'),
    [Input('users-search', 'value'),
     Input('users-role-filter', 'value'),
     Input('users-status-filter', 'value')],
)
def filter_users_table(search, role_filter, status_filter):
    current_user_id = session.get('user_id')
    all_users = database.list_users()
    pending_ids = {u['id'] for u in all_users
                   if u['status'] == 'pending' or u['role_name'] == 'researcher_pending'}
    registered = [u for u in all_users if u['id'] not in pending_ids]

    if search:
        q = search.lower().strip()
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
     Output('admin-users-alert', 'style')],
    [Input({'type': 'approve-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'reject-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'activate-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'deactivate-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'promote-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'delete-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'reset-pw-btn', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True,
)
def handle_user_actions(approve_clicks, reject_clicks, activate_clicks,
                         deactivate_clicks, promote_clicks, delete_clicks,
                         reset_pw_clicks):
    triggered_id = ctx.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict):
        return no_update, no_update, no_update

    # Guard: only act if the button was actually clicked (n_clicks > 0)
    triggered_prop = ctx.triggered[0] if ctx.triggered else None
    if not triggered_prop or not triggered_prop.get('value'):
        return no_update, no_update, no_update

    action_type = triggered_id.get('type')
    target_user_id = triggered_id.get('index')
    current_admin_id = session.get('user_id')
    current_admin_username = session.get('username', 'admin')

    if not auth.is_admin():
        return ('Access Denied: Administrative action not authorized.',
                'alert alert-error', {})

    user = database.get_user_by_id(target_user_id)
    if not user:
        return ('Target user not found.', 'alert alert-error', {})

    if action_type == 'approve-btn':
        database.update_user(target_user_id, role_id=2, status='active')
        database.log_audit_event(
            user_id=current_admin_id, action='approve_user', target='users',
            details=f"Admin {current_admin_username} approved registration for "
                    f"user '{user['username']}'")
        return (f"User '{user['username']}' approved successfully.",
                'alert alert-success', {})

    elif action_type == 'reject-btn':
        database.delete_user(target_user_id)
        database.log_audit_event(
            user_id=current_admin_id, action='reject_user', target='users',
            details=f"Admin {current_admin_username} rejected and deleted pending "
                    f"user '{user['username']}'")
        return (f"Pending user '{user['username']}' was rejected.",
                'alert alert-success', {})

    elif action_type == 'activate-btn':
        database.update_user(target_user_id, status='active')
        database.log_audit_event(
            user_id=current_admin_id, action='activate_user', target='users',
            details=f"Admin {current_admin_username} activated account for "
                    f"user '{user['username']}'")
        return (f"User '{user['username']}' activated successfully.",
                'alert alert-success', {})

    elif action_type == 'deactivate-btn':
        if user['role_name'] == 'admin' and database.count_active_admins() <= 1:
            return ("Safeguard: Cannot deactivate the last active administrator.",
                    'alert alert-error', {})
        database.update_user(target_user_id, status='inactive')
        database.log_audit_event(
            user_id=current_admin_id, action='deactivate_user', target='users',
            details=f"Admin {current_admin_username} deactivated account for "
                    f"user '{user['username']}'")
        return (f"User '{user['username']}' deactivated successfully.",
                'alert alert-success', {})

    elif action_type == 'promote-btn':
        database.update_user(target_user_id, role_id=1)
        database.log_audit_event(
            user_id=current_admin_id, action='promote_user', target='users',
            details=f"Admin {current_admin_username} promoted user '{user['username']}' "
                    f"to Admin role")
        return (f"User '{user['username']}' promoted to Admin.",
                'alert alert-success', {})

    elif action_type == 'delete-btn':
        if target_user_id == current_admin_id:
            return ("Safeguard: You cannot delete your own account while logged in.",
                    'alert alert-error', {})
        if user['role_name'] == 'admin' and database.count_active_admins() <= 1:
            return ("Safeguard: Cannot delete the last active administrator.",
                    'alert alert-error', {})
        database.delete_user(target_user_id)
        database.log_audit_event(
            user_id=current_admin_id, action='delete_user', target='users',
            details=f"Admin {current_admin_username} permanently deleted user "
                    f"'{user['username']}'")
        return (f"User '{user['username']}' permanently deleted.",
                'alert alert-success', {})

    elif action_type == 'reset-pw-btn':
        new_pw = secrets.token_urlsafe(12)
        hashed = auth.hash_password(new_pw)
        database.update_user(target_user_id, password_hash=hashed,
                             must_change_password=1)
        database.log_audit_event(
            user_id=current_admin_id, action='reset_password', target='users',
            details=f"Admin {current_admin_username} reset password for user "
                    f"'{user['username']}'")
        return (f"Password reset for '{user['username']}'. New temporary password: "
                f"`{new_pw}`. User must change on next login.",
                'alert alert-success', {})

    return no_update, no_update, no_update


@callback(
    [Output('selected-user-id', 'data'),
     Output('user-modal-overlay', 'className')],
    [Input({'type': 'view-user-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'view-detail-btn', 'index': ALL}, 'n_clicks'),
     Input('user-modal-close', 'n_clicks')],
    prevent_initial_call=True,
)
def toggle_user_modal(view_clicks, view_detail_clicks, close_click):
    triggered_id = ctx.triggered_id

    # Guard: if triggered by a pattern-match button, verify it was actually clicked
    triggered_prop = ctx.triggered[0] if ctx.triggered else None
    if not triggered_prop or not triggered_prop.get('value'):
        return no_update, no_update

    # Close trigger
    if triggered_id == 'user-modal-close':
        return None, 'modal-overlay hidden'

    # Open from table row
    if isinstance(triggered_id, dict) and triggered_id.get('type') == 'view-user-btn':
        user_id = triggered_id.get('index')
        return user_id, 'modal-overlay'

    # Open from pending card
    if isinstance(triggered_id, dict) and triggered_id.get('type') == 'view-detail-btn':
        prefix = triggered_id.get('index', '')
        if prefix.startswith('pending:'):
            user_id = int(prefix.split(':')[1])
            return user_id, 'modal-overlay'

    return no_update, no_update


@callback(
    [Output('user-modal-title', 'children'),
     Output('user-modal-body', 'children')],
    Input('selected-user-id', 'data'),
    prevent_initial_call=True,
)
def populate_user_modal(user_id):
    if user_id is None:
        return 'User Details', ''

    user = database.get_user_by_id(user_id)
    if not user:
        return 'User Not Found', html.Div(className='drawer-empty', children=[
            html.I(className='fas fa-exclamation-triangle'),
            html.P('This user no longer exists.'),
        ])

    activity = database.get_user_activity_summary(user_id)
    color = _avatar_color(user['username'])
    name = user['full_name'] or ''

    content = html.Div(children=[
        # Profile header
        html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '14px',
                        'marginBottom': '16px'}, children=[
            html.Div(className=f'user-cell-avatar {color}',
                     style={'width': '44px', 'height': '44px', 'fontSize': '16px',
                            'borderRadius': 'var(--radius-md)'},
                     children=_initials(name)),
            html.Div(children=[
                html.Div(name, style={'fontSize': '15px', 'fontWeight': '700',
                                      'color': 'var(--text-primary)'}),
                html.Div(f'@{user["username"]}',
                         style={'fontSize': '12px', 'color': 'var(--text-muted)'}),
            ]),
        ]),
        # Info grid
        html.Div(className='drawer-section', children=[
            html.Div(className='drawer-section-body', children=[
                html.Div(className='drawer-info-row', children=[
                    html.Span('Email', className='drawer-info-label'),
                    html.Span(user.get('email', 'N/A'), className='drawer-info-value'),
                ]),
                html.Div(className='drawer-info-row', children=[
                    html.Span('Role', className='drawer-info-label'),
                    html.Span(_role_badge(user['role_name'])),
                ]),
                html.Div(className='drawer-info-row', children=[
                    html.Span('Status', className='drawer-info-label'),
                    html.Span(_status_badge(user['status'])),
                ]),
                html.Div(className='drawer-info-row', children=[
                    html.Span('Member Since', className='drawer-info-label'),
                    html.Span(_fmt_date(user.get('created_at')),
                              className='drawer-info-value'),
                ]),
                html.Div(className='drawer-info-row', children=[
                    html.Span('Last Login', className='drawer-info-label'),
                    html.Span(_fmt_date(user.get('last_login_at')) or 'Never',
                              className='drawer-info-value'),
                ]),
            ]),
        ]),
        # Stats
        html.Div(style={'marginTop': '12px'}, children=[
            html.Div(className='drawer-stat-grid', children=[
                html.Div(className='drawer-stat-item', children=[
                    html.Span('Simulation Runs', className='stat-label'),
                    html.Span(str(activity['run_count']), className='stat-value info'),
                ]),
                html.Div(className='drawer-stat-item', children=[
                    html.Span('Audit Events', className='stat-label'),
                    html.Span(str(activity['audit_count']), className='stat-value warning'),
                ]),
            ]),
        ]),
    ])

    return name, content
