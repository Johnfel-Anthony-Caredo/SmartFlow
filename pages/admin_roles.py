"""
SMARTFLOW — Admin Role & Access Control Page
Manage permission matrices dynamically in SQLite permissions table.
"""

import json
from dash import html, dcc, callback, Input, Output, State, ALL, ctx
from flask import session

import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section


# Defined set of system-wide permissions
PERMISSION_KEYS = [
    ('dashboard', 'view', 'View Dashboard Overview'),
    ('simulation', 'view', 'View Simulation Control Panel'),
    ('simulation', 'run', 'Execute Traffic Simulation Runs'),
    ('scenarios', 'view', 'View Scenarios Configurations'),
    ('scenarios', 'create', 'Create Custom Scenarios'),
    ('scenarios', 'edit', 'Edit Scenario Settings'),
    ('scenarios', 'delete', 'Delete Scenario Presets'),
    ('live-traffic', 'view', 'View Live Traffic Monitoring'),
    ('performance', 'view', 'View Performance Analytics Charts'),
    ('ai-agent', 'view', 'View AI Agent Reinforcement Learning Telemetry'),
    ('runs-reports', 'view', 'View Runs History List'),
    ('runs-reports', 'export', 'Export Simulation Reports (CSV/Excel/PDF)'),
    ('admin-users', 'view', 'Admin: Account Approvals & User Management'),
    ('admin-roles', 'view', 'Admin: Access Control Permissions Matrix'),
    ('admin-scenarios', 'view', 'Admin: Scenario Library presets governing'),
    ('admin-config', 'view', 'Admin: Platform Config Settings'),
    ('admin-audit', 'view', 'Admin: View Audit Ledger'),
    ('admin-backups', 'view', 'Admin: Database Backups & Restore'),
]


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
        
    # Get researcher current permissions list from DB
    researcher_perms = database.get_permissions_for_role(2)
    researcher_active_keys = {f"{p['page']}:{p['action']}" for p in researcher_perms}
    
    rows = []
    for page, action, desc in PERMISSION_KEYS:
        researcher_has_perm = f"{page}:{action}" in researcher_active_keys
        
        rows.append(
            html.Tr(children=[
                html.Td(desc, style={'fontWeight': '500'}),
                html.Td(html.Code(f"{page}:{action}", style={'color': '#ab47bc'})),
                
                # Admin (bypassed, always active)
                html.Td(style={'textAlign': 'center'}, children=[
                    dcc.Checkbox(value=True, disabled=True, className='checkbox')
                ]),
                
                # Researcher (Checkable)
                html.Td(style={'textAlign': 'center'}, children=[
                    dcc.Checkbox(
                        id={'type': 'perm-checkbox', 'index': f"2:{page}:{action}"},
                        value=researcher_has_perm,
                        className='checkbox'
                    )
                ]),
                
                # Researcher Pending (Disabled, unchecked)
                html.Td(style={'textAlign': 'center'}, children=[
                    dcc.Checkbox(value=False, disabled=True, className='checkbox')
                ]),
                
                # Disabled Role (Disabled, unchecked)
                html.Td(style={'textAlign': 'center'}, children=[
                    dcc.Checkbox(value=False, disabled=True, className='checkbox')
                ])
            ])
        )
        
    table = html.Table(
        className='data-table',
        children=[
            html.Thead(children=[
                html.Tr(children=[
                    html.Th('Permission Name'),
                    html.Th('Key Identifier'),
                    html.Th('Administrator', style={'textAlign': 'center'}),
                    html.Th('Researcher', style={'textAlign': 'center'}),
                    html.Th('Researcher Pending', style={'textAlign': 'center'}),
                    html.Th('Disabled User', style={'textAlign': 'center'})
                ])
            ]),
            html.Tbody(children=rows)
        ]
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
                                    html.H1(children='Access Control & Permissions Matrix'),
                                    html.P(children='Govern functional access rights for system roles. Changes applied here affect active user sessions dynamically.'),
                                ]
                            ),
                            
                            html.Div(
                                id='admin-roles-alert',
                                className='alert alert-info hidden',
                                children=''
                            ),
                            
                            create_section(
                                title='Role Permission Grid',
                                icon='fas fa-shield-alt',
                                children=[table]
                            )
                        ]
                    )
                ]
            )
        ]
    )


@callback(
    [Output('admin-roles-alert', 'children'),
     Output('admin-roles-alert', 'className')],
    Input({'type': 'perm-checkbox', 'index': ALL}, 'value'),
    State({'type': 'perm-checkbox', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def handle_permission_change(values, ids):
    triggered = ctx.triggered
    if not triggered:
        return '', 'alert alert-info hidden'
        
    # Verify administrative state
    if not auth.is_admin():
        return 'Access Denied: Administrative action not authorized.', 'alert alert-error'
        
    triggered_prop = triggered[0]['prop_id']
    
    try:
        # Extract dynamic ID details
        dict_str = triggered_prop.split('.value')[0]
        triggered_id = json.loads(dict_str)
        index_val = triggered_id['index']  # Format: "2:page:action"
        role_id_str, page, action = index_val.split(':')
        role_id = int(role_id_str)
        
        # Match index to obtain the updated value
        idx_in_list = [i for i, d in enumerate(ids) if d['index'] == index_val][0]
        new_enabled = bool(values[idx_in_list])
        
        # Update permissions table in DB
        database.update_role_permission(role_id, page, action, new_enabled)
        
        # Log audit log
        current_admin_id = session.get('user_id')
        current_admin_username = session.get('username')
        action_name = "granted" if new_enabled else "revoked"
        database.log_audit_event(
            user_id=current_admin_id,
            action='update_permission',
            target='permissions',
            details=f"Admin {current_admin_username} {action_name} '{page}:{action}' permission for Researcher role."
        )
        
        return f"Successfully updated Researcher permission '{page}:{action}' to {new_enabled}.", 'alert alert-success'
    except Exception as e:
        return f"Failed to update permission: {str(e)}", 'alert alert-error'
