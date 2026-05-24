"""
SMARTFLOW — Main Dash Application
AI-driven traffic simulation and decision support platform.

Run with: python app.py
Then open: http://localhost:8050
"""

import os
from dash import Dash, html, dcc, callback, Input, Output, State
from flask import session

import config
import database
import auth

# Page imports
from pages import login, register, dashboard, simulation, scenarios
from pages import live_traffic, performance, ai_agent, runs_reports
from pages import change_password, admin_users, admin_audit, admin_config, admin_scenarios
from pages import profile_settings, help_about, admin_roles, admin_backups


# ─── External Resources ─────────────────────────────────────────────
external_stylesheets = [
    # Google Fonts: Inter + JetBrains Mono
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap',
    # Font Awesome 6 icons
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
]

# ─── Initialize Dash App ────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    title='SMARTFLOW — Traffic Simulation Platform',
    update_title=None,
    suppress_callback_exceptions=True,
)

app.server.secret_key = config.SECRET_KEY

# ─── Initialize Database ────────────────────────────────────────────
database.init_db()
database.seed_data()

# ─── Register Dashboard Callbacks ───────────────────────────────────
from callbacks import register_callbacks
register_callbacks(app)


# ─── App Layout with Routing ────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])


@callback(Output('page-content', 'children'),
          Input('url', 'pathname'))
def route_page(pathname):
    # Active Session Cleanup (expired ones)
    try:
        database.delete_expired_sessions()
    except Exception:
        pass

    # Public routes (no auth required)
    if pathname == '/login' or pathname == '/':
        if auth.is_authenticated():
            # Validate active session against database
            if not auth.validate_current_session():
                auth.clear_session()
                return login.layout()
                
            if session.get('must_change_password'):
                return change_password.layout()
            return dashboard.layout()
        return login.layout()
    
    if pathname == '/register':
        return register.layout()
        
    if pathname == '/logout':
        auth.clear_session()
        return dcc.Location(pathname='/login', id='redirect-logout')
    
    # Protected routes (auth required)
    if not auth.is_authenticated():
        return dcc.Location(pathname='/login', id='redirect-login')
        
    # Active session validation against DB and status checks
    if not auth.validate_current_session():
        auth.clear_session()
        return dcc.Location(pathname='/login', id='redirect-session-expired')
        
    # Forced password change redirect
    if session.get('must_change_password'):
        if pathname != '/change-password':
            return dcc.Location(pathname='/change-password', id='redirect-change-password')
        return change_password.layout()
        
    if pathname == '/change-password':
        # If they don't need to change password, redirect to dashboard
        return dcc.Location(pathname='/dashboard', id='redirect-dashboard')
    
    # Permission mappings
    permission_mappings = {
        '/dashboard': 'dashboard',
        '/simulation': 'simulation',
        '/scenarios': 'scenarios',
        '/live-traffic': 'live-traffic',
        '/performance': 'performance',
        '/ai-agent': 'ai-agent',
        '/runs-reports': 'runs-reports',
        '/profile': 'profile',
        '/help': 'help',
        '/admin/users': 'admin-users',
        '/admin/roles': 'admin-roles',
        '/admin/scenarios': 'admin-scenarios',
        '/admin/config': 'admin-config',
        '/admin/audit': 'admin-audit',
        '/admin/backups': 'admin-backups',
    }
    
    # Enforce page-level permissions
    page_key = permission_mappings.get(pathname)
    if page_key and not auth.has_permission(page_key, 'view'):
        from components.header import create_header
        from components.sidebar import create_sidebar
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
                                    children='Access Denied: You do not have permissions to view this page.'
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    
    # Route to appropriate page
    if pathname == '/dashboard':
        return dashboard.layout()
    elif pathname == '/simulation':
        return simulation.layout()
    elif pathname == '/scenarios':
        return scenarios.layout()
    elif pathname == '/live-traffic':
        return live_traffic.layout()
    elif pathname == '/performance':
        return performance.layout()
    elif pathname == '/ai-agent':
        return ai_agent.layout()
    elif pathname == '/runs-reports':
        return runs_reports.layout()
    elif pathname == '/profile':
        return profile_settings.layout()
    elif pathname == '/help':
        return help_about.layout()
    elif pathname == '/admin/users':
        return admin_users.layout()
    elif pathname == '/admin/roles':
        return admin_roles.layout()
    elif pathname == '/admin/scenarios':
        return admin_scenarios.layout()
    elif pathname == '/admin/config':
        return admin_config.layout()
    elif pathname == '/admin/audit':
        return admin_audit.layout()
    elif pathname == '/admin/backups':
        return admin_backups.layout()
    else:
        return html.Div([
            html.H1('404 - Page Not Found'),
            html.P('The page you are looking for does not exist.'),
            dcc.Link('Return to Dashboard', href='/dashboard')
        ], style={'textAlign': 'center', 'padding': '50px'})


# ─── Run Server ─────────────────────────────────────────────────────
if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('  SMARTFLOW - Traffic Simulation Platform')
    print('  Open in browser: http://localhost:8050')
    print('  Default login: admin / SmartFlow2026!')
    print('=' * 60 + '\n')
    app.run(debug=True, port=8050)

