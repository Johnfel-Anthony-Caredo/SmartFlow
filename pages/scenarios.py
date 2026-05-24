"""
SMARTFLOW — Scenarios Page
Create, edit, and manage traffic simulation scenarios.
Includes JSON schema/field validation and audit logs.
"""

import json
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
from flask import session

import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_button, create_section, create_input, create_dropdown


def layout():
    # If not authenticated, let app.py handle redirection
    if not auth.is_authenticated():
        return html.Div()
        
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
                                    html.H1(children='Scenarios'),
                                    html.P(children='Create and manage traffic simulation scenarios'),
                                ]
                            ),
                            
                            html.Div(
                                id='scenario-alert',
                                className='alert alert-info hidden',
                                children=''
                            ),
                            
                            html.Div(
                                className='scenarios-layout',
                                children=[
                                    html.Div(
                                        className='scenarios-list-panel',
                                        children=[
                                            html.Div(
                                                className='panel-header',
                                                children=[
                                                    html.H3(children='Saved Scenarios'),
                                                    create_button(
                                                        id='new-scenario-btn',
                                                        text='New',
                                                        icon='fas fa-plus',
                                                        className='btn btn-primary btn-sm'
                                                    ),
                                                ]
                                            ),
                                            
                                            html.Div(
                                                id='scenarios-list',
                                                className='scenarios-list',
                                                children=[]
                                            ),
                                        ]
                                    ),
                                    
                                    html.Div(
                                        className='scenario-editor-panel',
                                        children=[
                                            html.H3(children='Scenario Configuration'),
                                            
                                            create_section(
                                                title='Basic Information',
                                                children=[
                                                    html.Div(
                                                        className='form-group',
                                                        children=[
                                                            html.Label(children='Scenario Name'),
                                                            create_input(
                                                                id='scenario-name',
                                                                placeholder='Enter scenario name',
                                                                value='New Scenario'
                                                            ),
                                                        ]
                                                    ),
                                                    
                                                    html.Div(
                                                        className='form-group',
                                                        children=[
                                                            html.Label(children='Description'),
                                                            dcc.Textarea(
                                                                id='scenario-description',
                                                                placeholder='Describe this scenario...',
                                                                className='textarea-field',
                                                                style={'width': '100%', 'height': '80px'}
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            
                                            create_section(
                                                title='Traffic Conditions',
                                                children=[
                                                    html.Div(
                                                        className='form-row',
                                                        children=[
                                                            html.Div(
                                                                className='form-group',
                                                                children=[
                                                                    html.Label(children='Traffic Density'),
                                                                    create_dropdown(
                                                                        id='traffic-density',
                                                                        options=[
                                                                            {'label': 'Low', 'value': 'Low'},
                                                                            {'label': 'Medium', 'value': 'Medium'},
                                                                            {'label': 'High', 'value': 'High'},
                                                                            {'label': 'Very High', 'value': 'Very High'},
                                                                        ],
                                                                        value='Medium'
                                                                    ),
                                                                ]
                                                            ),
                                                            
                                                            html.Div(
                                                                className='form-group',
                                                                children=[
                                                                    html.Label(children='Weather'),
                                                                    create_dropdown(
                                                                        id='weather',
                                                                        options=[
                                                                            {'label': 'Clear', 'value': 'Clear'},
                                                                            {'label': 'Rainy', 'value': 'Rainy'},
                                                                            {'label': 'Partly Cloudy', 'value': 'Partly Cloudy'},
                                                                            {'label': 'Night', 'value': 'Night'},
                                                                        ],
                                                                        value='Clear'
                                                                    ),
                                                                ]
                                                            ),
                                                        ]
                                                    ),
                                                    
                                                    html.Div(
                                                        className='form-row',
                                                        children=[
                                                            html.Div(
                                                                className='form-group',
                                                                children=[
                                                                    html.Label(children='Pedestrian Activity'),
                                                                    create_dropdown(
                                                                        id='pedestrian-activity',
                                                                        options=[
                                                                            {'label': 'Low', 'value': 'Low'},
                                                                            {'label': 'Medium', 'value': 'Medium'},
                                                                            {'label': 'High', 'value': 'High'},
                                                                        ],
                                                                        value='Medium'
                                                                    ),
                                                                ]
                                                            ),
                                                            
                                                            html.Div(
                                                                className='form-group',
                                                                children=[
                                                                    html.Label(children='Emergency Mode'),
                                                                    create_dropdown(
                                                                        id='emergency-mode',
                                                                        options=[
                                                                            {'label': 'Disabled', 'value': 'Disabled'},
                                                                            {'label': 'Enabled (1 Ambulance)', 'value': 'Enabled (1 Ambulance)'},
                                                                            {'label': 'Enabled (2 Vehicles)', 'value': 'Enabled (2 Vehicles)'},
                                                                        ],
                                                                        value='Disabled'
                                                                    ),
                                                                ]
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            
                                            create_section(
                                                title='Advanced Configurations (JSON Validation)',
                                                children=[
                                                    html.Div(
                                                        className='form-group',
                                                        style={'marginBottom': '10px'},
                                                        children=[
                                                            html.Label(children='Lane Closure Config (JSON)'),
                                                            dcc.Textarea(
                                                                id='lane-closure-config',
                                                                placeholder='{"enabled": false}',
                                                                value='{}',
                                                                className='textarea-field',
                                                                style={'width': '100%', 'height': '60px', 'fontFamily': 'monospace'}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='form-group',
                                                        style={'marginBottom': '10px'},
                                                        children=[
                                                            html.Label(children='Construction Config (JSON)'),
                                                            dcc.Textarea(
                                                                id='construction-config',
                                                                placeholder='{"enabled": false}',
                                                                value='{}',
                                                                className='textarea-field',
                                                                style={'width': '100%', 'height': '60px', 'fontFamily': 'monospace'}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='form-group',
                                                        style={'marginBottom': '10px'},
                                                        children=[
                                                            html.Label(children='Accident Config (JSON)'),
                                                            dcc.Textarea(
                                                                id='accident-config',
                                                                placeholder='{"enabled": false}',
                                                                value='{}',
                                                                className='textarea-field',
                                                                style={'width': '100%', 'height': '60px', 'fontFamily': 'monospace'}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='form-group',
                                                        style={'marginBottom': '10px'},
                                                        children=[
                                                            html.Label(children='Flooding Config (JSON)'),
                                                            dcc.Textarea(
                                                                id='flooding-config',
                                                                placeholder='{"enabled": false}',
                                                                value='{}',
                                                                className='textarea-field',
                                                                style={'width': '100%', 'height': '60px', 'fontFamily': 'monospace'}
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='form-group',
                                                        style={'marginBottom': '10px'},
                                                        children=[
                                                            html.Label(children='Constraints Config (JSON)'),
                                                            dcc.Textarea(
                                                                id='constraints-config',
                                                                placeholder='{"safety_limit": 50}',
                                                                value='{}',
                                                                className='textarea-field',
                                                                style={'width': '100%', 'height': '60px', 'fontFamily': 'monospace'}
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            
                                            html.Div(
                                                className='form-actions',
                                                children=[
                                                    create_button(
                                                        id='save-scenario-btn',
                                                        text='Save Scenario',
                                                        icon='fas fa-save',
                                                        className='btn btn-primary'
                                                    ),
                                                    create_button(
                                                        id='delete-scenario-btn',
                                                        text='Delete',
                                                        icon='fas fa-trash',
                                                        className='btn btn-danger'
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            dcc.Store(id='selected-scenario-id', data=None)
                        ]
                    ),
                ]
            ),
        ]
    )


# ─── Callbacks ────────────────────────────────────────────────────────

@callback(
    Output('scenarios-list', 'children'),
    [Input('selected-scenario-id', 'data'),
     Input('scenario-alert', 'children')]
)
def update_scenarios_list(selected_id, _alert):
    scenarios = database.get_scenarios()
    items = []
    for s in scenarios:
        is_selected = (s['id'] == selected_id)
        items.append(
            html.Div(
                id={'type': 'scenario-item', 'index': s['id']},
                className=f'scenario-item {"active" if is_selected else ""}',
                style={'cursor': 'pointer', 'padding': '12px', 'borderBottom': '1px solid #dee2e6'},
                children=[
                    html.Div(className='scenario-name', style={'fontWeight': '600'}, children=s['name']),
                    html.Div(className='scenario-meta', style={'fontSize': '12px', 'color': '#64748b'},
                             children=f"{s['traffic_density']} Density, {s['weather_condition']}")
                ]
            )
        )
    return items


@callback(
    [Output('scenario-name', 'value'),
     Output('scenario-description', 'value'),
     Output('traffic-density', 'value'),
     Output('weather', 'value'),
     Output('pedestrian-activity', 'value'),
     Output('emergency-mode', 'value'),
     Output('lane-closure-config', 'value'),
     Output('construction-config', 'value'),
     Output('accident-config', 'value'),
     Output('flooding-config', 'value'),
     Output('constraints-config', 'value')],
    Input('selected-scenario-id', 'data')
)
def load_scenario(scenario_id):
    if scenario_id is None:
        return 'New Scenario', '', 'Medium', 'Clear', 'Medium', 'Disabled', '{}', '{}', '{}', '{}', '{}'
        
    s = database.get_scenario_by_id(scenario_id)
    if not s:
        return 'New Scenario', '', 'Medium', 'Clear', 'Medium', 'Disabled', '{}', '{}', '{}', '{}', '{}'
        
    # Fetch constraints
    constraints = database.get_scenario_constraints(scenario_id)
    constraints_json = '{}'
    if constraints:
        # Load constraints into a serialized dict
        c_dict = {c['constraint_type']: json.loads(c['config_json']) for c in constraints}
        constraints_json = json.dumps(c_dict, indent=2)
        
    return (
        s['name'],
        s['description'] or '',
        s['traffic_density'],
        s['weather_condition'],
        s['pedestrian_density'] or 'Medium',
        s['emergency_mode'] or 'Disabled',
        s['lane_closure_config'] or '{}',
        s['construction_config'] or '{}',
        s['accident_config'] or '{}',
        s['flooding_config'] or '{}',
        constraints_json
    )


@callback(
    Output('selected-scenario-id', 'data'),
    [Input('new-scenario-btn', 'n_clicks'),
     Input({'type': 'scenario-item', 'index': ALL}, 'n_clicks')],
    State('selected-scenario-id', 'data'),
    prevent_initial_call=True
)
def handle_scenario_selection(new_clicks, item_clicks, current_id):
    triggered_id = ctx.triggered_id
    if not triggered_id:
        return current_id
        
    if triggered_id == 'new-scenario-btn':
        return None
        
    if isinstance(triggered_id, dict) and triggered_id.get('type') == 'scenario-item':
        return triggered_id.get('index')
        
    return current_id


@callback(
    [Output('scenario-alert', 'children'),
     Output('scenario-alert', 'className'),
     Output('selected-scenario-id', 'data', allow_duplicate=True)],
    [Input('save-scenario-btn', 'n_clicks'),
     Input('delete-scenario-btn', 'n_clicks')],
    [State('selected-scenario-id', 'data'),
     State('scenario-name', 'value'),
     State('scenario-description', 'value'),
     State('traffic-density', 'value'),
     State('weather', 'value'),
     State('pedestrian-activity', 'value'),
     State('emergency-mode', 'value'),
     State('lane-closure-config', 'value'),
     State('construction-config', 'value'),
     State('accident-config', 'value'),
     State('flooding-config', 'value'),
     State('constraints-config', 'value')],
    prevent_initial_call=True
)
def handle_save_delete(save_clicks, delete_clicks, selected_id, name, desc, density, weather, pedestrian, emergency,
                        lane_closure_config, construction_config, accident_config, flooding_config, constraints_config):
    triggered_id = ctx.triggered_id
    
    # Check active session
    if not auth.validate_current_session():
        auth.clear_session()
        return 'Session expired. Please log in again.', 'alert alert-error', no_update
        
    current_user_id = session.get('user_id')
    current_username = session.get('username')
    
    # ─── HANDLE DELETE ────────────────────────────────────────────────
    if triggered_id == 'delete-scenario-btn':
        if selected_id is None:
            return 'No scenario selected to delete.', 'alert alert-error', no_update
            
        # Check permission
        if not auth.has_permission('scenarios', 'delete'):
            return 'Access Denied: You do not have permission to delete scenarios.', 'alert alert-error', no_update
            
        s = database.get_scenario_by_id(selected_id)
        if not s:
            return 'Scenario not found.', 'alert alert-error', no_update
            
        # Delete constraints and scenario
        database.delete_scenario_constraints(selected_id)
        database.delete_scenario(selected_id)
        
        # Log audit event
        database.log_audit_event(
            user_id=current_user_id,
            action='delete_scenario',
            target='scenarios',
            details=f"User {current_username} deleted scenario '{s['name']}' (ID={selected_id})"
        )
        
        return f"Scenario '{s['name']}' deleted successfully.", 'alert alert-success', None
        
    # ─── HANDLE SAVE ──────────────────────────────────────────────────
    elif triggered_id == 'save-scenario-btn':
        if not name:
            return 'Scenario name cannot be empty.', 'alert alert-error', no_update
            
        # Check permissions
        action_name = 'edit' if selected_id else 'create'
        if not auth.has_permission('scenarios', action_name):
            return f"Access Denied: You do not have permission to {action_name} scenarios.", 'alert alert-error', no_update
            
        # JSON config parsing & validation
        try:
            parsed_lane = json.loads(lane_closure_config or '{}')
        except Exception as e:
            return f"Invalid JSON in Lane Closure Config: {str(e)}", 'alert alert-error', no_update
            
        try:
            parsed_const = json.loads(construction_config or '{}')
        except Exception as e:
            return f"Invalid JSON in Construction Config: {str(e)}", 'alert alert-error', no_update
            
        try:
            parsed_acc = json.loads(accident_config or '{}')
        except Exception as e:
            return f"Invalid JSON in Accident Config: {str(e)}", 'alert alert-error', no_update
            
        try:
            parsed_flood = json.loads(flooding_config or '{}')
        except Exception as e:
            return f"Invalid JSON in Flooding Config: {str(e)}", 'alert alert-error', no_update
            
        try:
            parsed_constraints = json.loads(constraints_config or '{}')
            if not isinstance(parsed_constraints, dict):
                return "Constraints Config must be a JSON object mapping constraint types to configs.", 'alert alert-error', no_update
        except Exception as e:
            return f"Invalid JSON in Constraints Config: {str(e)}", 'alert alert-error', no_update
            
        # Perform DB insert or update
        if selected_id:
            # Update scenario
            database.update_scenario(
                selected_id,
                name=name,
                description=desc,
                traffic_density=density,
                pedestrian_density=pedestrian,
                emergency_mode=emergency,
                weather_condition=weather,
                lane_closure_config=json.dumps(parsed_lane),
                construction_config=json.dumps(parsed_const),
                accident_config=json.dumps(parsed_acc),
                flooding_config=json.dumps(parsed_flood)
            )
            
            # Update constraints
            database.delete_scenario_constraints(selected_id)
            for c_type, c_cfg in parsed_constraints.items():
                database.save_scenario_constraint(selected_id, c_type, json.dumps(c_cfg))
                
            # Log audit event
            database.log_audit_event(
                user_id=current_user_id,
                action='update_scenario',
                target='scenarios',
                details=f"User {current_username} updated scenario '{name}' (ID={selected_id})"
            )
            
            return f"Scenario '{name}' updated successfully.", 'alert alert-success', selected_id
        else:
            # Create scenario
            new_id = database.create_scenario(
                name=name,
                description=desc,
                traffic_density=density,
                pedestrian_density=pedestrian,
                emergency_mode=emergency,
                weather_condition=weather,
                lane_closure_config=json.dumps(parsed_lane),
                construction_config=json.dumps(parsed_const),
                accident_config=json.dumps(parsed_acc),
                flooding_config=json.dumps(parsed_flood),
                created_by=current_user_id
            )
            
            # Save constraints
            for c_type, c_cfg in parsed_constraints.items():
                database.save_scenario_constraint(new_id, c_type, json.dumps(c_cfg))
                
            # Log audit event
            database.log_audit_event(
                user_id=current_user_id,
                action='create_scenario',
                target='scenarios',
                details=f"User {current_username} created scenario '{name}' (ID={new_id})"
            )
            
            return f"Scenario '{name}' created successfully.", 'alert alert-success', new_id
            
    return '', 'alert alert-info hidden', no_update
