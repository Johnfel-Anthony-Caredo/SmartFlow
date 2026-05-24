"""
SMARTFLOW — Sidebar Component
Left navigation sidebar with role-based menu items and grouped sections.
"""

from dash import html, dcc
from flask import session


def _make_nav_item(item):
    return dcc.Link(
        className='nav-item',
        href=item['href'],
        id=f'nav-{item["id"]}',
        children=[
            html.I(className=item['icon']),
            html.Span(children=item['label']),
        ],
    )


def _make_section(title, items):
    children = [html.Div(className='nav-section-title', children=title)]
    for item in items:
        children.append(_make_nav_item(item))
    return children


def create_sidebar():
    user_role = session.get('role', 'researcher')
    is_admin = (user_role == 'admin')

    main_nav = [
        {'id': 'dashboard',   'label': 'Dashboard',          'icon': 'fas fa-tachometer-alt', 'href': '/dashboard'},
        {'id': 'simulation',  'label': 'Simulation Control',  'icon': 'fas fa-play-circle',   'href': '/simulation'},
        {'id': 'scenarios',   'label': 'Scenarios',           'icon': 'fas fa-map-marked-alt','href': '/scenarios'},
        {'id': 'live-traffic','label': 'Live Traffic',        'icon': 'fas fa-traffic-light', 'href': '/live-traffic'},
        {'id': 'performance', 'label': 'Performance',         'icon': 'fas fa-chart-line',    'href': '/performance'},
    ]

    intelligence_nav = [
        {'id': 'ai-agent',    'label': 'AI Agent (RL)',      'icon': 'fas fa-brain',   'href': '/ai-agent'},
        {'id': 'runs-reports','label': 'Runs & Reports',      'icon': 'fas fa-file-alt','href': '/runs-reports'},
    ]

    system_nav = [
        {'id': 'profile',     'label': 'Settings',            'icon': 'fas fa-cog',             'href': '/profile'},
        {'id': 'help',        'label': 'Help',                'icon': 'fas fa-question-circle', 'href': '/help'},
    ]

    admin_nav = [
        {'id': 'user-management','label': 'User Management',       'icon': 'fas fa-users',          'href': '/admin/users'},
        {'id': 'role-access',    'label': 'Role & Access Control', 'icon': 'fas fa-shield-alt',     'href': '/admin/roles'},
        {'id': 'scenario-library','label': 'Scenario Library',     'icon': 'fas fa-book',           'href': '/admin/scenarios'},
        {'id': 'system-config',  'label': 'System Config',         'icon': 'fas fa-cogs',           'href': '/admin/config'},
        {'id': 'audit-logs',     'label': 'Audit Logs',            'icon': 'fas fa-clipboard-list',  'href': '/admin/audit'},
        {'id': 'backup-restore', 'label': 'Backup & Restore',      'icon': 'fas fa-database',       'href': '/admin/backups'},
    ]

    nav_children = []
    nav_children.extend(_make_section('MAIN', main_nav))
    nav_children.extend(_make_section('INTELLIGENCE', intelligence_nav))
    nav_children.extend(_make_section('SYSTEM', system_nav))

    if is_admin:
        nav_children.append(html.Div(className='nav-divider'))
        nav_children.extend(_make_section('ADMIN', admin_nav))

    system_status = html.Div(
        className='system-status-panel',
        children=[
            html.Div(className='panel-title', children=[
                html.I(className='fa-solid fa-circle-nodes'),
                ' System Status',
            ]),
            html.Ul(className='status-list', children=[
                html.Li(className='status-item', children=[
                    html.Span(className='status-indicator active'),
                    html.Span('SUMO Connection', className='status-name'),
                    html.Span('ONLINE', className='status-value active'),
                ]),
                html.Li(className='status-item', children=[
                    html.Span(className='status-indicator active'),
                    html.Span('RL Agent', className='status-name'),
                    html.Span('ACTIVE', className='status-value active'),
                ]),
                html.Li(className='status-item', children=[
                    html.Span(className='status-indicator active'),
                    html.Span('Visualization', className='status-name'),
                    html.Span('RUNNING', className='status-value active'),
                ]),
                html.Li(className='status-item', children=[
                    html.Span(className='status-indicator active'),
                    html.Span('Data Logging', className='status-name'),
                    html.Span('RECORDING', className='status-value active'),
                ]),
            ]),
        ],
    )

    return html.Aside(
        className='sidebar',
        id='sidebar',
        children=[
            html.Nav(
                className='sidebar-nav',
                children=nav_children,
            ),
            system_status,
        ],
    )
