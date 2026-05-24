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
from components.common import create_section, create_status_badge, create_mini_stat

DENSITY_OPTIONS = [
    {'label': 'All Densities', 'value': 'all'},
    {'label': 'Low', 'value': 'Low'},
    {'label': 'Medium', 'value': 'Medium'},
    {'label': 'High', 'value': 'High'},
    {'label': 'Very High', 'value': 'Very High'},
]

TYPE_OPTIONS = [
    {'label': 'All Types', 'value': 'all'},
    {'label': 'Official', 'value': 'official'},
    {'label': 'User-Created', 'value': 'user'},
]

ARCHIVE_OPTIONS = [
    {'label': 'All States', 'value': 'all'},
    {'label': 'Active', 'value': 'active'},
    {'label': 'Archived', 'value': 'archived'},
]


def _density_badge(density):
    d = (density or 'Medium').lower().replace(' ', '-')
    return html.Span(density or 'Medium', className=f'density-badge density-{d}')


def _build_table(scenarios):
    if not scenarios:
        return html.Div(className='empty-state', children=[
            html.I(className='fas fa-map'),
            html.P('No scenarios found'),
            html.P('No scenarios match the current search or filter criteria.', className='empty-state-hint'),
        ])

    rows = []
    for s in scenarios:
        badges = []
        badges.append(html.Span('OFFICIAL', className='status-badge status-active')
                      if s['is_official'] else
                      html.Span('USER', className='status-badge status-inactive'))
        if s['is_archived']:
            badges.append(html.Span('ARCHIVED', className='status-badge status-stopped'))

        actions = []
        if s['is_official']:
            actions.append(html.Button('Demote', id={'type': 'official-btn', 'index': s['id']},
                                       className='btn btn-secondary btn-sm'))
        else:
            actions.append(html.Button('Make Official', id={'type': 'official-btn', 'index': s['id']},
                                       className='btn btn-success btn-sm'))

        if s['is_archived']:
            actions.append(html.Button('Restore', id={'type': 'archive-btn', 'index': s['id']},
                                       className='btn btn-success btn-sm'))
        else:
            actions.append(html.Button('Archive', id={'type': 'archive-btn', 'index': s['id']},
                                       className='btn btn-warning btn-sm'))

        actions.append(html.Button('Delete', id={'type': 'del-scenario-btn', 'index': s['id']},
                                   className='btn btn-danger btn-sm'))

        rows.append(html.Tr([
            html.Td(s['name']),
            html.Td(s['description'] or '—', style={'maxWidth': '240px', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'whiteSpace': 'nowrap'}),
            html.Td(_density_badge(s['traffic_density'])),
            html.Td(html.Div(className='actions-cell', children=badges)),
            html.Td(html.Div(className='actions-cell', children=actions)),
        ]))

    return html.Table(className='data-table', children=[
        html.Thead([html.Tr([
            html.Th('Scenario Name'), html.Th('Description'), html.Th('Density'),
            html.Th('Classification'), html.Th('Actions'),
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

    all_scenarios = database.get_scenarios(include_archived=True)
    total = len(all_scenarios)
    officials = sum(1 for s in all_scenarios if s['is_official'])
    archived = sum(1 for s in all_scenarios if s['is_archived'])
    active_count = total - archived

    return html.Div(className='app-layout', children=[
        create_header(),
        html.Div(className='app-body', children=[
            create_sidebar(),
            html.Main(className='main-content', children=[
                html.Div(className='page-header', children=[
                    html.H1('Scenario Library'),
                    html.P('Manage, verify, publish, or archive simulation scenarios globally.'),
                ]),

                html.Div(className='stats-row', children=[
                    create_mini_stat('Total', str(total), 'fas fa-layer-group', 'var(--info)'),
                    create_mini_stat('Official', str(officials), 'fas fa-certificate', 'var(--success)'),
                    create_mini_stat('Active', str(active_count), 'fas fa-play', 'var(--accent)'),
                    create_mini_stat('Archived', str(archived), 'fas fa-box-archive', 'var(--text-muted)'),
                ]),

                html.Div(id='admin-scenarios-alert', className='alert alert-info hidden'),

                html.Div(className='section', children=[
                    html.Div(className='section-header', children=[
                        html.I(className='fas fa-book'),
                        html.H3(className='section-title', children=[
                            html.Span('Global Scenarios Library', className='section-title-text'),
                            html.Small('Verify, publish, archive, or remove scenarios', className='section-subtitle'),
                        ]),
                    ]),
                    html.Div(className='filter-toolbar', children=[
                        html.Div(className='filter-group filter-group-wide', children=[
                            html.Label('Search', className='filter-label'),
                            dcc.Input(id='scenarios-search', type='text', placeholder='Search by name...',
                                      className='filter-input', debounce=True),
                        ]),
                        html.Div(className='filter-group', children=[
                            html.Label('Density', className='filter-label'),
                            dcc.Dropdown(id='scenarios-density-filter', options=DENSITY_OPTIONS, value='all',
                                         clearable=False, searchable=False,
                                         className='dash-dropdown dropdown-small'),
                        ]),
                        html.Div(className='filter-group', children=[
                            html.Label('Type', className='filter-label'),
                            dcc.Dropdown(id='scenarios-type-filter', options=TYPE_OPTIONS, value='all',
                                         clearable=False, searchable=False,
                                         className='dash-dropdown dropdown-small'),
                        ]),
                        html.Div(className='filter-group', children=[
                            html.Label('State', className='filter-label'),
                            dcc.Dropdown(id='scenarios-archive-filter', options=ARCHIVE_OPTIONS, value='all',
                                         clearable=False, searchable=False,
                                         className='dash-dropdown dropdown-small'),
                        ]),
                    ]),
                    html.Div(id='scenarios-table-container', className='section-content', children=[
                        _build_table(all_scenarios)
                    ]),
                ]),

                dcc.Location(id='admin-scenarios-redirect', refresh=True),
            ])
        ])
    ])


@callback(
    Output('scenarios-table-container', 'children'),
    [Input('scenarios-search', 'value'),
     Input('scenarios-density-filter', 'value'),
     Input('scenarios-type-filter', 'value'),
     Input('scenarios-archive-filter', 'value')]
)
def filter_scenarios_table(search, density, type_filter, archive_filter):
    scenarios = database.get_scenarios(include_archived=True)

    if search:
        q = search.lower()
        scenarios = [s for s in scenarios if q in (s['name'] or '').lower()]

    if density and density != 'all':
        scenarios = [s for s in scenarios if s['traffic_density'] == density]

    if type_filter and type_filter != 'all':
        if type_filter == 'official':
            scenarios = [s for s in scenarios if s['is_official']]
        else:
            scenarios = [s for s in scenarios if not s['is_official']]

    if archive_filter and archive_filter != 'all':
        if archive_filter == 'archived':
            scenarios = [s for s in scenarios if s['is_archived']]
        else:
            scenarios = [s for s in scenarios if not s['is_archived']]

    return _build_table(scenarios)


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

    if action_type == 'official-btn':
        new_official = 0 if scenario['is_official'] else 1
        database.update_scenario(target_id, is_official=new_official)
        action_name = "demoted" if new_official == 0 else "promoted to official"
        database.log_audit_event(user_id=current_admin_id, action='update_scenario_official', target='scenarios',
                                 details=f"Admin {current_admin_username} {action_name} scenario '{scenario['name']}' (ID={target_id})")
        return f"Scenario '{scenario['name']}' {action_name}.", 'alert alert-success', '/admin/scenarios'

    elif action_type == 'archive-btn':
        new_archived = 0 if scenario['is_archived'] else 1
        database.update_scenario(target_id, is_archived=new_archived)
        action_name = "restored" if new_archived == 0 else "archived"
        database.log_audit_event(user_id=current_admin_id, action='update_scenario_archive', target='scenarios',
                                 details=f"Admin {current_admin_username} {action_name} scenario '{scenario['name']}' (ID={target_id})")
        return f"Scenario '{scenario['name']}' {action_name}.", 'alert alert-success', '/admin/scenarios'

    elif action_type == 'del-scenario-btn':
        database.delete_scenario(target_id)
        database.log_audit_event(user_id=current_admin_id, action='delete_scenario', target='scenarios',
                                 details=f"Admin {current_admin_username} permanently deleted scenario '{scenario['name']}' (ID={target_id})")
        return f"Scenario '{scenario['name']}' permanently deleted.", 'alert alert-success', '/admin/scenarios'

    return '', 'alert alert-info hidden', None
