"""
SMARTFLOW — Admin Backup & Restore Page
Manage SQLite local database snapshots, create manual backups, and restore snapshots.
"""

import os
import json
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
from flask import session

import auth
import database
import config
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_button


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
        
    backups = database.list_backups()
    
    rows = []
    if not backups:
        rows.append(
            html.Tr(children=[
                html.Td('No backups recorded.', colSpan=5, style={'textAlign': 'center', 'color': '#64748b'})
            ])
        )
    else:
        for b in backups:
            size_kb = f"{b['size_bytes'] / 1024:.1f} KB"
            rows.append(
                html.Tr(children=[
                    html.Td(b['created_at']),
                    html.Td(b['username'] or 'System'),
                    html.Td(b['filename']),
                    html.Td(size_kb),
                    html.Td(children=[
                        html.Button(
                            'Restore',
                            id={'type': 'restore-backup-btn', 'index': b['id']},
                            className='btn btn-warning btn-sm',
                            style={'marginRight': '8px'}
                        ),
                        html.Button(
                            'Delete',
                            id={'type': 'delete-backup-btn', 'index': b['id']},
                            className='btn btn-danger btn-sm'
                        )
                    ])
                ])
            )
            
    table = html.Table(
        className='data-table',
        children=[
            html.Thead(children=[
                html.Tr(children=[
                    html.Th('Created At'),
                    html.Th('Creator'),
                    html.Th('Filename'),
                    html.Th('File Size'),
                    html.Th('Actions')
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
                                    html.H1(children='Backup & Restore'),
                                    html.P(children='Create manual snapshots of the platform database, restore past snapshots, or download raw SQLite databases directly.'),
                                ]
                            ),
                            
                            html.Div(
                                id='admin-backups-alert',
                                className='alert alert-info hidden',
                                children=''
                            ),
                            
                            html.Div(
                                style={'display': 'grid', 'gridTemplateColumns': '3fr 1fr', 'gap': '20px'},
                                children=[
                                    create_section(
                                        title='Available Database Snapshots',
                                        icon='fas fa-history',
                                        children=[table]
                                    ),
                                    
                                    create_section(
                                        title='Database Actions',
                                        icon='fas fa-database',
                                        children=[
                                            html.Div(style={'marginBottom': '20px'}, children=[
                                                html.H4('Create Local Snapshot'),
                                                html.P('Create a duplicate copy of the active database on disk.', style={'fontSize': '12px', 'color': '#64748b', 'marginBottom': '10px'}),
                                                create_button(
                                                    id='create-backup-btn',
                                                    text='Backup Database',
                                                    icon='fas fa-file-medical',
                                                    className='btn btn-success btn-full'
                                                )
                                            ]),
                                            
                                            html.Div(children=[
                                                html.H4('Export Active SQLite'),
                                                html.P('Download the live database file to your local computer.', style={'fontSize': '12px', 'color': '#64748b', 'marginBottom': '10px'}),
                                                create_button(
                                                    id='download-db-btn',
                                                    text='Download SQLite DB',
                                                    icon='fas fa-download',
                                                    className='btn btn-primary btn-full'
                                                )
                                            ])
                                        ]
                                    )
                                ]
                            ),
                            dcc.Download(id='download-db-file'),
                            dcc.Location(id='admin-backups-redirect', refresh=True)
                        ]
                    )
                ]
            )
        ]
    )


@callback(
    [Output('admin-backups-alert', 'children'),
     Output('admin-backups-alert', 'className'),
     Output('admin-backups-redirect', 'pathname')],
    [Input('create-backup-btn', 'n_clicks'),
     Input({'type': 'restore-backup-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'delete-backup-btn', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def handle_backup_actions(create_clicks, restore_clicks, delete_clicks):
    triggered_id = ctx.triggered_id
    if not triggered_id:
        return '', 'alert alert-info hidden', None
        
    # Verify administrator access
    if not auth.is_admin():
        return 'Access Denied: Administrative action not authorized.', 'alert alert-error', '/login'
        
    current_admin_id = session.get('user_id')
    current_admin_username = session.get('username')
    
    # ─── HANDLE CREATE BACKUP ─────────────────────────────────────────
    if triggered_id == 'create-backup-btn':
        try:
            filename = database.create_backup(current_admin_id)
            database.log_audit_event(
                user_id=current_admin_id,
                action='create_backup',
                target='system_settings',
                details=f"Admin {current_admin_username} created manual database backup snapshot: '{filename}'"
            )
            return 'Database backup created successfully.', 'alert alert-success', '/admin/backups'
        except Exception as e:
            return f"Failed to create backup: {str(e)}", 'alert alert-error', None
            
    # ─── HANDLE DYNAMIC snapshot restore or deletion ──────────────────
    elif isinstance(triggered_id, dict):
        action_type = triggered_id.get('type')
        backup_id = triggered_id.get('index')
        
        # ─── Restore snapshot ───
        if action_type == 'restore-backup-btn':
            try:
                # Retrieve details of the backup before restoring (restoring will modify database metadata)
                filename = database.restore_backup(backup_id)
                database.log_audit_event(
                    user_id=current_admin_id,
                    action='restore_backup',
                    target='system_settings',
                    details=f"Admin {current_admin_username} restored database from snapshot '{filename}' (ID={backup_id})"
                )
                
                # Enforce system logout: DB file has swapped, user sessions should be re-authenticated
                return 'Database restored successfully! Logging out to apply restored user credentials...', 'alert alert-success', '/logout'
            except Exception as e:
                return f"Failed to restore backup: {str(e)}", 'alert alert-error', None
                
        # ─── Delete snapshot ───
        elif action_type == 'delete-backup-btn':
            try:
                database.delete_backup_from_db(backup_id)
                database.log_audit_event(
                    user_id=current_admin_id,
                    action='delete_backup',
                    target='system_settings',
                    details=f"Admin {current_admin_username} deleted backup snapshot ID={backup_id}"
                )
                return 'Database backup snapshot permanently deleted.', 'alert alert-success', '/admin/backups'
            except Exception as e:
                return f"Failed to delete backup: {str(e)}", 'alert alert-error', None
                
    return '', 'alert alert-info hidden', None


@callback(
    Output('download-db-file', 'data'),
    Input('download-db-btn', 'n_clicks'),
    prevent_initial_call=True
)
def handle_db_download(n_clicks):
    if not n_clicks:
        return no_update
        
    if not auth.is_admin():
        return no_update
        
    current_admin_id = session.get('user_id')
    current_admin_username = session.get('username')
    
    # Log database download
    database.log_audit_event(
        user_id=current_admin_id,
        action='download_database',
        target='system_settings',
        details=f"Admin {current_admin_username} downloaded the active SQLite database file."
    )
    
    return dcc.send_file(config.DB_PATH)
