"""
SMARTFLOW — Admin Role & Access Control Page
Manage permission matrices dynamically in SQLite permissions table.
"""

from dash import html, dcc, callback, Input, Output, State, ALL, ctx
from flask import session

import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_modal


# Permission group configuration

PERMISSION_GROUPS = [
    (
        'Dashboard Access',
        'fas fa-gauge',
        [
            ('dashboard', 'view', 'View Dashboard Overview'),
        ],
    ),
    (
        'Simulation Control',
        'fas fa-play-circle',
        [
            ('simulation', 'view', 'View Simulation Control Panel'),
            ('simulation', 'run', 'Execute Traffic Simulation Runs'),
        ],
    ),
    (
        'Scenario Management',
        'fas fa-map-marked-alt',
        [
            ('scenarios', 'view', 'View Scenarios Configurations'),
            ('scenarios', 'create', 'Create Custom Scenarios'),
            ('scenarios', 'edit', 'Edit Scenario Settings'),
            ('scenarios', 'delete', 'Delete Scenario Presets'),
        ],
    ),
    (
        'Live Traffic Monitoring',
        'fas fa-traffic-light',
        [
            ('live-traffic', 'view', 'View Live Traffic Monitoring'),
        ],
    ),
    (
        'Performance Reports',
        'fas fa-chart-line',
        [
            ('performance', 'view', 'View Performance Analytics Charts'),
        ],
    ),
    (
        'AI Agent RL Panel',
        'fas fa-brain',
        [
            ('ai-agent', 'view', 'View AI Agent Reinforcement Learning Telemetry'),
        ],
    ),
    (
        'Runs and Reports Export',
        'fas fa-file-export',
        [
            ('runs-reports', 'view', 'View Runs History List'),
            ('runs-reports', 'export', 'Export Simulation Reports (CSV/Excel/PDF)'),
        ],
    ),
    (
        'User Management',
        'fas fa-users',
        [
            ('admin-users', 'view', 'Admin: Account Approvals & User Management'),
        ],
    ),
    (
        'Role Access Control',
        'fas fa-shield-alt',
        [
            ('admin-roles', 'view', 'Admin: Access Control Permissions Matrix'),
        ],
    ),


    (
        'Audit Logs',
        'fas fa-clipboard-list',
        [
            ('admin-audit', 'view', 'Admin: View Audit Ledger'),
        ],
    ),
    (
        'Backup and Restore',
        'fas fa-database',
        [
            ('admin-backups', 'view', 'Admin: Database Backups & Restore'),
        ],
    ),
]

ROLE_ORDER = ['admin', 'researcher', 'researcher_pending', 'disabled']

ROLE_META = {
    'admin': {
        'label': 'Administrator',
        'icon': 'fas fa-shield-halved',
        'pill': 'pill-admin',
        'locked': True,
        'note': 'Full platform access with security oversight.',
    },
    'researcher': {
        'label': 'Researcher',
        'icon': 'fas fa-flask',
        'pill': 'pill-researcher',
        'locked': False,
        'note': 'Standard role for experiments and analysis.',
    },
    'researcher_pending': {
        'label': 'Researcher Pending',
        'icon': 'fas fa-hourglass-half',
        'pill': 'pill-pending',
        'locked': True,
        'note': 'Limited access pending admin review.',
    },
    'disabled': {
        'label': 'Disabled User',
        'icon': 'fas fa-user-slash',
        'pill': 'pill-disabled',
        'locked': True,
        'note': 'Account suspended or deactivated.',
    },
}

PROTECTED_PERMISSION_KEYS = {
    'admin-users:view',
    'admin-roles:view',

    'admin-audit:view',
    'admin-backups:view',

}


def permission_key(page, action):
    return f"{page}:{action}"


def flatten_permission_groups(groups):
    return [perm for _, _, items in groups for perm in items]


def apply_pending_permissions(base_keys, pending_map, role_id):
    effective = set(base_keys)
    for key, enabled in (pending_map or {}).items():
        role_str, page, action = key.split(':', 2)
        if role_str != str(role_id):
            continue
        perm = f"{page}:{action}"
        if enabled:
            effective.add(perm)
        else:
            effective.discard(perm)
    return effective


def compute_role_stats(all_perm_keys, role_perm_keys, protected_keys):
    all_keys = set(all_perm_keys)
    role_keys = set(role_perm_keys)
    protected = set(protected_keys)
    return {
        'granted': len(role_keys & all_keys),
        'restricted': len(all_keys - role_keys),
        'protected_total': len(all_keys & protected),
        'protected_granted': len(role_keys & protected),
    }


def _load_roles():
    roles = database.list_roles()
    by_name = {r['name']: r for r in roles}
    ordered = []
    for name in ROLE_ORDER:
        role = by_name.get(name)
        if not role:
            continue
        meta = ROLE_META.get(name, {})
        ordered.append({**role, **meta})
    return ordered


def _build_permissions_map(roles):
    perm_map = {}
    for role in roles:
        perms = database.get_permissions_for_role(role['id'])
        perm_map[str(role['id'])] = {
            permission_key(p['page'], p['action']) for p in perms
        }
    return perm_map


def _build_kpi_row(total_roles, total_perms, admin_enabled, restricted):
    items = [
        ('fas fa-users', str(total_roles), 'Total Roles', 'var(--info)'),
        ('fas fa-layer-group', str(total_perms), 'Total Permissions', 'var(--success)'),
        ('fas fa-shield-check', str(admin_enabled), 'Enabled Admin Permissions', 'var(--purple)'),
        ('fas fa-lock', str(restricted), 'Restricted Actions', 'var(--warning)'),
    ]
    return html.Div(
        className='kpi-row-4',
        children=[
            html.Div(
                className='kpi-card-compact',
                children=[
                    html.Div(
                        className='kpi-icon-wrap',
                        style={
                            'background': f'color-mix(in srgb, {color} 12%, transparent)',
                            'border': f'1px solid color-mix(in srgb, {color} 20%, transparent)',
                        },
                        children=[html.I(className=icon, style={'color': color})],
                    ),
                    html.Div(
                        className='kpi-content',
                        children=[
                            html.Span(value, className='kpi-value'),
                            html.Span(label, className='kpi-label'),
                        ],
                    ),
                ],
            )
            for icon, value, label, color in items
        ],
    )


def _build_matrix(roles, perm_map, pending, selected_role, search_query):
    rows = []
    query = (search_query or '').strip().lower()

    def _role_header(role, effective_count):
        selected = 'selected' if str(role['id']) == str(selected_role) else ''
        return html.Th(
            className=f'role-col {selected}'.strip(),
            children=[
                html.I(className=f"role-icon {role['icon']}") if role.get('icon') else '',
                role['label'],
                html.Span(str(effective_count), className='count-badge'),
            ],
        )

    header_roles = []
    for role in roles:
        base_keys = perm_map.get(str(role['id']), set())
        effective = apply_pending_permissions(base_keys, pending, role['id'])
        header_roles.append(_role_header(role, len(effective)))

    for group_label, group_icon, items in PERMISSION_GROUPS:
        group_rows = []
        for page, action, desc in items:
            key = permission_key(page, action)
            if query and query not in desc.lower() and query not in key.lower():
                continue

            cells = [
                html.Td(desc),
                html.Td(html.Code(key, className='perm-key')),
            ]

            for role in roles:
                base_keys = perm_map.get(str(role['id']), set())
                effective = apply_pending_permissions(base_keys, pending, role['id'])
                enabled = key in effective
                selected = 'selected' if str(role['id']) == str(selected_role) else ''
                cell_class = f'perm-toggle-cell role-col {selected}'.strip()

                if role.get('locked', True) and role['name'] != 'researcher':
                    toggle = html.Span(
                        className=f"perm-toggle {'enabled' if enabled else 'disabled'}",
                    )
                else:
                    toggle = dcc.Checklist(
                        id={
                            'type': 'perm-checkbox',
                            'index': f"{role['id']}:{page}:{action}",
                        },
                        options=[{'label': '', 'value': 'enabled'}],
                        value=['enabled'] if enabled else [],
                        className='perm-checkbox',
                        labelStyle={'display': 'none'},
                    )

                cells.append(html.Td(toggle, className=cell_class))

            row_class = 'highlight-row' if query else ''
            group_rows.append(html.Tr(cells, className=row_class))

        if group_rows:
            rows.append(
                html.Tr(
                    className='perm-category',
                    children=[
                        html.Td(
                            [html.I(className=group_icon), group_label],
                            colSpan=2 + len(roles),
                        )
                    ],
                )
            )
            rows.extend(group_rows)

    table = html.Table(
        className='perm-matrix',
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th('Permission'),
                        html.Th('Key'),
                        *header_roles,
                    ]
                )
            ),
            html.Tbody(rows),
        ],
    )

    return html.Div(className='perm-matrix-wrap', children=[table])


def _build_role_detail(role, effective_keys, all_perm_keys):
    stats = compute_role_stats(all_perm_keys, effective_keys, PROTECTED_PERMISSION_KEYS)
    protected_labels = [
        'User management',
        'Role access control',
        'Audit logs',
        'Backup and restore',
    ]
    description = role.get('description') or ''
    note = role.get('note') or ''

    return html.Div(
        className='role-detail-card selected',
        children=[
            html.Div(
                className='role-detail-top',
                children=[
                    html.Div(
                        className='role-detail-icon',
                        style={'background': 'var(--bg-input)'},
                        children=[html.I(className=role['icon'])],
                    ),
                    html.Div(
                        children=[
                            html.Div(role['label'], className='role-detail-name'),
                            html.Span(description, className='role-detail-desc') if description else None,
                            html.Span(note, className='role-detail-note') if note else None,
                        ],
                    ),
                ],
            ),
            html.Div(
                className='role-detail-stats',
                children=[
                    html.Div(
                        className='role-stat',
                        children=[
                            html.Span('Granted', className='role-stat-label'),
                            html.Span(str(stats['granted']), className='role-stat-value green'),
                        ],
                    ),
                    html.Div(
                        className='role-stat',
                        children=[
                            html.Span('Restricted', className='role-stat-label'),
                            html.Span(str(stats['restricted']), className='role-stat-value amber'),
                        ],
                    ),
                ],
            ),
            html.Div(
                className='role-detail-notes',
                children=[
                    html.Div('Protected Actions', className='role-notes-title'),
                    html.Ul(
                        className='role-notes-list',
                        children=[html.Li(item) for item in protected_labels],
                    ),
                ],
            ),
        ],
    )


def layout():
    # Enforce admin check
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

    roles = _load_roles()
    role_options = [
        {'label': r['label'], 'value': str(r['id'])}
        for r in roles
    ]
    default_role = next(
        (str(r['id']) for r in roles if r['name'] == 'researcher'),
        role_options[0]['value'] if role_options else None,
    )

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
                                    html.H1('Access Control & Permissions Matrix'),
                                    html.P(
                                        'Govern role-based access for the SMARTFLOW admin platform. '
                                        'Changes apply after review and save.'
                                    ),
                                ],
                            ),
                            html.Div(
                                id='admin-roles-alert',
                                className='alert alert-info hidden',
                                children='',
                            ),
                            html.Div(id='roles-kpi-row'),
                            html.Div(
                                className='roles-page-grid',
                                children=[
                                    html.Div(
                                        className='section perm-matrix-card',
                                        children=[
                                            html.Div(
                                                className='section-header',
                                                children=[
                                                    html.I(className='fas fa-shield-alt'),
                                                    html.H3(
                                                        className='section-title',
                                                        children=[
                                                            html.Span(
                                                                'Role Permission Matrix',
                                                                className='section-title-text',
                                                            ),
                                                            html.Small(
                                                                'Compare permissions across roles and save safely.',
                                                                className='section-subtitle',
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className='filter-bar-roles',
                                                children=[
                                                    html.Div(
                                                        className='filter-group filter-group-wide',
                                                        children=[
                                                            html.Span('Search permissions', className='filter-label'),
                                                            dcc.Input(
                                                                id='role-search-input',
                                                                type='text',
                                                                placeholder='Search by name or key...',
                                                                className='filter-input',
                                                                debounce=True,
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        className='filter-group',
                                                        children=[
                                                            html.Span('Role focus', className='filter-label'),
                                                            dcc.Dropdown(
                                                                id='role-selector',
                                                                options=role_options,
                                                                value=default_role,
                                                                className='dropdown dropdown-small',
                                                                clearable=False,
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(className='filter-spacer'),
                                                    html.Button(
                                                        [html.I(className='fas fa-rotate-left'), 'Reset'],
                                                        id='reset-perms-btn',
                                                        className='btn btn-secondary btn-sm',
                                                    ),
                                                    html.Button(
                                                        [html.I(className='fas fa-shield-check'), 'Save Changes'],
                                                        id='save-perms-btn',
                                                        className='btn btn-primary btn-sm',
                                                        disabled=True,
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className='section-content',
                                                children=[
                                                    html.Div(
                                                        className='legend-row',
                                                        children=[
                                                            html.Div(
                                                                className='legend-item',
                                                                children=[
                                                                    html.Span('', className='legend-swatch on'),
                                                                    'Enabled',
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className='legend-item',
                                                                children=[
                                                                    html.Span('', className='legend-swatch off'),
                                                                    'Disabled',
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className='legend-item',
                                                                children=[
                                                                    html.Span(
                                                                        html.I(
                                                                            className='fas fa-lock',
                                                                            style={'fontSize': '7px'},
                                                                        ),
                                                                        className='legend-swatch off',
                                                                    ),
                                                                    'Locked',
                                                                ],
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(id='roles-matrix'),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className='role-detail-sidebar',
                                        children=[
                                            html.Div(
                                                id='role-detail-panel',
                                                className='role-detail-panel',
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            dcc.Store(id='perm-pending-store', data={}),
                            dcc.Store(id='perm-refresh-store', data=0),
                            create_modal(
                                id='perm-confirm-modal',
                                title='Confirm Protected Changes',
                                children=[
                                    html.P(
                                        'You are attempting to modify protected admin permissions. '
                                        'Confirm to apply these changes.'
                                    ),
                                    html.Div(
                                        className='modal-footer',
                                        children=[
                                            html.Button(
                                                'Cancel',
                                                id='perm-confirm-cancel',
                                                className='btn btn-secondary btn-sm',
                                            ),
                                            html.Button(
                                                'Confirm',
                                                id='perm-confirm-apply',
                                                className='btn btn-primary btn-sm',
                                            ),
                                        ],
                                    ),
                                ],
                                is_open=False,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


@callback(
    Output('roles-kpi-row', 'children'),
    Output('roles-matrix', 'children'),
    Output('role-detail-panel', 'children'),
    Input('role-search-input', 'value'),
    Input('role-selector', 'value'),
    Input('perm-pending-store', 'data'),
    Input('perm-refresh-store', 'data'),
)
def render_roles_matrix(search_value, selected_role, pending, _refresh):
    roles = _load_roles()
    perm_map = _build_permissions_map(roles)
    all_perm_keys = {
        permission_key(page, action)
        for page, action, _ in flatten_permission_groups(PERMISSION_GROUPS)
    }

    if not roles:
        empty = html.Div(
            className='empty-state',
            children=[
                html.I(className='fas fa-shield'),
                html.P('No roles available.'),
            ],
        )
        return html.Div(), empty, empty

    selected = selected_role or str(roles[0]['id'])
    selected_role_obj = next(
        (r for r in roles if str(r['id']) == str(selected)),
        roles[0],
    )

    effective_selected = apply_pending_permissions(
        perm_map.get(str(selected_role_obj['id']), set()),
        pending,
        selected_role_obj['id'],
    )

    kpi_row = _build_kpi_row(
        total_roles=len(roles),
        total_perms=len(all_perm_keys),
        admin_enabled=len(all_perm_keys),
        restricted=len(all_perm_keys - effective_selected),
    )

    matrix = _build_matrix(
        roles,
        perm_map,
        pending,
        selected,
        search_value,
    )

    detail_panel = _build_role_detail(
        selected_role_obj,
        effective_selected,
        all_perm_keys,
    )

    return kpi_row, matrix, detail_panel


@callback(
    Output('perm-pending-store', 'data', allow_duplicate=True),
    Output('save-perms-btn', 'disabled'),
    Output('admin-roles-alert', 'children', allow_duplicate=True),
    Output('admin-roles-alert', 'className', allow_duplicate=True),
    Input({'type': 'perm-checkbox', 'index': ALL}, 'value'),
    State({'type': 'perm-checkbox', 'index': ALL}, 'id'),
    State('perm-pending-store', 'data'),
    prevent_initial_call=True
)
def track_permission_changes(values, ids, pending):
    if not ctx.triggered_id:
        return pending or {}, True, '', 'alert alert-info hidden'

    if not auth.is_admin():
        return pending or {}, True, 'Access Denied: Administrative action not authorized.', 'alert alert-error'

    pending = dict(pending or {})
    triggered = ctx.triggered_id

    try:
        idx = next(i for i, val in enumerate(ids) if val == triggered)
    except StopIteration:
        return pending, len(pending) == 0, '', 'alert alert-info hidden'

    new_enabled = bool(values[idx])
    pending[triggered['index']] = new_enabled

    count = len(pending)
    alert = f"Pending changes: {count}. Save to apply." if count else ''
    alert_class = 'alert alert-warning' if count else 'alert alert-info hidden'

    return pending, count == 0, alert, alert_class


@callback(
    Output('perm-confirm-modal', 'className'),
    Output('perm-pending-store', 'data'),
    Output('perm-refresh-store', 'data'),
    Output('admin-roles-alert', 'children'),
    Output('admin-roles-alert', 'className'),
    Input('save-perms-btn', 'n_clicks'),
    Input('reset-perms-btn', 'n_clicks'),
    Input('perm-confirm-apply', 'n_clicks'),
    Input('perm-confirm-cancel', 'n_clicks'),
    Input('perm-confirm-modal-close', 'n_clicks'),
    State('perm-pending-store', 'data'),
    State('perm-refresh-store', 'data'),
    prevent_initial_call=True
)
def handle_save_reset(
    save_clicks,
    reset_clicks,
    confirm_clicks,
    cancel_clicks,
    close_clicks,
    pending,
    refresh,
):
    pending = dict(pending or {})
    refresh = refresh or 0
    triggered = ctx.triggered_id

    if not auth.is_admin():
        return 'modal-overlay hidden', pending, refresh, 'Access Denied: Administrative action not authorized.', 'alert alert-error'

    if triggered in {'perm-confirm-cancel', 'perm-confirm-modal-close'}:
        return 'modal-overlay hidden', pending, refresh, '', 'alert alert-info hidden'

    if triggered == 'reset-perms-btn':
        return 'modal-overlay hidden', {}, refresh + 1, 'Changes reset.', 'alert alert-info'

    if triggered == 'save-perms-btn':
        if not pending:
            return 'modal-overlay hidden', pending, refresh, 'No changes to save.', 'alert alert-info'

        protected_pending = any(
            ':'.join(key.split(':', 2)[1:]) in PROTECTED_PERMISSION_KEYS
            for key in pending
        )

        if protected_pending:
            return 'modal-overlay', pending, refresh, 'Protected changes require confirmation.', 'alert alert-warning'

    if triggered in {'perm-confirm-apply', 'save-perms-btn'}:
        for key, enabled in pending.items():
            role_str, page, action = key.split(':', 2)
            database.update_role_permission(int(role_str), page, action, enabled)

            current_admin_id = session.get('user_id')
            current_admin_username = session.get('username')
            action_name = 'granted' if enabled else 'revoked'
            database.log_audit_event(
                user_id=current_admin_id,
                action='update_permission',
                target='permissions',
                details=(
                    f"Admin {current_admin_username} {action_name} "
                    f"'{page}:{action}' permission for role {role_str}."
                ),
            )

        return 'modal-overlay hidden', {}, refresh + 1, 'Permissions saved.', 'alert alert-success'

    return 'modal-overlay hidden', pending, refresh, '', 'alert alert-info hidden'
