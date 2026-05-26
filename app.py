"""
SMARTFLOW — Main Dash Application
AI-driven traffic simulation and decision support platform.
"""

import os
from dash import Dash, html, dcc, callback, Input, Output
from flask import session, request

import config
import database
import auth

from pages import login, register, dashboard, simulation, scenarios
from pages import performance, ai_agent, runs_reports
from pages import change_password, admin_users, admin_roles
from pages import admin_audit, admin_backups
from pages import profile_settings, help_about


external_scripts = [
    'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
    'https://cdn.jsdelivr.net/npm/three@0.128/examples/js/loaders/GLTFLoader.js',
]

external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
]

app = Dash(
    __name__,
    external_scripts=external_scripts,
    external_stylesheets=external_stylesheets,
    title='SMARTFLOW — Traffic Simulation Platform',
    update_title=None,
    suppress_callback_exceptions=True,
)

app.server.secret_key = config.SECRET_KEY

database.init_db()
database.seed_data()

from callbacks import register_callbacks
register_callbacks(app)


# ─── Public vs Protected Routes ──────────────────────────────────────

PUBLIC_ROUTES = {'/login', '/register', '/logout'}

PAGE_ROUTES = {
    '/dashboard':       ('dashboard', dashboard),
    '/simulation':      ('simulation', simulation),
    '/scenarios':       ('scenarios', scenarios),
    '/performance':     ('performance', performance),
    '/ai-agent':        ('ai-agent', ai_agent),
    '/runs-reports':    ('runs-reports', runs_reports),
    '/profile':         ('profile', profile_settings),
    '/help':            ('help', help_about),
    '/change-password': (None, change_password),
}

ADMIN_PAGE_ROUTES = {
    '/admin/users':     ('admin-users', admin_users),
    '/admin/roles':     ('admin-roles', admin_roles),

    '/admin/audit':     ('admin-audit', admin_audit),
    '/admin/backups':   ('admin-backups', admin_backups),
}


def _access_denied(message='Access Denied'):
    from components.header import create_header
    from components.sidebar import create_sidebar
    return html.Div(className='app-layout', children=[
        create_header(),
        html.Div(className='app-body', children=[
            create_sidebar(),
            html.Main(className='main-content', children=[
                html.Div(className='alert alert-error', style={'marginTop': '30px'}, children=message)
            ])
        ])
    ])


def _require_auth():
    """Return (redirect_component, None) if not authenticated, or (None, None) if OK."""
    if not auth.is_authenticated():
        return dcc.Location(pathname='/login?reason=session_expired', id='redirect-login'), None
    if not auth.validate_current_session():
        auth.clear_session()
        return dcc.Location(pathname='/login?reason=session_expired', id='redirect-expired'), None
    return None, None


def _page_or_denied(page_key, page_module):
    """Render page if user has 'view' permission, else access-denied."""
    if page_key and not auth.has_permission(page_key, 'view'):
        return _access_denied('Access Denied: You do not have permission to view this page.')
    return page_module.layout()


def _admin_or_denied(page_key, page_module):
    """Render admin page if user is admin and has permission."""
    if not auth.is_admin():
        return _access_denied('Access Denied: Administrator privileges required.')
    if page_key and not auth.has_permission(page_key, 'view'):
        return _access_denied('Access Denied: You do not have permission to view this page.')
    return page_module.layout()


# ─── Layout & Routing ────────────────────────────────────────────────

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Interval(id='clock-interval', interval=1000, n_intervals=0),
    dcc.Interval(id='sim-interval', interval=500, n_intervals=0),
    dcc.Store(id='sim-state', data={'status': 'stopped', 'elapsed_seconds': 0, 'phase_seconds': 30}),
    dcc.Store(id='sim-engine-tick', data=0),
    dcc.Store(id='engine-state-json', data='{}'),
    html.Script(src='/assets/three-bridge.mjs', type='module'),
    html.Div(id='page-content'),
])


@callback(Output('page-content', 'children'),
          Input('url', 'pathname'))
def route_page(pathname):
    from flask import g
    g.current_pathname = pathname
    
    # Periodic session cleanup
    try:
        database.delete_expired_sessions()
    except Exception:
        pass

    pathname = pathname.rstrip('/') or '/login'

    # -- Public routes (no auth needed) --
    if pathname == '/login':
        if auth.is_authenticated() and auth.validate_current_session():
            if session.get('must_change_password'):
                return change_password.layout()
            return dashboard.layout()
        return login.layout()

    if pathname == '/register':
        return register.layout()

    if pathname == '/logout':
        auth.clear_session()
        return dcc.Location(pathname='/login', id='logout-redirect')

    # -- Change password (auth but no permission check) --
    if pathname == '/change-password':
        redirect, _ = _require_auth()
        if redirect:
            return redirect
        return change_password.layout()

    # -- All other routes require auth --
    redirect, _ = _require_auth()
    if redirect:
        return redirect

    # Force password change before anything else
    if session.get('must_change_password') and pathname != '/change-password':
        return dcc.Location(pathname='/change-password', id='force-change-pwd')

    # ── User pages ──
    if pathname in PAGE_ROUTES:
        page_key, module = PAGE_ROUTES[pathname]
        return _page_or_denied(page_key, module)

    # -- Admin pages --
    if pathname in ADMIN_PAGE_ROUTES:
        page_key, module = ADMIN_PAGE_ROUTES[pathname]
        return _admin_or_denied(page_key, module)

    # -- 404 --
    return html.Div(style={'textAlign': 'center', 'padding': '80px 20px'}, children=[
        html.H1('404 — Page Not Found', style={'fontSize': '28px', 'color': 'var(--text-primary)'}),
        html.P('The page you are looking for does not exist.', style={'color': 'var(--text-muted)', 'marginTop': '8px'}),
        html.A('Return to Dashboard', href='/dashboard', style={'color': 'var(--accent)', 'marginTop': '16px', 'display': 'inline-block'}),
    ])


# ─── Run Server ─────────────────────────────────────────────────────

if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('  SMARTFLOW — Traffic Simulation Platform')
    print('  http://localhost:8050')
    print('  Default admin: admin / SmartFlow2026!')
    print('=' * 60 + '\n')
    app.run(debug=True, port=8050)
