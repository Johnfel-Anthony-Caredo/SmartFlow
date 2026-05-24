"""
SMARTFLOW — Admin Scenario Library Page
View, delete, archive, or declare scenarios official.
"""

from dash import html, dcc, callback, Input, Output, State, ALL, ctx
from flask import session
import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_status_badge, create_button


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
        
    scenarios = database.get_scenarios(include_archived=True)
    
    rows = []
    for s in scenarios:
        official_badge = html.Span('OFFICIAL', className='status-badge status-active', style={'fontSize': '10px', 'padding': '2px 6px'}) if s['is_official'] else None
        archived_badge = html.Span('ARCHIVED', className='status-badge status-inactive', style={'fontSize': '10px', 'padding': '2px 6px'}) if s['is_archived'] else None
        
        actions = []
        # Toggle Official
        if s['is_official']:
            actions.append(
                html.Button(
                    'Remove Official',
                    id={'type': 'official-btn', 'index': s['id']},
                    className='btn btn-warning btn-sm',
                    style={'marginRight': '8px'}
                )
            )
        else:
            actions.append(
                html.Button(
                    'Make Official',
                    id={'type': 'official-btn', 'index': s['id']},
                    className='btn btn-success btn-sm',
                    style={'marginRight': '8px'}
                )
            )
            
        # Toggle Archived
        if s['is_archived']:
            actions.append(
                html.Button(
                    'Unarchive',
                    id={'type': 'archive-btn', 'index': s['id']},
                    className='btn btn-secondary btn-sm',
                    style={'marginRight': '8px'}
                )
            )
        else:
            actions.append(
                html.Button(
                    'Archive',
                    id={'type': 'archive-btn', 'index': s['id']},
                    className='btn btn-warning btn-sm',
                    style={'marginRight': '8px'}
                )
            )
            
        # Delete
        actions.append(
            html.Button(
                'Delete',
                id={'type': 'del-scenario-btn', 'index': s['id']},
                className='btn btn-danger btn-sm'
            )
        )
        
        rows.append(
            html.Tr(children=[
                html.Td(s['name']),
                html.Td(s['description'] or 'No description'),
                html.Td(s['traffic_density']),
                html.Td(s['weather_condition']),
                html.Td(children=[
                    html.Div(style={'display': 'flex', 'gap': '5px'}, children=[
                        official_badge or html.Span('USER-CREATED', className='status-badge status-pending', style={'fontSize': '10px', 'padding': '2px 6px'}),
                        archived_badge
                    ])
                ]),
                html.Td(children=actions)
            ])
        )
        
    table = html.Table(
        className='data-table',
        children=[
            html.Thead(children=[
                html.Tr(children=[
                    html.Th('Scenario Name'),
                    html.Th('Description'),
                    html.Th('Density'),
                    html.Th('Weather'),
                    html.Th('Classification'),
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
                                    html.H1(children='Scenario Library'),
                                    html.P(children='Manage, verify, publish, or archive simulation scenarios globally.'),
                                ]
                            ),
                            
                            html.Div(
                                id='admin-scenarios-alert',
                                className='alert alert-info hidden',
                                children=''
                            ),
                            
                            create_section(
                                title='Global Scenarios Library',
                                icon='fas fa-book',
                                children=[table]
                            ),
                            dcc.Location(id='admin-scenarios-redirect', refresh=True)
                        ]
                    )
                ]
            )
        ]
    )


@callback(
    [Output('admin-scenarios-alert', 'children'),
     Output('admin-scenarios-alert', 'className'),
     Output('admin-scenarios-redirect', 'pathname')],
    [Input({'type': 'official-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'archive-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'del-scenario-btn', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def handle_scenario_actions(official_clicks, archive_clicks, delete_clicks):
    triggered_id = ctx.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict):
        return '', 'alert alert-info hidden', None
        
    action_type = triggered_id.get('type')
    target_id = triggered_id.get('index')
    
    current_admin_id = session.get('user_id')
    current_admin_username = session.get('username')
    
    if not auth.is_admin():
        return 'Access Denied: Administrative action not authorized.', 'alert alert-error', '/login'
        
    scenario = database.get_scenario_by_id(target_id)
    if not scenario:
        return 'Scenario not found.', 'alert alert-error', None
        
    # Toggle Official
    if action_type == 'official-btn':
        new_official = 0 if scenario['is_official'] else 1
        database.update_scenario(target_id, is_official=new_official)
        action_name = "demoted official status of" if new_official == 0 else "promoted to official"
        database.log_audit_event(
            user_id=current_admin_id,
            action='update_scenario_official',
            target='scenarios',
            details=f"Admin {current_admin_username} {action_name} scenario '{scenario['name']}' (ID={target_id})"
        )
        return f"Scenario official status updated successfully.", 'alert alert-success', '/admin/scenarios'
        
    # Toggle Archive
    elif action_type == 'archive-btn':
        new_archived = 0 if scenario['is_archived'] else 1
        database.update_scenario(target_id, is_archived=new_archived)
        action_name = "unarchived" if new_archived == 0 else "archived"
        database.log_audit_event(
            user_id=current_admin_id,
            action='update_scenario_archive',
            target='scenarios',
            details=f"Admin {current_admin_username} {action_name} scenario '{scenario['name']}' (ID={target_id})"
        )
        return f"Scenario archive status updated successfully.", 'alert alert-success', '/admin/scenarios'
        
    # Delete scenario
    elif action_type == 'del-scenario-btn':
        database.delete_scenario(target_id)
        database.log_audit_event(
            user_id=current_admin_id,
            action='delete_scenario',
            target='scenarios',
            details=f"Admin {current_admin_username} permanently deleted scenario '{scenario['name']}' (ID={target_id})"
        )
        return f"Scenario '{scenario['name']}' permanently deleted.", 'alert alert-success', '/admin/scenarios'
        
    return '', 'alert alert-info hidden', None
