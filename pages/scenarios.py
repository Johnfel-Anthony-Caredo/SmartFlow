"""
SMARTFLOW — Scenarios Library Page
Premium dark scenario library with category rail, card/table views,
filter toolbar, and drawer-based inspector + compact editor.
"""

import json
from dash import html, dcc, callback, Input, Output, State, ALL, ctx, no_update
from flask import session

import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_mini_stat


# ─── Filter/Sort Constants ───────────────────────────────────────────

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

STATE_OPTIONS = [
    {'label': 'All States', 'value': 'all'},
    {'label': 'Active', 'value': 'active'},
    {'label': 'Archived', 'value': 'archived'},
]

SORT_OPTIONS = [
    {'label': 'Name A-Z', 'value': 'name_asc'},
    {'label': 'Name Z-A', 'value': 'name_desc'},
    {'label': 'Newest First', 'value': 'date_desc'},
    {'label': 'Oldest First', 'value': 'date_asc'},
    {'label': 'Density (High-Low)', 'value': 'density_desc'},
]

DENSITY_ORDER = {'Very High': 4, 'High': 3, 'Medium': 2, 'Low': 1}


# ─── Helper Functions ────────────────────────────────────────────────

def _density_color(density):
    m = {
        'Low': 'var(--info)',
        'Medium': 'var(--warning)',
        'High': 'var(--error)',
        'Very High': '#ff6b6b',
    }
    return m.get(density, 'var(--text-muted)')


def _scenario_badge(badge_type, label=None):
    m = {
        'official': ('scenario-badge scenario-badge-official', 'Official'),
        'user': ('scenario-badge scenario-badge-user', 'User'),
        'archived': ('scenario-badge scenario-badge-archived', 'Archived'),
        'active': ('scenario-badge scenario-badge-active', 'Active'),
    }
    cls, default_label = m.get(badge_type, ('scenario-badge', badge_type))
    return html.Span(label or default_label, className=cls)


def _density_badge(density):
    d = (density or 'Medium').lower().replace(' ', '-')
    return html.Span(density or 'Medium', className=f'density-badge density-{d}')


def _cat_match(s, cat_key):
    if cat_key == 'all':
        return True
    if cat_key == 'official':
        return s.get('is_official')
    if cat_key == 'user':
        return not s.get('is_official')
    if cat_key == 'active':
        return not s.get('is_archived')
    if cat_key == 'archived':
        return s.get('is_archived')
    return True


def _filter_match(s, search, density, type_f, state_f, category):
    if category and not _cat_match(s, category):
        return False
    if search and search not in (s.get('name') or '').lower():
        return False
    if density and density != 'all' and s.get('traffic_density') != density:
        return False
    if type_f and type_f != 'all':
        if type_f == 'official' and not s.get('is_official'):
            return False
        if type_f == 'user' and s.get('is_official'):
            return False
    if state_f and state_f != 'all':
        if state_f == 'archived' and not s.get('is_archived'):
            return False
        if state_f == 'active' and s.get('is_archived'):
            return False
    return True


def _sort_scenarios(scenarios, sort_val):
    if sort_val == 'name_asc':
        return sorted(scenarios, key=lambda s: (s.get('name') or '').lower())
    if sort_val == 'name_desc':
        return sorted(scenarios, key=lambda s: (s.get('name') or '').lower(), reverse=True)
    if sort_val == 'date_desc':
        return sorted(scenarios, key=lambda s: s.get('updated_at') or s.get('created_at') or '', reverse=True)
    if sort_val == 'date_asc':
        return sorted(scenarios, key=lambda s: s.get('updated_at') or s.get('created_at') or '')
    if sort_val == 'density_desc':
        return sorted(scenarios, key=lambda s: DENSITY_ORDER.get(s.get('traffic_density'), 0), reverse=True)
    return scenarios


# ─── Card Builder ────────────────────────────────────────────────────

def _build_scenario_card(s, selected_id):
    classes = ['scenario-item-card']
    if s.get('is_archived'):
        classes.append('archived')
    if s['id'] == selected_id:
        classes.append('selected')

    badges = []
    badges.append(_scenario_badge('official') if s['is_official'] else _scenario_badge('user'))
    if s['is_archived']:
        badges.append(_scenario_badge('archived'))

    updated = s.get('updated_at') or s.get('created_at') or '—'
    if updated and len(updated) > 10:
        updated = updated[:10]

    return html.Div(
        className=' '.join(classes),
        id={'type': 'scenario-card', 'index': s['id']},
        children=[
            html.Div(className='scenario-card-top', children=[
                html.Div(s['name'], className='scenario-card-name'),
                html.Div(className='scenario-card-badges', children=badges),
            ]),
            html.Div(s.get('description') or 'No description provided.',
                     className='scenario-card-desc'),
            html.Div(className='scenario-card-meta', children=[
                html.Div(className='scenario-card-meta-item', children=[
                    _density_badge(s.get('traffic_density')),
                ]),
                html.Div(className='scenario-card-meta-item', children=[
                    html.I(className='fas fa-calendar-alt'),
                    updated,
                ]),
            ]),
            html.Div(className='scenario-card-actions', children=[
                html.Button(html.I(className='fas fa-eye'),
                            id={'type': 'view-scenario-btn', 'index': s['id']},
                            className='icon-btn-sm edit', title='View Details'),
                html.Button(html.I(className='fas fa-pen'),
                            id={'type': 'edit-scenario-btn', 'index': s['id']},
                            className='icon-btn-sm activate', title='Edit Scenario'),
                html.Button(html.I(className='fas fa-copy'),
                            id={'type': 'duplicate-scenario-btn', 'index': s['id']},
                            className='icon-btn-sm', title='Duplicate'),
                *( [
                    html.Button(
                        html.I(className='fas fa-arrow-down' if s['is_official'] else 'fas fa-arrow-up'),
                        id={'type': 'official-btn', 'index': s['id']},
                        className='icon-btn-sm activate',
                        title='Demote' if s['is_official'] else 'Make Official'),
                    html.Button(
                        html.I(className='fas fa-box-open' if s['is_archived'] else 'fas fa-box-archive'),
                        id={'type': 'archive-btn', 'index': s['id']},
                        className='icon-btn-sm deactivate',
                        title='Restore' if s['is_archived'] else 'Archive')
                ] if auth.is_admin() else [] ),
                html.Span(className='action-sep'),
                html.Button(html.I(className='fas fa-trash'),
                            id={'type': 'del-scenario-btn', 'index': s['id']},
                            className='icon-btn-sm danger', title='Delete'),
            ]),
        ]
    )


# ─── Table Builder ───────────────────────────────────────────────────

def _build_scenario_table(scenarios, selected_id):
    if not scenarios:
        return html.Div(className='empty-state', children=[
            html.I(className='fas fa-map'),
            html.P('No scenarios found'),
            html.P('No scenarios match the current filter criteria.',
                   className='empty-state-hint'),
        ])

    rows = []
    for s in scenarios:
        row_class = 'selected' if s['id'] == selected_id else ''
        if s.get('is_archived'):
            row_class += ' archived'

        dot_cls = 'archived' if s.get('is_archived') else ('official' if s['is_official'] else 'user')

        updated = s.get('updated_at') or s.get('created_at') or '—'
        if updated and len(updated) > 10:
            updated = updated[:10]

        rows.append(html.Tr(
            className=row_class.strip(),
            id={'type': 'scenario-table-row', 'index': s['id']},
            children=[
                html.Td(html.Div(className='scenario-name-cell', children=[
                    html.Span(className=f'scenario-dot {dot_cls}'),
                    html.Span(s['name'], className='scenario-row-name'),
                ])),
                html.Td(s.get('description') or '—',
                        style={'maxWidth': '260px', 'overflow': 'hidden',
                               'textOverflow': 'ellipsis', 'whiteSpace': 'nowrap'}),
                html.Td(_density_badge(s.get('traffic_density'))),
                html.Td(_scenario_badge('official') if s['is_official'] else _scenario_badge('user')),
                html.Td(_scenario_badge('archived') if s['is_archived'] else _scenario_badge('active')),
                html.Td(updated),
                html.Td(html.Div(className='actions-cell', children=[
                    html.Button(html.I(className='fas fa-eye'),
                                id={'type': 'view-scenario-btn', 'index': s['id']},
                                className='icon-btn-sm edit', title='View Details'),
                    html.Button(html.I(className='fas fa-pen'),
                                id={'type': 'edit-scenario-btn', 'index': s['id']},
                                className='icon-btn-sm activate', title='Edit Scenario'),
                    html.Button(html.I(className='fas fa-copy'),
                                id={'type': 'duplicate-scenario-btn', 'index': s['id']},
                                className='icon-btn-sm', title='Duplicate'),
                    *( [
                        html.Button(html.I(className='fas fa-arrow-down' if s['is_official'] else 'fas fa-arrow-up'),
                                    id={'type': 'official-btn', 'index': s['id']},
                                    className='icon-btn-sm activate',
                                    title='Demote' if s['is_official'] else 'Make Official'),
                        html.Button(html.I(className='fas fa-box-open' if s['is_archived'] else 'fas fa-box-archive'),
                                    id={'type': 'archive-btn', 'index': s['id']},
                                    className='icon-btn-sm deactivate',
                                    title='Restore' if s['is_archived'] else 'Archive')
                    ] if auth.is_admin() else [] ),
                    html.Span(className='action-sep'),
                    html.Button(html.I(className='fas fa-trash'),
                                id={'type': 'del-scenario-btn', 'index': s['id']},
                                className='icon-btn-sm danger', title='Delete'),
                ])),
            ]
        ))

    return html.Div(className='scenario-table-wrap', children=[
        html.Table(className='scenario-table', children=[
            html.Thead(html.Tr([
                html.Th('Scenario Name'), html.Th('Description'), html.Th('Density'),
                html.Th('Type'), html.Th('State'), html.Th('Updated'), html.Th('Actions'),
            ])),
            html.Tbody(rows),
        ])
    ])


# ─── Category Panel ─────────────────────────────────────────────────

def _build_category_panel(scenarios, active_cat, densities):
    cats = [
        ('all', 'fas fa-layer-group', 'All Scenarios'),
        ('official', 'fas fa-certificate', 'Official'),
        ('user', 'fas fa-user', 'User-Created'),
        ('active', 'fas fa-play', 'Active'),
        ('archived', 'fas fa-box-archive', 'Archived'),
    ]

    cat_items = []
    for key, icon, label in cats:
        count = sum(1 for s in scenarios if _cat_match(s, key))
        cat_items.append(html.Div(
            className=f'scenario-cat-item{" active" if active_cat == key else ""}',
            id={'type': 'cat-filter', 'index': key},
            children=[
                html.I(className=icon),
                html.Span(label),
                html.Span(str(count), className='cat-item-count'),
            ]
        ))

    tree_items = []
    for d in densities:
        count = sum(1 for s in scenarios
                    if _filter_match(s, search=None, density=d, type_f=None, state_f=None, category=active_cat))
        tree_items.append(html.Div(
            className='scenario-tree-item',
            id={'type': 'density-filter-btn', 'index': d},
            children=[
                html.I(className='fas fa-circle',
                       style={'fontSize': '6px', 'color': _density_color(d)}),
                html.Span(d if d else 'No Density'),
                html.Span(str(count), style={'marginLeft': 'auto', 'fontSize': '10px',
                                             'color': 'var(--text-muted)'}),
            ]
        ))

    return [
        html.Div(className='scenario-category-card', children=[
            html.Div(className='scenario-category-header', children=[
                html.I(className='fas fa-folder-tree'),
                html.Span('Categories'),
                html.Span(str(len(scenarios)), className='cat-count'),
            ]),
            html.Div(className='scenario-category-list', children=cat_items),
        ]),
        html.Div(className='scenario-category-card', children=[
            html.Div(className='scenario-category-header', children=[
                html.I(className='fas fa-traffic-light'),
                html.Span('Traffic Density'),
            ]),
            html.Div(className='scenario-category-list', children=tree_items),
        ]),
    ]


# ─── Detail Panel (View Mode) ───────────────────────────────────────

def _build_detail_panel(scenario):
    if not scenario:
        return [
            html.Div(className='scenario-detail-header', children=[
                html.Div(className='scenario-detail-title-group', children=[
                    html.Div(className='scenario-detail-icon',
                             children=[html.I(className='fas fa-book-open')]),
                    html.Div(className='scenario-detail-title', children=[
                        html.H2('No Scenario Selected'),
                    ]),
                ]),
                html.Button(html.I(className='fas fa-times'),
                            id='scn-detail-close',
                            className='scenario-detail-close'),
            ]),
            html.Div(className='scenario-detail-body', children=[
                html.Div(className='scenario-detail-empty', children=[
                    html.I(className='fas fa-book-open'),
                    html.H3('No Scenario Selected'),
                    html.P('Click on a scenario from the library to view its full details and configuration here.'),
                ]),
            ]),
            html.Div(className='scenario-detail-footer', style={'display': 'none'}, children=[
                html.Button('Cancel', id='scn-edit-cancel'),
                html.Button('Save', id='scn-edit-save'),
            ]),
        ]

    is_official = scenario.get('is_official')
    is_archived = scenario.get('is_archived')

    icon_cls = 'archived' if is_archived else ('official' if is_official else 'user')
    icon_fa = 'fa-box-archive' if is_archived else ('fa-certificate' if is_official else 'fa-user')

    updated = scenario.get('updated_at') or scenario.get('created_at') or '—'
    created = scenario.get('created_at') or '—'

    badges = []
    badges.append(_scenario_badge('official') if is_official else _scenario_badge('user'))
    if is_archived:
        badges.append(_scenario_badge('archived'))
    else:
        badges.append(_scenario_badge('active'))

    density = scenario.get('traffic_density') or 'Medium'
    ped_density = scenario.get('pedestrian_density') or 'Medium'
    emergency = scenario.get('emergency_mode') or 'Disabled'

    return [
        html.Div(className='scenario-detail-header', children=[
            html.Div(className='scenario-detail-title-group', children=[
                html.Div(className=f'scenario-detail-icon {icon_cls}',
                         children=[html.I(className=f'fas {icon_fa}')]),
                html.Div(className='scenario-detail-title', children=[
                    html.H2(scenario.get('name', 'Unnamed')),
                    html.Div(className='scenario-detail-meta-line', children=[
                        html.Span([html.I(className='fas fa-calendar'),
                                   f' Updated {updated[:10]}' if len(str(updated)) > 10 else updated]),
                        html.Span([html.I(className='fas fa-id-card'),
                                   f' ID: {scenario.get("id")}']),
                    ]),
                ]),
            ]),
            html.Button(html.I(className='fas fa-pen'),
                        id={'type': 'drawer-edit-btn', 'index': scenario['id']},
                        className='icon-btn-sm activate',
                        style={'width': '32px', 'height': '32px', 'marginRight': '8px'},
                        title='Edit'),
            html.Button(html.I(className='fas fa-times'),
                        id='scn-detail-close',
                        className='scenario-detail-close'),
        ]),

        html.Div(className='scenario-detail-body', children=[
            html.Div(className='scenario-detail-badges', children=badges),
            html.Div(scenario.get('description') or 'No description provided.',
                     className='scenario-detail-desc'),

            html.Div(className='scenario-detail-section', children=[
                html.Div(className='scenario-detail-section-header', children=[
                    html.I(className='fas fa-sliders-h'),
                    html.H3('Configuration Summary'),
                ]),
                html.Div(className='scenario-detail-section-body', children=[
                    html.Div(className='scenario-detail-grid', children=[
                        html.Div(className='scenario-detail-item', children=[
                            html.Span('Traffic Density', className='detail-label'),
                            html.Span(_density_badge(density)),
                        ]),
                        html.Div(className='scenario-detail-item', children=[
                            html.Span('Pedestrian Activity', className='detail-label'),
                            html.Span(ped_density, className='detail-value'),
                        ]),
                        html.Div(className='scenario-detail-item', children=[
                            html.Span('Emergency Mode', className='detail-label'),
                            html.Span(emergency, className='detail-value'),
                        ]),
                        html.Div(className='scenario-detail-item', children=[
                            html.Span('Created', className='detail-label'),
                            html.Span(created[:10] if len(str(created)) > 10 else created,
                                      className='detail-value'),
                        ]),
                    ]),
                ]),
            ]),

            html.Div(className='scenario-preview-card', children=[
                html.Div(className='scenario-preview-header', children=[
                    html.I(className='fas fa-diagram-project'),
                    html.Span('Traffic Schematic'),
                ]),
                html.Div(className='scenario-preview-body', children=[
                    html.Div(className='scenario-schematic', children=[
                        html.Div(className='scenario-schematic-road', children=[
                            html.Div(className=f'scenario-schematic-lane{" active" if density in ("High","Very High") else ""}'),
                            html.Div(className=f'scenario-schematic-lane{" active" if density in ("Medium","High","Very High") else ""}'),
                        ]),
                        html.Div(className='scenario-schematic-intersection'),
                        html.Div(className='scenario-schematic-road', children=[
                            html.Div(className=f'scenario-schematic-lane{" active" if density != "Low" else ""}'),
                            html.Div(className=f'scenario-schematic-lane{" active" if density in ("High","Very High") else ""}'),
                        ]),
                        html.Div(className='scenario-schematic-labels', children=[
                            html.Span('N', className=f'scenario-schematic-label{" active" if density in ("High","Very High") else ""}'),
                            html.Span('E', className=f'scenario-schematic-label{" active" if density in ("Medium","High","Very High") else ""}'),
                            html.Span('S', className=f'scenario-schematic-label{" active" if density != "Low" else ""}'),
                            html.Span('W', className=f'scenario-schematic-label{" active" if density in ("High","Very High") else ""}'),
                        ]),
                    ]),
                ]),
            ]),
        ]),

        html.Div(className='scenario-detail-footer', children=[
            *( [
                html.Button('Demote' if is_official else 'Make Official',
                            id={'type': 'official-btn', 'index': scenario['id']},
                            className='btn btn-success' if not is_official else 'btn btn-secondary',
                            style={'flex': '1'}),
                html.Button('Restore' if is_archived else 'Archive',
                            id={'type': 'archive-btn', 'index': scenario['id']},
                            className='btn btn-warning' if not is_archived else 'btn btn-success',
                            style={'flex': '1'})
            ] if auth.is_admin() else [] ),
            html.Button([html.I(className='fas fa-pen'), ' Edit'],
                        id={'type': 'drawer-edit-btn', 'index': scenario['id']},
                        className='btn btn-success', style={'flex': '1'}),
            html.Button([html.I(className='fas fa-copy'), ' Duplicate'],
                        id={'type': 'duplicate-scenario-btn', 'index': scenario['id']},
                        className='btn btn-secondary', style={'flex': '1'}),
            html.Button([html.I(className='fas fa-trash'), ' Delete'],
                        id={'type': 'del-scenario-btn', 'index': scenario['id']},
                        className='btn btn-danger', style={'flex': '1'}),
        ]),
    ]


# ─── Disruption Block Builder ───────────────────────────────────────

def _build_disruption_block(title, id_prefix, icon, fields):
    return html.Div(
        style={
            'background': 'var(--bg-input)',
            'padding': '12px',
            'borderRadius': 'var(--radius-sm)',
            'border': '1px solid var(--border-subtle)',
        },
        children=[
            html.Div(
                style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center',
                    'marginBottom': '8px'
                },
                children=[
                    html.Div(
                        style={'display': 'flex', 'alignItems': 'center', 'gap': '8px'},
                        children=[
                            html.I(className=f'fas {icon}',
                                   style={'color': 'var(--accent)', 'fontSize': '13px'}),
                            html.Span(title, style={
                                'fontSize': '12px', 'fontWeight': '600',
                                'color': 'var(--text-primary)'
                            }),
                        ]
                    ),
                    html.Div(className='toggle-switch', children=[
                        dcc.Checklist(
                            id=f'{id_prefix}-toggle',
                            options=[{'label': '', 'value': 'enabled'}],
                            value=[],
                            inline=True,
                            inputClassName='toggle-input',
                            labelClassName='toggle-label'
                        )
                    ])
                ]
            ),
            html.Div(
                id=f'{id_prefix}-options',
                style={
                    'display': 'grid',
                    'gridTemplateColumns': '1fr 1fr',
                    'gap': '10px',
                    'marginTop': '8px',
                    'paddingTop': '8px',
                    'borderTop': '1px solid var(--border-subtle)'
                },
                children=fields
            )
        ]
    )


# ─── Edit Panel (Edit/Create Mode) ──────────────────────────────────

def _build_edit_panel(scenario):
    is_new = scenario is None
    s = scenario or {}

    if is_new:
        defaults = {
            'name': '', 'description': '',
            'density': 'Medium', 'pedestrian': 'Medium', 'emergency': 'Disabled',
            'lane_toggle': [], 'lane_app': 'north', 'lane_lanes': 1,
            'const_toggle': [], 'const_app': 'north', 'const_spd': 0.5,
            'acc_toggle': [], 'acc_app': 'north', 'acc_sev': 'major',
            'flood_toggle': [], 'flood_app': 'all', 'flood_sev': 'major',
            'constraints': '{}',
        }
    else:
        def safe_loads(json_str):
            try:
                return json.loads(json_str or '{}')
            except Exception:
                return {}

        lane_cfg = safe_loads(s.get('lane_closure_config'))
        const_cfg = safe_loads(s.get('construction_config'))
        acc_cfg = safe_loads(s.get('accident_config'))
        flood_cfg = safe_loads(s.get('flooding_config'))

        constraints = database.get_scenario_constraints(s['id'])
        constraints_json = '{}'
        if constraints:
            c_dict = {c['constraint_type']: json.loads(c['config_json'])
                      for c in constraints}
            constraints_json = json.dumps(c_dict, indent=2)

        defaults = {
            'name': s.get('name', ''),
            'description': s.get('description', ''),
            'density': s.get('traffic_density', 'Medium'),
            'pedestrian': s.get('pedestrian_density', 'Medium'),
            'emergency': s.get('emergency_mode', 'Disabled'),
            'lane_toggle': ['enabled'] if lane_cfg.get('enabled') else [],
            'lane_app': lane_cfg.get('approach', 'north'),
            'lane_lanes': lane_cfg.get('lanes_closed', 1),
            'const_toggle': ['enabled'] if const_cfg.get('enabled') else [],
            'const_app': const_cfg.get('approach', 'north'),
            'const_spd': const_cfg.get('speed_reduction', 0.5),
            'acc_toggle': ['enabled'] if acc_cfg.get('enabled') else [],
            'acc_app': acc_cfg.get('approach', 'north'),
            'acc_sev': acc_cfg.get('severity', 'major'),
            'flood_toggle': ['enabled'] if flood_cfg.get('enabled') else [],
            'flood_app': flood_cfg.get('approach', 'all'),
            'flood_sev': flood_cfg.get('severity', 'major'),
            'constraints': constraints_json,
        }

    def fld(key, default_val):
        return defaults.get(key, default_val)

    header_title = 'Create New Scenario' if is_new else f'Edit: {fld("name", "Unnamed")}'

    # ── Disruption dropdowns ──
    direction_opts = [{'label': a, 'value': a.lower()} for a in ['North', 'South', 'East', 'West']]

    def _dd(id, opts, val):
        return dcc.Dropdown(id=id, options=opts, value=val, clearable=False,
                            searchable=False, className='dash-dropdown dropdown-small')

    def _inp(id, type, val, **kw):
        return dcc.Input(id=id, type=type, value=val, className='input-field', **kw)

    return [
        html.Div(className='scenario-detail-header', children=[
            html.Div(className='scenario-detail-title-group', children=[
                html.Div(className='scenario-detail-icon user',
                         children=[html.I(className='fas fa-pen')]),
                html.Div(className='scenario-detail-title', children=[
                    html.H2(header_title),
                ]),
            ]),
            html.Button(html.I(className='fas fa-times'),
                        id='scn-detail-close',
                        className='scenario-detail-close'),
        ]),

        html.Div(className='scenario-detail-body', children=[
            # Section 1: Basic Information
            html.Div(className='scenario-detail-section', children=[
                html.Div(className='scenario-detail-section-header', children=[
                    html.I(className='fas fa-info-circle'),
                    html.H3('Basic Information'),
                ]),
                html.Div(className='scenario-detail-section-body', children=[
                    html.Div(style={'marginBottom': '10px'}, children=[
                        html.Span('Scenario Name', className='detail-label',
                                  style={'display': 'block', 'marginBottom': '4px'}),
                        _inp('scn-edit-name', 'text', fld('name', '')),
                    ]),
                    html.Div(children=[
                        html.Span('Description', className='detail-label',
                                  style={'display': 'block', 'marginBottom': '4px'}),
                        dcc.Textarea(
                            id='scn-edit-desc',
                            value=fld('description', ''),
                            placeholder='Describe this scenario...',
                            style={
                                'width': '100%', 'height': '60px',
                                'background': 'var(--bg-input)',
                                'border': '1px solid var(--border-default)',
                                'borderRadius': 'var(--radius-sm)',
                                'color': 'var(--text-primary)',
                                'padding': '8px 10px', 'fontFamily': 'var(--font-sans)',
                                'fontSize': '12.5px', 'resize': 'vertical',
                            }
                        ),
                    ]),
                ]),
            ]),

            # Section 2: Traffic Conditions
            html.Div(className='scenario-detail-section', children=[
                html.Div(className='scenario-detail-section-header', children=[
                    html.I(className='fas fa-car'),
                    html.H3('Traffic Conditions'),
                ]),
                html.Div(className='scenario-detail-section-body', children=[
                    html.Div(className='scenario-detail-grid', children=[
                        html.Div(className='scenario-detail-item', children=[
                            html.Span('Traffic Density', className='detail-label'),
                            _dd('scn-edit-density', [
                                {'label': 'Low', 'value': 'Low'},
                                {'label': 'Medium', 'value': 'Medium'},
                                {'label': 'High', 'value': 'High'},
                                {'label': 'Very High', 'value': 'Very High'},
                            ], fld('density', 'Medium')),
                        ]),
                        html.Div(className='scenario-detail-item', children=[
                            html.Span('Pedestrian Activity', className='detail-label'),
                            _dd('scn-edit-pedestrian', [
                                {'label': 'Low', 'value': 'Low'},
                                {'label': 'Medium', 'value': 'Medium'},
                                {'label': 'High', 'value': 'High'},
                            ], fld('pedestrian', 'Medium')),
                        ]),
                        html.Div(className='scenario-detail-item',
                                 style={'gridColumn': '1 / -1'}, children=[
                            html.Span('Emergency Mode', className='detail-label'),
                            _dd('scn-edit-emergency', [
                                {'label': 'Disabled', 'value': 'Disabled'},
                                {'label': 'Enabled (1 Ambulance)', 'value': 'Enabled (1 Ambulance)'},
                                {'label': 'Enabled (2 Vehicles)', 'value': 'Enabled (2 Vehicles)'},
                            ], fld('emergency', 'Disabled')),
                        ]),
                    ]),
                ]),
            ]),

            # Section 3: Disruptions
            html.Div(className='scenario-detail-section', children=[
                html.Div(className='scenario-detail-section-header', children=[
                    html.I(className='fas fa-triangle-exclamation'),
                    html.H3('Active Disruptions'),
                ]),
                html.Div(className='scenario-detail-section-body', children=[
                    html.Div(style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'},
                             children=[
                        _build_disruption_block(
                            'Lane Closure', 'scn-lane', 'fa-road-barrier',
                            [
                                html.Div(children=[
                                    html.Span('Approach', className='detail-label',
                                              style={'display': 'block', 'marginBottom': '3px'}),
                                    _dd('scn-lane-approach', direction_opts, fld('lane_app', 'north')),
                                ]),
                                html.Div(children=[
                                    html.Span('Lanes Closed', className='detail-label',
                                              style={'display': 'block', 'marginBottom': '3px'}),
                                    _inp('scn-lane-lanes', 'number', fld('lane_lanes', 1),
                                         min=1, max=3),
                                ]),
                            ]
                        ),
                        _build_disruption_block(
                            'Road Construction', 'scn-const', 'fa-person-digging',
                            [
                                html.Div(children=[
                                    html.Span('Approach', className='detail-label',
                                              style={'display': 'block', 'marginBottom': '3px'}),
                                    _dd('scn-const-approach', direction_opts, fld('const_app', 'north')),
                                ]),
                                html.Div(children=[
                                    html.Span('Speed Reduction', className='detail-label',
                                              style={'display': 'block', 'marginBottom': '3px'}),
                                    _inp('scn-const-speed', 'number', fld('const_spd', 0.5),
                                         min=0.1, max=0.9, step=0.1),
                                ]),
                            ]
                        ),
                        _build_disruption_block(
                            'Accident / Blockage', 'scn-acc', 'fa-car-burst',
                            [
                                html.Div(children=[
                                    html.Span('Approach', className='detail-label',
                                              style={'display': 'block', 'marginBottom': '3px'}),
                                    _dd('scn-acc-approach', direction_opts, fld('acc_app', 'north')),
                                ]),
                                html.Div(children=[
                                    html.Span('Severity', className='detail-label',
                                              style={'display': 'block', 'marginBottom': '3px'}),
                                    _dd('scn-acc-severity', [
                                        {'label': 'Minor', 'value': 'minor'},
                                        {'label': 'Major', 'value': 'major'},
                                        {'label': 'Severe', 'value': 'severe'},
                                    ], fld('acc_sev', 'major')),
                                ]),
                            ]
                        ),
                        _build_disruption_block(
                            'Flooding', 'scn-flood', 'fa-water',
                            [
                                html.Div(children=[
                                    html.Span('Affected Approach', className='detail-label',
                                              style={'display': 'block', 'marginBottom': '3px'}),
                                    _dd('scn-flood-approach', [
                                        {'label': 'North', 'value': 'north'},
                                        {'label': 'South', 'value': 'south'},
                                        {'label': 'East', 'value': 'east'},
                                        {'label': 'West', 'value': 'west'},
                                        {'label': 'All', 'value': 'all'},
                                    ], fld('flood_app', 'all')),
                                ]),
                                html.Div(children=[
                                    html.Span('Severity', className='detail-label',
                                              style={'display': 'block', 'marginBottom': '3px'}),
                                    _dd('scn-flood-severity', [
                                        {'label': 'Minor', 'value': 'minor'},
                                        {'label': 'Major', 'value': 'major'},
                                        {'label': 'Severe', 'value': 'severe'},
                                    ], fld('flood_sev', 'major')),
                                ]),
                            ]
                        ),
                    ]),
                ]),
            ]),

            # Section 4: Advanced Settings
            html.Div(className='scenario-detail-section', children=[
                html.Div(className='scenario-detail-section-header', children=[
                    html.I(className='fas fa-cog'),
                    html.H3('Advanced Settings'),
                ]),
                html.Div(className='scenario-detail-section-body', children=[
                    html.Div(children=[
                        html.Span('System Constraints (JSON)', className='detail-label',
                                  style={'display': 'block', 'marginBottom': '4px'}),
                        dcc.Textarea(
                            id='scn-constraints-config',
                            value=fld('constraints', '{}'),
                            placeholder='{"safety_limit": 50}',
                            style={
                                'width': '100%', 'height': '50px',
                                'background': 'var(--bg-input)',
                                'border': '1px solid var(--border-default)',
                                'borderRadius': 'var(--radius-sm)',
                                'color': 'var(--text-primary)',
                                'padding': '8px 10px',
                                'fontFamily': 'var(--font-mono)',
                                'fontSize': '11px', 'resize': 'vertical',
                            }
                        ),
                    ]),
                ]),
            ]),
        ]),

        html.Div(className='scenario-detail-footer', children=[
            html.Button([html.I(className='fas fa-times'), ' Cancel'],
                        id='scn-edit-cancel',
                        className='btn btn-secondary', style={'flex': '1'}),
            html.Button([html.I(className='fas fa-save'), ' Save Scenario'],
                        id='scn-edit-save',
                        className='btn btn-primary', style={'flex': '2'}),
        ]),
    ]


# ─── Layout ─────────────────────────────────────────────────────────

def layout():
    if not auth.is_authenticated():
        return html.Div()

    all_scenarios = database.get_scenarios(include_archived=True)
    total = len(all_scenarios)
    officials = sum(1 for s in all_scenarios if s['is_official'])
    archived = sum(1 for s in all_scenarios if s['is_archived'])
    user_count = total - officials
    active_count = total - archived
    densities = sorted(
        set(s.get('traffic_density') for s in all_scenarios if s.get('traffic_density')),
        key=lambda d: DENSITY_ORDER.get(d, 99)
    )

    return html.Div(className='app-layout', children=[
        create_header(),
        html.Div(className='app-body', children=[
            create_sidebar(),
            html.Main(className='main-content', children=[
                html.Div(className='page-header', children=[
                    html.H1('Scenario Library'),
                    html.P('Browse, create, and manage traffic simulation scenarios.'),
                ]),

                html.Div(id='scn-alert', className='alert alert-info hidden',
                         style={'display': 'none'}),

                html.Div(className='scenario-kpi-row', children=[
                    create_mini_stat('Total Scenarios', str(total),
                                     'fas fa-layer-group', 'var(--info)'),
                    create_mini_stat('Official', str(officials),
                                     'fas fa-certificate', 'var(--success)'),
                    create_mini_stat('User-Created', str(user_count),
                                     'fas fa-user', 'var(--accent)'),
                    create_mini_stat('Active', str(active_count),
                                     'fas fa-play', 'var(--text-muted)'),
                ]),

                html.Div(className='scenario-library-grid', children=[
                    html.Div(className='scenario-left-panel',
                             id='scn-left-panel',
                             children=_build_category_panel(all_scenarios, 'all', densities)),

                    html.Div(className='scenario-content-area', children=[
                        html.Div(className='scenario-toolbar', children=[
                            html.Div(className='filter-group filter-group-wide', children=[
                                html.Label('Search', className='filter-label'),
                                dcc.Input(id='scn-search', type='text',
                                          placeholder='Search by scenario name...',
                                          className='filter-input', debounce=True),
                            ]),
                            html.Div(className='filter-group', children=[
                                html.Label('Density', className='filter-label'),
                                dcc.Dropdown(id='scn-density-filter',
                                             options=DENSITY_OPTIONS, value='all',
                                             clearable=False, searchable=False,
                                             className='dash-dropdown dropdown-small'),
                            ]),
                            html.Div(className='filter-group', children=[
                                html.Label('Type', className='filter-label'),
                                dcc.Dropdown(id='scn-type-filter',
                                             options=TYPE_OPTIONS, value='all',
                                             clearable=False, searchable=False,
                                             className='dash-dropdown dropdown-small'),
                            ]),
                            html.Div(className='filter-group', children=[
                                html.Label('State', className='filter-label'),
                                dcc.Dropdown(id='scn-state-filter',
                                             options=STATE_OPTIONS, value='all',
                                             clearable=False, searchable=False,
                                             className='dash-dropdown dropdown-small'),
                            ]),
                            html.Div(className='filter-group', children=[
                                html.Label('Sort', className='filter-label'),
                                dcc.Dropdown(id='scn-sort', options=SORT_OPTIONS,
                                             value='name_asc', clearable=False,
                                             searchable=False,
                                             className='dash-dropdown dropdown-small'),
                            ]),
                            html.Div(className='filter-spacer'),
                            html.Div(className='view-mode-toggle', children=[
                                html.Button(html.I(className='fas fa-th-large'),
                                            id='scn-view-cards',
                                            className='view-mode-btn active'),
                                html.Button(html.I(className='fas fa-list'),
                                            id='scn-view-table',
                                            className='view-mode-btn'),
                            ]),
                            html.Button([html.I(className='fas fa-plus'), ' New Scenario'],
                                        id='scn-new-scenario',
                                        className='toolbar-create-btn'),
                        ]),

                        html.Div(id='scn-display-area'),
                    ]),
                ]),

                dcc.Store(id='scn-selected-id', data=None),
                dcc.Store(id='scn-view-mode', data='cards'),
                dcc.Store(id='scn-active-category', data='all'),
                dcc.Store(id='scn-drawer-mode', data=None),
            ]),
        ]),

        html.Div(id='scn-detail-overlay', className='scenario-detail-overlay',
                 n_clicks=0),
        html.Div(id='scn-detail-panel', className='scenario-detail-panel',
                 children=_build_detail_panel(None)),
    ])


# ─── Callbacks ────────────────────────────────────────────────────────

@callback(
    [Output('scn-display-area', 'children'),
     Output('scn-left-panel', 'children')],
    [Input('scn-search', 'value'),
     Input('scn-density-filter', 'value'),
     Input('scn-type-filter', 'value'),
     Input('scn-state-filter', 'value'),
     Input('scn-sort', 'value'),
     Input('scn-view-mode', 'data'),
     Input('scn-selected-id', 'data'),
     Input('scn-active-category', 'data'),
     Input({'type': 'cat-filter', 'index': ALL}, 'n_clicks'),
     Input({'type': 'density-filter-btn', 'index': ALL}, 'n_clicks')],
)
def update_scenarios_display(search, density, type_f, state_f, sort_val,
                              view_mode, selected_id, active_cat,
                              cat_clicks, density_clicks):
    scenarios = database.get_scenarios(include_archived=True)

    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict):
        if triggered_id.get('type') == 'cat-filter':
            active_cat = triggered_id.get('index')
        elif triggered_id.get('type') == 'density-filter-btn':
            density = triggered_id.get('index')
            active_cat = 'all'

    densities = sorted(
        set(s.get('traffic_density') for s in scenarios if s.get('traffic_density')),
        key=lambda d: DENSITY_ORDER.get(d, 99)
    )

    filtered = [s for s in scenarios if _filter_match(
        s, search, density, type_f, state_f, active_cat)]
    filtered = _sort_scenarios(filtered, sort_val)

    cat_panel = _build_category_panel(scenarios, active_cat, densities)

    if view_mode == 'table':
        content = _build_scenario_table(filtered, selected_id)
    else:
        if not filtered:
            content = html.Div(className='empty-state', children=[
                html.I(className='fas fa-map'),
                html.P('No scenarios found'),
                html.P('No scenarios match the current filter criteria.',
                       className='empty-state-hint'),
            ])
        else:
            content = html.Div(className='scenario-card-grid',
                               children=[_build_scenario_card(s, selected_id) for s in filtered])

    return content, cat_panel


@callback(
    [Output('scn-selected-id', 'data', allow_duplicate=True),
     Output('scn-view-mode', 'data'),
     Output('scn-active-category', 'data'),
     Output('scn-density-filter', 'value'),
     Output('scn-drawer-mode', 'data')],
    [Input({'type': 'scenario-card', 'index': ALL}, 'n_clicks'),
     Input({'type': 'scenario-table-row', 'index': ALL}, 'n_clicks'),
     Input({'type': 'view-scenario-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'edit-scenario-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'drawer-edit-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'cat-filter', 'index': ALL}, 'n_clicks'),
     Input({'type': 'density-filter-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'duplicate-scenario-btn', 'index': ALL}, 'n_clicks'),
     Input('scn-view-cards', 'n_clicks'),
     Input('scn-view-table', 'n_clicks'),
     Input('scn-new-scenario', 'n_clicks'),
     Input('scn-detail-close', 'n_clicks'),
     Input('scn-edit-cancel', 'n_clicks'),
     Input('scn-detail-overlay', 'n_clicks')],
    [State('scn-selected-id', 'data'),
     State('scn-view-mode', 'data'),
     State('scn-active-category', 'data'),
     State('scn-density-filter', 'value')],
    prevent_initial_call=True,
)
def handle_selection_and_view(card_clicks, row_clicks, view_clicks,
                               edit_clicks, drawer_edit_clicks,
                               cat_clicks, density_clicks,
                               duplicate_clicks,
                               cards_mode, table_mode,
                               new_click, close_clicks, cancel_clicks,
                               overlay_clicks,
                               current_selected, current_mode,
                               current_cat, current_density):
    triggered_id = ctx.triggered_id

    # Close drawer
    if triggered_id in ('scn-detail-close', 'scn-edit-cancel',
                        'scn-detail-overlay'):
        return None, no_update, no_update, no_update, None

    # View mode toggles
    if triggered_id == 'scn-view-cards':
        return no_update, 'cards', no_update, no_update, no_update
    if triggered_id == 'scn-view-table':
        return no_update, 'table', no_update, no_update, no_update

    # New Scenario
    if triggered_id == 'scn-new-scenario':
        return None, no_update, no_update, no_update, 'edit'

    # Category clicks
    if isinstance(triggered_id, dict):
        t = triggered_id.get('type')
        if t == 'cat-filter':
            return None, no_update, triggered_id.get('index'), 'all', None
        if t == 'density-filter-btn':
            return None, no_update, 'all', triggered_id.get('index'), None

        if t == 'view-scenario-btn':
            new_id = triggered_id.get('index')
            return new_id, no_update, no_update, no_update, 'view'

        if t in ('edit-scenario-btn', 'drawer-edit-btn'):
            new_id = triggered_id.get('index')
            return new_id, no_update, no_update, no_update, 'edit'

        if t == 'duplicate-scenario-btn':
            source_id = triggered_id.get('index')
            source = database.get_scenario_by_id(source_id)
            if source:
                new_id = database.create_scenario(
                    name=f"{source['name']} (Copy)",
                    description=source.get('description', ''),
                    traffic_density=source.get('traffic_density', 'Medium'),
                    pedestrian_density=source.get('pedestrian_density', 'Medium'),
                    emergency_mode=source.get('emergency_mode', 'Disabled'),
                    lane_closure_config=source.get('lane_closure_config', '{}'),
                    construction_config=source.get('construction_config', '{}'),
                    accident_config=source.get('accident_config', '{}'),
                    flooding_config=source.get('flooding_config', '{}'),
                    created_by=session.get('user_id'),
                )
                return new_id, no_update, no_update, no_update, 'view'
            return no_update, no_update, no_update, no_update, None

        if t in ('scenario-card', 'scenario-table-row'):
            new_id = triggered_id.get('index')
            if new_id == current_selected:
                return None, no_update, no_update, no_update, None
            return new_id, no_update, no_update, no_update, 'view'

    return no_update, no_update, no_update, no_update, None


@callback(
    [Output('scn-detail-overlay', 'className'),
     Output('scn-detail-panel', 'className'),
     Output('scn-detail-panel', 'children')],
    [Input('scn-selected-id', 'data'),
     Input('scn-drawer-mode', 'data'),
     Input('scn-detail-close', 'n_clicks'),
     Input('scn-detail-overlay', 'n_clicks')],
    prevent_initial_call=True,
)
def toggle_detail_panel(selected_id, drawer_mode, close_clicks, overlay_clicks):
    triggered_id = ctx.triggered_id

    if triggered_id in ('scn-detail-close', 'scn-detail-overlay'):
        return ('scenario-detail-overlay', 'scenario-detail-panel',
                _build_detail_panel(None))

    if drawer_mode is None or selected_id is None and drawer_mode != 'edit':
        return ('scenario-detail-overlay', 'scenario-detail-panel',
                _build_detail_panel(None))

    if drawer_mode == 'edit':
        scenario = database.get_scenario_by_id(selected_id) if selected_id else None
        return ('scenario-detail-overlay open', 'scenario-detail-panel open',
                _build_edit_panel(scenario))

    if drawer_mode == 'view' and selected_id is not None:
        scenario = database.get_scenario_by_id(selected_id)
        return ('scenario-detail-overlay open', 'scenario-detail-panel open',
                _build_detail_panel(scenario))

    return ('scenario-detail-overlay', 'scenario-detail-panel',
            _build_detail_panel(None))


@callback(
    Output('scn-view-cards', 'className'),
    Output('scn-view-table', 'className'),
    Input('scn-view-mode', 'data'),
)
def update_view_mode_toggle(mode):
    if mode == 'table':
        return 'view-mode-btn', 'view-mode-btn active'
    return 'view-mode-btn active', 'view-mode-btn'


@callback(
    [Output('scn-alert', 'children'),
     Output('scn-alert', 'className'),
     Output('scn-alert', 'style'),
     Output('scn-selected-id', 'data', allow_duplicate=True),
     Output('scn-drawer-mode', 'data', allow_duplicate=True)],
    [Input('scn-edit-save', 'n_clicks')],
    [State('scn-selected-id', 'data'),
     State('scn-edit-name', 'value'),
     State('scn-edit-desc', 'value'),
     State('scn-edit-density', 'value'),
     State('scn-edit-pedestrian', 'value'),
     State('scn-edit-emergency', 'value'),

     State('scn-lane-toggle', 'value'),
     State('scn-lane-approach', 'value'),
     State('scn-lane-lanes', 'value'),

     State('scn-const-toggle', 'value'),
     State('scn-const-approach', 'value'),
     State('scn-const-speed', 'value'),

     State('scn-acc-toggle', 'value'),
     State('scn-acc-approach', 'value'),
     State('scn-acc-severity', 'value'),

     State('scn-flood-toggle', 'value'),
     State('scn-flood-approach', 'value'),
     State('scn-flood-severity', 'value'),

     State('scn-constraints-config', 'value')],
    prevent_initial_call=True,
)
def handle_save_scenario(save_clicks, selected_id, name, desc, density, pedestrian, emergency,
                          lane_toggle, lane_app, lane_lanes,
                          const_toggle, const_app, const_spd,
                          acc_toggle, acc_app, acc_sev,
                          flood_toggle, flood_app, flood_sev,
                          constraints_config):
    if not auth.validate_current_session():
        auth.clear_session()
        return ('Session expired. Please log in again.',
                'alert alert-error', {}, no_update, no_update)

    current_user_id = session.get('user_id')
    current_username = session.get('username')

    if not name or not name.strip():
        return ('Scenario name cannot be empty.', 'alert alert-error', {},
                no_update, no_update)

    action_name = 'edit' if selected_id else 'create'
    if not auth.has_permission('scenarios', action_name):
        return (f"Access Denied: You do not have permission to {action_name} scenarios.",
                'alert alert-error', {}, no_update, no_update)

    # Serialize disruptions
    def _toggle_enabled(val):
        return bool(val and 'enabled' in (val or []))

    lane_enabled = _toggle_enabled(lane_toggle)
    lane_cfg = {'enabled': lane_enabled, 'approach': lane_app,
                'lanes_closed': lane_lanes} if lane_enabled else {'enabled': False}

    const_enabled = _toggle_enabled(const_toggle)
    const_cfg = {'enabled': const_enabled, 'approach': const_app,
                 'speed_reduction': const_spd} if const_enabled else {'enabled': False}

    acc_enabled = _toggle_enabled(acc_toggle)
    acc_cfg = {'enabled': acc_enabled, 'approach': acc_app,
               'severity': acc_sev} if acc_enabled else {'enabled': False}

    flood_enabled = _toggle_enabled(flood_toggle)
    flood_cfg = {'enabled': flood_enabled, 'approach': flood_app,
                 'severity': flood_sev} if flood_enabled else {'enabled': False}

    try:
        parsed_constraints = json.loads(constraints_config or '{}')
        if not isinstance(parsed_constraints, dict):
            return ('Constraints Config must be a JSON object.',
                    'alert alert-error', {}, no_update, no_update)
    except Exception as e:
        return (f"Invalid JSON in Constraints Config: {str(e)}",
                'alert alert-error', {}, no_update, no_update)

    if selected_id:
        database.update_scenario(
            selected_id,
            name=name.strip(),
            description=desc,
            traffic_density=density,
            pedestrian_density=pedestrian,
            emergency_mode=emergency,
            lane_closure_config=json.dumps(lane_cfg),
            construction_config=json.dumps(const_cfg),
            accident_config=json.dumps(acc_cfg),
            flooding_config=json.dumps(flood_cfg)
        )

        database.delete_scenario_constraints(selected_id)
        for c_type, c_cfg in parsed_constraints.items():
            database.save_scenario_constraint(selected_id, c_type, json.dumps(c_cfg))

        database.log_audit_event(
            user_id=current_user_id, action='update_scenario', target='scenarios',
            details=f"User {current_username} updated scenario '{name}' (ID={selected_id})"
        )
        return (f"Scenario '{name}' updated successfully.",
                'alert alert-success', {}, selected_id, None)
    else:
        new_id = database.create_scenario(
            name=name.strip(),
            description=desc,
            traffic_density=density,
            pedestrian_density=pedestrian,
            emergency_mode=emergency,
            lane_closure_config=json.dumps(lane_cfg),
            construction_config=json.dumps(const_cfg),
            accident_config=json.dumps(acc_cfg),
            flooding_config=json.dumps(flood_cfg),
            created_by=current_user_id
        )

        for c_type, c_cfg in parsed_constraints.items():
            database.save_scenario_constraint(new_id, c_type, json.dumps(c_cfg))

        database.log_audit_event(
            user_id=current_user_id, action='create_scenario', target='scenarios',
            details=f"User {current_username} created scenario '{name}' (ID={new_id})"
        )
        return (f"Scenario '{name}' created successfully.",
                'alert alert-success', {}, new_id, None)

    return ('', 'alert alert-info hidden', {'display': 'none'}, no_update, no_update)


@callback(
    [Output('scn-alert', 'children', allow_duplicate=True),
     Output('scn-alert', 'className', allow_duplicate=True),
     Output('scn-alert', 'style', allow_duplicate=True),
     Output('scn-selected-id', 'data', allow_duplicate=True),
     Output('scn-drawer-mode', 'data', allow_duplicate=True)],
    [Input({'type': 'official-btn', 'index': ALL}, 'n_clicks'),
     Input({'type': 'archive-btn', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True,
)
def handle_admin_scenario_actions(official_clicks, archive_clicks):
    triggered_id = ctx.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict):
        return ('', 'alert alert-info hidden', {'display': 'none'}, no_update, no_update)

    triggered_prop = ctx.triggered[0] if ctx.triggered else None
    if not triggered_prop or not triggered_prop.get('value'):
        return ('', 'alert alert-info hidden', {'display': 'none'}, no_update, no_update)

    action_type = triggered_id.get('type')
    target_id = triggered_id.get('index')
    current_admin_id = session.get('user_id')
    current_admin_username = session.get('username')

    if not auth.is_admin():
        return ('Access Denied: Administrative action not authorized.', 'alert alert-error', {}, no_update, no_update)

    scenario = database.get_scenario_by_id(target_id)
    if not scenario:
        return ('Scenario not found.', 'alert alert-error', {}, no_update, no_update)

    if action_type == 'official-btn':
        new_official = 0 if scenario['is_official'] else 1
        database.update_scenario(target_id, is_official=new_official)
        action_name = "demoted" if new_official == 0 else "promoted to official"
        database.log_audit_event(user_id=current_admin_id, action='update_scenario_official', target='scenarios',
                                 details=f"Admin {current_admin_username} {action_name} scenario '{scenario['name']}' (ID={target_id})")
        return (f"Scenario '{scenario['name']}' {action_name} successfully.", 'alert alert-success', {}, no_update, no_update)

    elif action_type == 'archive-btn':
        new_archived = 0 if scenario['is_archived'] else 1
        database.update_scenario(target_id, is_archived=new_archived)
        action_name = "restored" if new_archived == 0 else "archived"
        database.log_audit_event(user_id=current_admin_id, action='update_scenario_archive', target='scenarios',
                                 details=f"Admin {current_admin_username} {action_name} scenario '{scenario['name']}' (ID={target_id})")
        return (f"Scenario '{scenario['name']}' {action_name} successfully.", 'alert alert-success', {}, no_update, no_update)

    return ('', 'alert alert-info hidden', {'display': 'none'}, no_update, no_update)

@callback(
    [Output('scn-alert', 'children', allow_duplicate=True),
     Output('scn-alert', 'className', allow_duplicate=True),
     Output('scn-alert', 'style', allow_duplicate=True),
     Output('scn-selected-id', 'data', allow_duplicate=True),
     Output('scn-drawer-mode', 'data', allow_duplicate=True)],
    [Input({'type': 'del-scenario-btn', 'index': ALL}, 'n_clicks')],
    [State('scn-selected-id', 'data')],
    prevent_initial_call=True,
)
def handle_delete_scenario(del_clicks, current_selected):
    triggered_id = ctx.triggered_id
    if not triggered_id or not isinstance(triggered_id, dict):
        return ('', 'alert alert-info hidden', {'display': 'none'}, no_update, no_update)

    triggered_prop = ctx.triggered[0] if ctx.triggered else None
    if not triggered_prop or not triggered_prop.get('value'):
        return ('', 'alert alert-info hidden', {'display': 'none'}, no_update, no_update)

    if not auth.validate_current_session():
        auth.clear_session()
        return ('Session expired. Please log in again.',
                'alert alert-error', {}, no_update, no_update)

    target_id = triggered_id.get('index')
    current_user_id = session.get('user_id')
    current_username = session.get('username')

    if not auth.has_permission('scenarios', 'delete'):
        return ('Access Denied: You do not have permission to delete scenarios.',
                'alert alert-error', {}, no_update, no_update)

    s = database.get_scenario_by_id(target_id)
    if not s:
        return ('Scenario not found.', 'alert alert-error', {}, no_update, no_update)

    database.delete_scenario_constraints(target_id)
    database.delete_scenario(target_id)

    database.log_audit_event(
        user_id=current_user_id, action='delete_scenario', target='scenarios',
        details=f"User {current_username} deleted scenario '{s['name']}' (ID={target_id})"
    )
    return (f"Scenario '{s['name']}' deleted successfully.",
            'alert alert-success', {}, None, None)
