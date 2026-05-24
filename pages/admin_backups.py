"""
SMARTFLOW — Admin Backup & Restore Page
Manage SQLite local database snapshots, create manual backups, and restore snapshots.
"""

import os
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
from flask import session

import auth
import database
import config
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_button, create_mini_stat


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

    backups = database.list_backups()
    total = len(backups)
    total_bytes = sum(b['size_bytes'] for b in backups) if backups else 0
    storage_display = f"{total_bytes / 1024:.1f} KB" if total_bytes < 1048576 else f"{total_bytes / 1048576:.1f} MB"
    latest = backups[0]['created_at'] if backups else 'None'

    rows = []
    if not backups:
        rows.append(html.Tr([
            html.Td(html.Div(className='empty-state', children=[
                html.I(className='fas fa-history'),
                html.P('No backup snapshots yet'),
                html.P('Create your first backup using the Database Actions panel.', className='empty-state-hint'),
            ]), colSpan=5)
        ]))
    else:
        for b in backups:
            size_kb = f"{b['size_bytes'] / 1024:.1f} KB"
            rows.append(html.Tr([
                html.Td(b['created_at']),
                html.Td(b['username'] or 'System'),
                html.Td(b['filename']),
                html.Td(size_kb),
                html.Td(html.Div(className='actions-cell', children=[
                    html.Button('Restore', id={'type': 'restore-backup-btn', 'index': b['id']},
                                className='btn btn-warning btn-sm'),
                    html.Button('Delete', id={'type': 'delete-backup-btn', 'index': b['id']},
                                className='btn btn-danger btn-sm'),
                ]))
            ]))

    table = html.Table(className='data-table', children=[
        html.Thead([html.Tr([
            html.Th('Created At'), html.Th('Creator'), html.Th('Filename'),
            html.Th('File Size'), html.Th('Actions'),
        ])]),
        html.Tbody(rows)
    ])

    return html.Div(className='app-layout', children=[
        create_header(),
        html.Div(className='app-body', children=[
            create_sidebar(),
            html.Main(className='main-content', children=[
                html.Div(className='page-header', children=[
                    html.H1('Backup & Restore'),
                    html.P('Create database snapshots, restore from backups, or download the live SQLite file.'),
                ]),

                html.Div(className='stats-row stats-row-3', children=[
                    create_mini_stat('Total Backups', str(total), 'fas fa-history', 'var(--info)'),
                    create_mini_stat('Storage Used', storage_display, 'fas fa-hard-drive', 'var(--warning)'),
                    create_mini_stat('Latest Backup', latest, 'fas fa-clock', 'var(--accent)'),
                ]),

                html.Div(id='admin-backups-alert', className='alert alert-info hidden'),

                html.Div(style={'display': 'grid', 'gridTemplateColumns': '2fr 1fr', 'gap': '20px'},
                         children=[
                             create_section(
                                 title='Backup Snapshots',
                                 subtitle='View, restore, or delete saved database copies',
                                 icon='fas fa-history',
                                 children=[
                                     html.Div(className='table-scroll', style={'maxHeight': '460px'}, children=[table])
                                 ]
                             ),
                             create_section(
                                 title='Database Actions',
                                 subtitle='Create new backups or export the live database',
                                 icon='fas fa-database',
                                 children=[
                                     html.Div(className='action-card', children=[
                                         html.Div(className='action-card-icon', children=[
                                             html.I(className='fas fa-file-medical'),
                                         ]),
                                         html.Div(className='action-card-content', children=[
                                             html.H4('Create Local Snapshot'),
                                             html.P('Save a point-in-time copy of the entire database.'),
                                         ]),
                                         create_button(id='create-backup-btn', text='Backup Database',
                                                       icon='fas fa-file-medical',
                                                       className='btn btn-primary btn-full')
                                     ]),
                                     html.Div(className='action-card', style={'marginTop': '16px'}, children=[
                                         html.Div(className='action-card-icon', children=[
                                             html.I(className='fas fa-download'),
                                         ]),
                                         html.Div(className='action-card-content', children=[
                                             html.H4('Export Active SQLite'),
                                             html.P('Download the current database file to your local machine.'),
                                         ]),
                                         create_button(id='download-db-btn', text='Download SQLite DB',
                                                       icon='fas fa-download',
                                                       className='btn btn-secondary btn-full')
                                     ]),
                                 ]
                             ),
                         ]),

                dcc.Download(id='download-db-file'),
                dcc.Location(id='admin-backups-redirect', refresh=True),
            ])
        ])
    ])


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

    if not auth.is_admin():
        return 'Access Denied: Administrative action not authorized.', 'alert alert-error', '/login'

    current_admin_id = session.get('user_id')
    current_admin_username = session.get('username')

    if triggered_id == 'create-backup-btn':
        try:
            filename = database.create_backup(current_admin_id)
            database.log_audit_event(user_id=current_admin_id, action='create_backup', target='system_settings',
                                     details=f"Admin {current_admin_username} created manual backup snapshot: '{filename}'")
            return 'Database backup created successfully.', 'alert alert-success', '/admin/backups'
        except Exception as e:
            return f"Failed to create backup: {str(e)}", 'alert alert-error', None

    elif isinstance(triggered_id, dict):
        action_type = triggered_id.get('type')
        backup_id = triggered_id.get('index')

        if action_type == 'restore-backup-btn':
            try:
                filename = database.restore_backup(backup_id)
                database.log_audit_event(user_id=current_admin_id, action='restore_backup', target='system_settings',
                                         details=f"Admin {current_admin_username} restored database from snapshot '{filename}' (ID={backup_id})")
                return 'Database restored successfully! Logging out to apply restored credentials...', 'alert alert-success', '/logout'
            except Exception as e:
                return f"Failed to restore backup: {str(e)}", 'alert alert-error', None

        elif action_type == 'delete-backup-btn':
            try:
                database.delete_backup_from_db(backup_id)
                database.log_audit_event(user_id=current_admin_id, action='delete_backup', target='system_settings',
                                         details=f"Admin {current_admin_username} deleted backup snapshot ID={backup_id}")
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

    database.log_audit_event(user_id=current_admin_id, action='download_database', target='system_settings',
                             details=f"Admin {current_admin_username} downloaded the active SQLite database file.")

    return dcc.send_file(config.DB_PATH)
