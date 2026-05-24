"""
SMARTFLOW — Admin Audit Logs Page
View immutable ledger of system actions.
"""

from dash import html, dcc
import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section


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
        
    logs = database.get_audit_logs(limit=200)
    
    rows = []
    for log in logs:
        rows.append(
            html.Tr(children=[
                html.Td(log['timestamp']),
                html.Td(log['username'] or 'System'),
                html.Td(log['action'].upper()),
                html.Td(log['target'] or 'N/A'),
                html.Td(log['details'] or '')
            ])
        )
        
    table = html.Table(
        className='data-table',
        children=[
            html.Thead(children=[
                html.Tr(children=[
                    html.Th('Timestamp'),
                    html.Th('User'),
                    html.Th('Action'),
                    html.Th('Target'),
                    html.Th('Details')
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
                                    html.H1(children='System Audit Logs'),
                                    html.P(children='Immutable history of all system events, including user changes, deletions, exports, and config updates.'),
                                ]
                            ),
                            
                            create_section(
                                title='Audit Events Ledger',
                                icon='fas fa-clipboard-list',
                                children=[table]
                            )
                        ]
                    )
                ]
            )
        ]
    )
