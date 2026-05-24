"""
SMARTFLOW — Admin Audit Logs Page
View immutable ledger of system actions.
"""

from datetime import datetime
from dash import html, dcc, callback, Input, Output
import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_mini_stat

ACTION_OPTIONS = [
    {'label': 'All Actions', 'value': 'all'},
    {'label': 'Create / Approve', 'value': 'create'},
    {'label': 'Update / Edit / Config', 'value': 'update'},
    {'label': 'Delete / Reject', 'value': 'delete'},
    {'label': 'Login / Logout', 'value': 'login'},
    {'label': 'Backup / System', 'value': 'backup'},
]


def _action_pill(action):
    a = (action or '').lower()
    cls = 'audit-pill'
    if any(k in a for k in ('delete', 'reject', 'remove')):
        cls += ' audit-pill-danger'
    elif any(k in a for k in ('create', 'approve', 'promote', 'register')):
        cls += ' audit-pill-success'
    elif any(k in a for k in ('update', 'edit', 'change', 'modify', 'config')):
        cls += ' audit-pill-info'
    elif any(k in a for k in ('login', 'logout')):
        cls += ' audit-pill-neutral'
    elif 'backup' in a or 'restore' in a:
        cls += ' audit-pill-neutral'
    elif 'system' in a or 'database' in a:
        cls += ' audit-pill-info'
    else:
        cls += ' audit-pill-neutral'
    return html.Span(action.upper(), className=cls)


def _build_table(logs):
    if not logs:
        return html.Div(className='empty-state', children=[
            html.I(className='fas fa-clipboard-list'),
            html.P('No audit events found'),
            html.P('No entries match the current search or filter criteria.', className='empty-state-hint'),
        ])

    rows = []
    for log in logs:
        rows.append(html.Tr([
            html.Td(log['timestamp']),
            html.Td(log['username'] or 'System'),
            html.Td(_action_pill(log['action'])),
            html.Td(log['target'] or 'N/A'),
            html.Td(log['details'] or '—', style={'maxWidth': '300px', 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'whiteSpace': 'nowrap'}),
        ]))

    return html.Table(className='data-table', children=[
        html.Thead([html.Tr([
            html.Th('Timestamp'), html.Th('User'), html.Th('Action'),
            html.Th('Target'), html.Th('Details'),
        ])]),
        html.Tbody(rows)
    ])


def _compute_stats(logs):
    today = datetime.now().strftime('%Y-%m-%d')
    today_events = [l for l in logs if (l.get('timestamp') or '').startswith(today)]
    failed = [l for l in logs if 'fail' in (l.get('action') or '').lower() or 'reject' in (l.get('action') or '').lower()]
    config_changes = [l for l in logs if 'config' in (l.get('action') or '').lower() or 'setting' in (l.get('action') or '').lower()]
    return len(today_events), len(failed), len(config_changes)


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

    logs = database.get_audit_logs(limit=500)
    today_count, failed_count, config_count = _compute_stats(logs)

    return html.Div(className='app-layout', children=[
        create_header(),
        html.Div(className='app-body', children=[
            create_sidebar(),
            html.Main(className='main-content', children=[
                html.Div(className='page-header', children=[
                    html.H1('System Audit Logs'),
                    html.P('Immutable history of all system events — user changes, deletions, exports, and config updates.'),
                ]),

                html.Div(className='stats-row', children=[
                    create_mini_stat('Events Today', str(today_count), 'fas fa-calendar-day', 'var(--info)'),
                    create_mini_stat('Total Logged', str(len(logs)), 'fas fa-list-ol', 'var(--accent)'),
                    create_mini_stat('Failures', str(failed_count), 'fas fa-triangle-exclamation', 'var(--error)'),
                    create_mini_stat('Config Changes', str(config_count), 'fas fa-sliders', 'var(--warning)'),
                ]),

                html.Div(className='section', children=[
                    html.Div(className='section-header', children=[
                        html.I(className='fas fa-clipboard-list'),
                        html.H3(className='section-title', children=[
                            html.Span('Audit Events Ledger', className='section-title-text'),
                            html.Small('Immutable, read-only history of every system action', className='section-subtitle'),
                        ]),
                    ]),
                    html.Div(className='filter-toolbar', children=[
                        html.Div(className='filter-group filter-group-wide', children=[
                            html.Label('Search', className='filter-label'),
                            dcc.Input(id='audit-search', type='text', placeholder='Search user, action, target, or details...',
                                      className='filter-input', debounce=True),
                        ]),
                        html.Div(className='filter-group', children=[
                            html.Label('Action Type', className='filter-label'),
                            dcc.Dropdown(id='audit-action-filter', options=ACTION_OPTIONS, value='all',
                                         clearable=False, searchable=False,
                                         className='dash-dropdown dropdown-small'),
                        ]),
                        html.Div(className='filter-group', children=[
                            html.Label('User', className='filter-label'),
                            dcc.Input(id='audit-user-filter', type='text', placeholder='Filter by user...',
                                      className='filter-input'),
                        ]),
                        html.Div(className='filter-spacer'),
                        html.Span(f'{len(logs)} entries loaded', className='filter-label',
                                  style={'alignSelf': 'center'}),
                    ]),
                    html.Div(className='section-content', style={'padding': 0}, children=[
                        html.Div(id='audit-table-container', className='table-scroll', style={'maxHeight': '520px'}, children=[
                            _build_table(logs)
                        ]),
                    ]),
                ]),

                dcc.Store(id='audit-raw-data', data=[]),
            ])
        ])
    ])


@callback(
    Output('audit-raw-data', 'data'),
    [Input('audit-raw-data', 'id')]
)
def load_audit_data(_):
    logs = database.get_audit_logs(limit=500)
    return [dict(l) for l in logs]


@callback(
    Output('audit-table-container', 'children'),
    [Input('audit-search', 'value'),
     Input('audit-action-filter', 'value'),
     Input('audit-user-filter', 'value'),
     Input('audit-raw-data', 'data')],
    prevent_initial_call=True
)
def filter_audit_table(search, action_filter, user_filter, raw_data):
    if not raw_data:
        return _build_table([])

    logs = raw_data

    if search:
        q = search.lower()
        logs = [l for l in logs if
                q in (str(l.get('username') or '')).lower() or
                q in (str(l.get('action') or '')).lower() or
                q in (str(l.get('target') or '')).lower() or
                q in (str(l.get('details') or '')).lower()]

    if action_filter and action_filter != 'all':
        action_q = action_filter.lower()
        logs = [l for l in logs if action_q in (str(l.get('action') or '')).lower()]

    if user_filter:
        q = user_filter.lower()
        logs = [l for l in logs if q in (str(l.get('username') or '')).lower()]

    return _build_table(logs)
