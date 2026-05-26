"""
SmartFlow Traffic — Dash Callbacks
All interactive callbacks for the dashboard: clock, timers, controls, slider.
"""

from datetime import datetime
from dash import callback, Output, Input, State, html, no_update, ctx


def register_callbacks(app):
    """Register all dashboard callbacks with the Dash app."""

    # ═══════════════════════════════════════════════════════════════════
    # LIVE CLOCK — updates date and time every second
    # ═══════════════════════════════════════════════════════════════════
    @app.callback(
        [Output('current-date', 'children'),
         Output('current-time', 'children')],
        Input('clock-interval', 'n_intervals'),
        State('url', 'pathname'),
        prevent_initial_call=True
    )
    def update_clock(_n, pathname):
        path = pathname.rstrip('/') if pathname else ''
        if path in ('', '/login', '/register'):
            return no_update, no_update
        now = datetime.now()
        date_str = now.strftime('%B %d, %Y')        # e.g. "May 22, 2026"
        time_str = now.strftime('%I:%M %p').lstrip('0')  # e.g. "3:35 PM"
        return date_str, time_str

    # ═══════════════════════════════════════════════════════════════════
    # SIMULATION TIMER — increments while status is "running"
    # ═══════════════════════════════════════════════════════════════════
    @app.callback(
        Output('sim-state', 'data'),
        Input('sim-interval', 'n_intervals'),
        State('sim-state', 'data'),
        prevent_initial_call=True
    )
    def update_sim_state(_n, state):
        if state is None:
            state = {'status': 'running', 'elapsed_seconds': 872, 'phase_seconds': 18}

        if state.get('status') == 'running':
            state['elapsed_seconds'] = state.get('elapsed_seconds', 872) + 1
            # Decrement phase timer
            phase = state.get('phase_seconds', 18) - 1
            if phase <= 0:
                import random
                phase = random.randint(15, 35)
            state['phase_seconds'] = phase

        return state

    @app.callback(
        Output('sim-timer', 'children'),
        Input('sim-state', 'data'),
        State('url', 'pathname'),
        prevent_initial_call=True
    )
    def update_sim_timer_display(state, pathname):
        path = pathname.rstrip('/') if pathname else ''
        if path in ('', '/login', '/register'):
            return no_update
            
        total = state.get('elapsed_seconds', 0)
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        return f'{h:02d}:{m:02d}:{s:02d}'

    # ═══════════════════════════════════════════════════════════════════
    # PHASE TIMER — countdown display updated from sim-state
    # ═══════════════════════════════════════════════════════════════════
    @app.callback(
        Output('phase-timer-seconds', 'children'),
        Input('sim-state', 'data'),
        State('url', 'pathname'),
        prevent_initial_call=True
    )
    def update_phase_timer(state, pathname):
        path = pathname.rstrip('/') if pathname else ''
        if path != '/dashboard':
            return no_update
            
        if state is None:
            return '18'
        return str(state.get('phase_seconds', 18))

    # ═══════════════════════════════════════════════════════════════════
    # SIMULATION CONTROL BUTTONS — Start / Pause / Stop / Reset
    # ═══════════════════════════════════════════════════════════════════
    @app.callback(
        [Output('sim-status-badge', 'children'),
         Output('sim-status-badge', 'className'),
         Output('sim-state', 'data', allow_duplicate=True)],
        [Input('btn-start', 'n_clicks'),
         Input('btn-pause', 'n_clicks'),
         Input('btn-stop', 'n_clicks'),
         Input('btn-reset', 'n_clicks')],
        State('sim-state', 'data'),
        prevent_initial_call=True
    )
    def handle_control_buttons(start_clicks, pause_clicks, stop_clicks, reset_clicks, state):
        if state is None:
            state = {'status': 'running', 'elapsed_seconds': 872, 'phase_seconds': 18}

        triggered = ctx.triggered_id

        if triggered == 'btn-start':
            state['status'] = 'running'
            badge_children = [html.Span(className='status-dot'), ' Running']
            badge_class = 'status-badge running'
        elif triggered == 'btn-pause':
            state['status'] = 'paused'
            badge_children = [html.Span(className='status-dot'), ' Paused']
            badge_class = 'status-badge paused'
        elif triggered == 'btn-stop':
            state['status'] = 'stopped'
            badge_children = [html.Span(className='status-dot'), ' Stopped']
            badge_class = 'status-badge stopped'
        elif triggered == 'btn-reset':
            state['status'] = 'stopped'
            state['elapsed_seconds'] = 0
            state['phase_seconds'] = 30
            badge_children = [html.Span(className='status-dot'), ' Stopped']
            badge_class = 'status-badge stopped'
        else:
            return no_update, no_update, no_update

        return badge_children, badge_class, state

    # ═══════════════════════════════════════════════════════════════════
    # 3D VIEW / MAP VIEW TOGGLE
    # ═══════════════════════════════════════════════════════════════════
    @app.callback(
        [Output('btn-3d-view', 'className'),
         Output('btn-map-view', 'className')],
        [Input('btn-3d-view', 'n_clicks'),
         Input('btn-map-view', 'n_clicks')],
        prevent_initial_call=True
    )
    def toggle_view_mode(n_3d, n_map):
        triggered = ctx.triggered_id
        if triggered == 'btn-3d-view':
            return 'toggle-btn active', 'toggle-btn'
        elif triggered == 'btn-map-view':
            return 'toggle-btn', 'toggle-btn active'
        return 'toggle-btn active', 'toggle-btn'
