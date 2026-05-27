"""
SMARTFLOW — Profile & Settings Page
View account details and session activity.
"""

from dash import html, dcc
from flask import session
import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_mini_stat


# ─── Helper ────────────────────────────────────────────────────────

def _format_datetime(dt_str):
    """Format an ISO datetime string for display, or return a fallback."""
    if not dt_str:
        return 'Never'
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime('%B %d, %Y at %I:%M %p').replace(' 0', ' ')
    except Exception:
        return dt_str


def _role_color(role_name):
    """Return a CSS color for a given role."""
    colors = {
        'admin': 'var(--purple)',
        'user':  'var(--info)',
    }
    return colors.get(role_name, 'var(--accent)')


def _status_color(status):
    colors = {
        'active':   'var(--success)',
        'inactive': 'var(--text-muted)',
        'pending':  'var(--warning)',
    }
    return colors.get(status, 'var(--text-secondary)')


# ─── Section Builders ──────────────────────────────────────────────

def _build_profile_card(user):
    """Large profile identity card with avatar, name, and role badge."""
    role = user.get('role_name', 'user')
    role_clr = _role_color(role)
    initials = ''.join(w[0].upper() for w in (user.get('full_name') or 'U').split()[:2])

    return html.Div(className='profile-card', children=[
        # Avatar + identity
        html.Div(className='profile-card-top', children=[
            html.Div(
                className='profile-avatar',
                style={
                    'background': f'color-mix(in srgb, {role_clr} 15%, transparent)',
                    'border': f'2px solid color-mix(in srgb, {role_clr} 30%, transparent)',
                    'color': role_clr,
                },
                children=initials,
            ),
            html.Div(className='profile-identity', children=[
                html.H2(user['full_name'], className='profile-name'),
                html.Span(
                    f'@{user["username"]}',
                    className='profile-username',
                ),
            ]),
            html.Span(
                role.upper(),
                className='profile-role-badge',
                style={
                    'color': role_clr,
                    'background': f'color-mix(in srgb, {role_clr} 10%, transparent)',
                    'border': f'1px solid color-mix(in srgb, {role_clr} 20%, transparent)',
                },
            ),
        ]),

        html.Hr(className='profile-divider'),

        # Info rows
        html.Div(className='profile-info-grid', children=[
            _info_row('fas fa-envelope', 'Email', user.get('email') or 'Not provided'),
            _info_row('fas fa-shield-halved', 'Account Status',
                       user.get('status', 'active').capitalize(),
                       value_color=_status_color(user.get('status', 'active'))),
            _info_row('fas fa-calendar-plus', 'Member Since',
                       _format_datetime(user.get('created_at'))),
            _info_row('fas fa-right-to-bracket', 'Last Login',
                       _format_datetime(user.get('last_login_at'))),
        ]),

        html.Hr(className='profile-divider'),

        # Actions
        html.Div(className='profile-actions', children=[
            dcc.Link(
                html.Button(
                    className='btn btn-secondary btn-sm',
                    children=[html.I(className='fas fa-key'), html.Span('Change Password')],
                ),
                href='/change-password',
            ),
        ]),
    ])


def _info_row(icon, label, value, value_color=None):
    """Single row inside the profile info grid."""
    value_style = {}
    if value_color:
        value_style['color'] = value_color

    return html.Div(className='profile-info-row', children=[
        html.Div(className='profile-info-icon', children=[
            html.I(className=icon),
        ]),
        html.Div(className='profile-info-content', children=[
            html.Span(label, className='profile-info-label'),
            html.Span(value, className='profile-info-value', style=value_style),
        ]),
    ])


def _build_stats_row(user):
    """Top-level KPI summary using mini-stat chips."""
    activity = database.get_user_activity_summary(user['id'])
    last_login = _format_datetime(user.get('last_login_at'))

    return html.Div(className='stats-row profile-kpi-row', children=[
        create_mini_stat('Simulation Runs', str(activity.get('run_count', 0)),
                         'fas fa-flask', 'var(--accent)'),
        create_mini_stat('Audit Events', str(activity.get('audit_count', 0)),
                         'fas fa-scroll', 'var(--info)'),
        create_mini_stat('Last Login', last_login,
                         'fas fa-right-to-bracket', 'var(--warning)'),
        create_mini_stat('Account Status', user.get('status', 'active').capitalize(),
                         'fas fa-shield-halved', _status_color(user.get('status', 'active'))),
    ])


def _build_session_info():
    """Current session details."""
    session_token = session.get('session_token')
    masked = f'{session_token[:8]}•••' if session_token and len(session_token) > 8 else '—'

    rows = [
        ('Session ID',  masked),
        ('IP Address',  'localhost'),
        ('Platform',    'Plotly Dash / Flask'),
    ]

    return create_section(
        title='Current Session',
        icon='fas fa-fingerprint',
        children=[
            html.Div(className='profile-session-grid', children=[
                html.Div(className='profile-session-row', children=[
                    html.Span(label, className='profile-session-label'),
                    html.Span(value, className='profile-session-value'),
                ])
                for label, value in rows
            ]),
        ],
    )


# ─── Page Layout ───────────────────────────────────────────────────

def layout():
    if not auth.is_authenticated():
        return html.Div()

    user_id = session.get('user_id')
    user = database.get_user_by_id(user_id)
    if not user:
        return html.Div('User profile not found. Please log in.')

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
                                    html.H1('Profile & Settings'),
                                    html.P('View your account information and session details.'),
                                ],
                            ),

                            _build_stats_row(user),

                            # Two-column layout
                            html.Div(
                                className='profile-page-grid',
                                children=[
                                    # Left — profile card (full height)
                                    _build_profile_card(user),

                                    # Right — stacked panels
                                    html.Div(className='profile-right-stack', children=[
                                        _build_session_info(),
                                    ]),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
