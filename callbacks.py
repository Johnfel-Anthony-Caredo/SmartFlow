"""
SMARTFLOW — Dash Callbacks
All interactive callbacks wired to the real simulation engine.
"""

from datetime import datetime
from dash import callback, Output, Input, State, html, no_update, ctx
from flask import session
import plotly.graph_objects as go

import services.simulation_service as sim
import services.metrics_service as metrics_svc
import services.scenario_service as scenario_svc
from simulation.sumo_state import canonical_signal_states


def _chart_layout(title: str, yaxis_title: str = "") -> dict:
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#64748b', size=10),
        margin=dict(l=35, r=10, t=30, b=30),
        xaxis=dict(gridcolor='rgba(255,255,255,0.03)', tickfont=dict(size=9), showline=False),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.03)',
            tickfont=dict(size=9),
            showline=False,
            title=dict(text=yaxis_title, font=dict(size=10, color='#64748b')),
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(10,15,26,0.95)',
            bordercolor='rgba(255,255,255,0.08)',
            font=dict(family='Inter', size=11, color='#94a3b8'),
        ),
        title=dict(text=title, font=dict(size=12, color='#94a3b8')),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5, font=dict(size=10)),
    )


def _build_traffic_flow_figure(history: list[dict]) -> go.Figure:
    labels = [f"{point.get('time', 0):.0f}s" for point in history]
    fig = go.Figure()
    fill_colors = {
        'north': 'rgba(0,230,118,0.12)',
        'south': 'rgba(66,165,245,0.12)',
        'east': 'rgba(171,71,188,0.12)',
        'west': 'rgba(255,167,38,0.12)',
    }
    for key, label, color in (
        ('north', 'North', '#00e676'),
        ('south', 'South', '#42a5f5'),
        ('east', 'East', '#ab47bc'),
        ('west', 'West', '#ffa726'),
    ):
        fig.add_trace(go.Scatter(
            x=labels,
            y=[point.get(key, 0) for point in history],
            name=label,
            mode='lines',
            line=dict(color=color, width=2),
            fill='tozeroy',
            fillcolor=fill_colors[key],
        ))
    fig.update_layout(**_chart_layout('Live Queue Pressure by Approach', 'Queued vehicles'))
    return fig


def _build_wait_time_figure(wait_history: list[dict], queue_history: list[dict]) -> go.Figure:
    labels = [f"{point.get('time', 0):.0f}s" for point in wait_history]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=[point.get('value', 0) for point in wait_history],
        name='Avg Wait',
        mode='lines',
        line=dict(color='#00e676', width=2),
        fill='tozeroy',
        fillcolor='rgba(0,230,118,0.12)',
    ))
    fig.add_trace(go.Scatter(
        x=[f"{point.get('time', 0):.0f}s" for point in queue_history],
        y=[point.get('value', 0) for point in queue_history],
        name='Avg Queue',
        mode='lines',
        line=dict(color='#ef5350', width=2, dash='dash'),
    ))
    fig.update_layout(**_chart_layout('Live Wait vs Queue Trend', 'Seconds / vehicles'))
    return fig


def _format_elapsed(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    mt, st = divmod(rem, 60)
    return f'{h:02d}:{mt:02d}:{st:02d}'


def _format_event_time(value) -> str:
    if not isinstance(value, (int, float)):
        return str(value)
    return f"{int(value // 60):02d}:{int(value % 60):02d}"


def _build_event_items(raw_events: list[dict], class_prefix: str = 'event', limit: int = 10) -> list:
    icon_map = {
        'priority': 'fa-solid fa-truck-medical',
        'signal': 'fa-solid fa-traffic-light',
        'warning': 'fa-solid fa-triangle-exclamation',
        'info': 'fa-solid fa-circle-info',
    }
    if not raw_events:
        return [html.Div(className=f'{class_prefix}-item info', children=[
            html.Span('--:--', className=f'{class_prefix}-time'),
            html.Span(className=f'{class_prefix}-icon', children=[html.I(className='fa-solid fa-circle-info')]),
            html.Span('No live events yet', className=f'{class_prefix}-text'),
        ])]

    items = []
    for ev in raw_events[-limit:]:
        ev_kind = ev.get('kind', 'info')
        ev_msg = ev.get('message', '')
        items.append(html.Div(className=f'{class_prefix}-item {ev_kind}', children=[
            html.Span(_format_event_time(ev.get('time', 0)), className=f'{class_prefix}-time'),
            html.Span(className=f'{class_prefix}-icon', children=[
                html.I(className=icon_map.get(ev_kind, 'fa-solid fa-circle-info')),
            ]),
            html.Span(ev_msg, className=f'{class_prefix}-text'),
        ]))
    return items


def _status_badge(status: str):
    if status == 'running':
        return [html.Span(className='status-dot'), ' Running'], 'status-badge running'
    if status == 'paused':
        return [html.Span(className='status-dot'), ' Paused'], 'status-badge paused'
    return [html.Span(className='status-dot'), ' Stopped'], 'status-badge stopped'


def register_callbacks(app):
    """Register all dashboard callbacks with the Dash app."""

    # ── LIVE CLOCK ────────────────────────────────────────────
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
        date_str = now.strftime('%B %d, %Y')
        time_str = now.strftime('%I:%M %p').lstrip('0')
        return date_str, time_str

    # ── ENGINE STEP ───────────────────────────────────────────
    @app.callback(
        Output('sim-engine-tick', 'data'),
        Input('sim-interval', 'n_intervals'),
        prevent_initial_call=True
    )
    def step_engine(_n):
        if sim.current_status() == 'running':
            sim.step(num_ticks=1)
        return datetime.now().timestamp()

    # ── HEADER STATUS UPDATE ──────────────────────────────────
    @app.callback(
        [Output('sim-timer', 'children'),
         Output('sim-status-badge', 'children'),
         Output('sim-status-badge', 'className')],
        Input('sim-engine-tick', 'data'),
        prevent_initial_call=True
    )
    def update_header_status(_ts):
        state = sim.get_state()
        s = state['status']
        t = state['time']

        # Timer
        h, rem = divmod(int(t), 3600)
        mt, st = divmod(rem, 60)
        timer_str = f'{h:02d}:{mt:02d}:{st:02d}'

        # Status badge
        if s == 'running':
            badge_children = [html.Span(className='status-dot'), ' Running']
            badge_cls = 'status-badge running'
        elif s == 'paused':
            badge_children = [html.Span(className='status-dot'), ' Paused']
            badge_cls = 'status-badge paused'
        else:
            badge_children = [html.Span(className='status-dot'), ' Stopped']
            badge_cls = 'status-badge stopped'
            
        return timer_str, badge_children, badge_cls

    # ── DASHBOARD UI UPDATE ───────────────────────────────────
    @app.callback(
        [Output('sim-phase-display', 'children'),
         Output('phase-timer-seconds', 'children'),
         Output('stat-vehicles', 'children'),
         Output('stat-pedestrians', 'children'),
         Output('stat-emergency', 'children'),
         Output('kpi-wait-time-value', 'children'),
         Output('kpi-queue-length-value', 'children'),
         Output('kpi-throughput-value', 'children'),
         Output('kpi-pedestrians-value', 'children'),
         Output('kpi-emergency-value', 'children'),
         Output('events-feed', 'children')],
        Input('sim-engine-tick', 'data'),
        State('url', 'pathname'),
        prevent_initial_call=True
    )
    def update_dashboard_stats(_ts, pathname):
        path = pathname.rstrip('/') if pathname else ''
        if path not in ('/dashboard', '/simulation'):
            return [no_update] * 11

        state = sim.get_state()
        m = state['metrics']
        dashboard = state.get('dashboard', {})

        # Phase
        phase = state.get('phase', 'NS_GREEN')
        phase_text = f' {phase.replace("_", " ")}'
        phase_icon = html.I(className='fa-solid fa-traffic-light')

        # Phase remaining
        phase_rem = str(int(state.get('phase_remaining', 0)))

        # Stat chips
        v_count = state.get('vehicle_count', 0)
        p_count = state.get('pedestrian_count', 0)

        # KPI values
        avg_wait = str(m.get('avg_wait', 0))
        avg_queue = str(m.get('avg_queue', 0))
        throughput = str(m.get('throughput', 0))
        ped_completed = str(m.get('total_pedestrians_completed', 0))
        emergency_count = str(dashboard.get('emergency_active_count', 0))

        event_items = _build_event_items(state.get('events', []), limit=10)

        return (
            [phase_icon, phase_text],
            phase_rem,
            f' {v_count} vehicles',
            f' {p_count} peds',
            f' {emergency_count} EV',
            avg_wait, avg_queue, throughput, ped_completed,
            emergency_count,
            event_items,
        )

    @app.callback(
        [Output('traffic-flow-chart', 'figure'),
         Output('wait-time-chart', 'figure')],
        Input('sim-engine-tick', 'data'),
        State('url', 'pathname'),
        prevent_initial_call=True
    )
    def update_dashboard_charts(_ts, pathname):
        path = pathname.rstrip('/') if pathname else ''
        if path != '/dashboard':
            return no_update, no_update

        charts = sim.get_state().get('charts', {})
        traffic_history = charts.get('traffic_flow', [])
        wait_history = charts.get('wait_time', [])
        queue_history = charts.get('queue_length', [])
        return (
            _build_traffic_flow_figure(traffic_history),
            _build_wait_time_figure(wait_history, queue_history),
        )

    # ── CONTROL BUTTONS (dashboard) ───────────────────────────
    @app.callback(
        Output('sim-engine-tick', 'data', allow_duplicate=True),
        [Input('btn-start', 'n_clicks'),
         Input('btn-pause', 'n_clicks'),
         Input('btn-stop', 'n_clicks'),
         Input('btn-reset', 'n_clicks')],
        prevent_initial_call=True
    )
    def handle_controls(start_clicks, pause_clicks, stop_clicks, reset_clicks):
        triggered = ctx.triggered_id
        if triggered == 'btn-start':
            sim.resume() if sim.current_status() == 'paused' else sim.start()
        elif triggered == 'btn-pause':
            sim.pause()
        elif triggered == 'btn-stop':
            sim.stop()
        elif triggered == 'btn-reset':
            sim.reset()
        return datetime.now().timestamp()

    # ── CONTROL BUTTONS (simulation page) ─────────────────────
    @app.callback(
        Output('sim-engine-tick', 'data', allow_duplicate=True),
        [Input('start-btn', 'n_clicks'),
         Input('pause-btn', 'n_clicks'),
         Input('stop-btn', 'n_clicks'),
         Input('reset-btn', 'n_clicks')],
        prevent_initial_call=True
    )
    def handle_sim_controls(sc, pc, stc, rc):
        triggered = ctx.triggered_id
        if triggered == 'start-btn':
            sim.resume() if sim.current_status() == 'paused' else sim.start()
        elif triggered == 'pause-btn':
            sim.pause()
        elif triggered == 'stop-btn':
            sim.stop()
        elif triggered == 'reset-btn':
            sim.reset()
        return datetime.now().timestamp()

    # ── SIMULATION PAGE STATS ─────────────────────────────────
    @app.callback(
        [Output('sim-elapsed', 'children'),
         Output('sim-time', 'children'),
         Output('sim-steps', 'children'),
         Output('sim-active-scenario', 'children'),
         Output('sim-control-mode', 'children'),
         Output('sim-current-status', 'children'),
         Output('sim-current-status', 'className'),
         Output('sim-last-action', 'children'),
         Output('sim-last-error', 'children'),
         Output('sim-run-id', 'children'),
         Output('simulation-log', 'children')],
        Input('sim-engine-tick', 'data'),
        prevent_initial_call=True
    )
    def update_simulation_page(_ts):
        state = sim.get_state()
        s = state['status']
        t = state['time']
        m = state['metrics']
        dashboard = state.get('dashboard', {})

        elapsed = f"{int(t // 3600):02d}:{int((t % 3600) // 60):02d}:{int(t % 60):02d}"
        steps = str(m.get('step_count', 0))

        if s == 'running':
            status_text, status_cls = 'Running', 'sim-stat-badge running'
        elif s == 'paused':
            status_text, status_cls = 'Paused', 'sim-stat-badge paused'
        else:
            status_text, status_cls = 'Idle', 'sim-stat-badge idle'

        raw_events = state.get('events', [])
        if not raw_events:
            log_items = [html.Div(className='event-item info', children=[
                html.Span('--:--:--', className='event-time'),
                html.I(className='fa-solid fa-circle-info event-icon'),
                html.Span('No events yet', className='event-text'),
            ])]
        else:
            log_items = []
            for ev in raw_events[-20:]:
                ev_kind = ev.get('kind', 'info')
                ev_msg = ev.get('message', '')
                et = ev.get('time', 0)
                ft = f"{int(et // 60):02d}:{int(et % 60):02d}"
                im = {
                    'priority': 'fa-solid fa-truck-medical',
                    'signal': 'fa-solid fa-traffic-light',
                    'warning': 'fa-solid fa-triangle-exclamation',
                    'info': 'fa-solid fa-circle-info',
                }
                log_items.append(html.Div(className=f'event-item {ev_kind}', children=[
                    html.Span(ft, className='event-time'),
                    html.I(className=f'{im.get(ev_kind, "fa-solid fa-circle-info")} event-icon'),
                    html.Span(ev_msg, className='event-text'),
                ]))

        return (
            elapsed,
            elapsed,
            steps,
            dashboard.get('current_scenario_name', 'Unknown'),
            dashboard.get('control_mode_label', 'Fixed-Time'),
            status_text,
            status_cls,
            dashboard.get('last_action', '—'),
            dashboard.get('last_error', 'None'),
            dashboard.get('run_id', '—'),
            log_items,
        )

    # ── SCENARIO APPLY (dashboard) ────────────────────────────
    @app.callback(
        Output('sim-engine-tick', 'data', allow_duplicate=True),
        Input('btn-apply-scenario', 'n_clicks'),
        [State('traffic-density-dropdown', 'value'),
         State('pedestrian-density-dropdown', 'value'),
         State('emergency-vehicle-dropdown', 'value'),
         State('road-constraint-dropdown', 'value')],
        prevent_initial_call=True
    )
    def apply_scenario(n, traffic, pedestrian, emergency, road_constraint):
        if not n:
            return no_update
        density_map = {'Very High': 'heavy', 'High': 'heavy', 'Medium': 'medium', 'Low': 'low', 'None': 'none'}
        emap = {'Disabled': 'disabled', 'Enabled (1 Ambulance)': 'enabled', 'Enabled (2 Vehicles)': 'enabled'}
        sim.configure(
            traffic_density=density_map.get(traffic, 'medium'),
            pedestrian_density=density_map.get(pedestrian, 'medium'),
            emergency_mode=emap.get(emergency, 'disabled'),
            road_constraint=road_constraint or 'None',
        )
        return datetime.now().timestamp()

    # ── SIM PAGE CONFIG APPLY ─────────────────────────────────
    @app.callback(
        Output('sim-engine-tick', 'data', allow_duplicate=True),
        Input('apply-btn', 'n_clicks'),
        State('sim-traffic-density', 'value'),
        prevent_initial_call=True
    )
    def apply_sim_config(n, traffic):
        if not n:
            return no_update
        density_map = {'Very High': 'heavy', 'High': 'heavy', 'Medium': 'medium', 'Low': 'low'}
        sim.configure(traffic_density=density_map.get(traffic, 'medium'))
        return datetime.now().timestamp()

    # ── SCENARIO DROPDOWN (header) ────────────────────────────
    @app.callback(
        Output('sim-engine-tick', 'data', allow_duplicate=True),
        Input('scenario-dropdown', 'value'),
        prevent_initial_call=True
    )
    def header_scenario_changed(scenario_value):
        if not scenario_value:
            return no_update
        # Load scenario from DB by matching name patterns
        scenarios = scenario_svc.get_presets()
        for sc in scenarios:
            name = sc.get('name', '').lower()
            val = scenario_value.lower()
            if val in name or name in val:
                scenario_svc.load_into_engine(sc['id'], sim.get_engine())
                break
        return datetime.now().timestamp()

    # ── ENGINE STATE JSON (for Three.js bridge) ──────────────
    @app.callback(
        Output('engine-state-json', 'data'),
        Input('sim-engine-tick', 'data'),
        prevent_initial_call=True
    )
    def serialize_engine_state(_ts):
        import json
        state = sim.get_state()
        phase = state.get('phase', 'NS_GREEN')
        ns_state, ew_state = canonical_signal_states(phase)
        payload = {
            'time': state.get('time', 0),
            'status': state.get('status', 'stopped'),
            'phase': phase,
            'ns_state': ns_state,
            'ew_state': ew_state,
            'vehicles': state.get('vehicles', [])[:50],
            'pedestrians': state.get('pedestrians', [])[:20],
            'queues': state.get('queues', {}),
            'visual': state.get('visual', {}),
            'scenario': state.get('scenario', {}),
        }
        return json.dumps(payload)

    # ── THREE.JS CLIENTSIDE — pipes JSON state into scene ────
    app.clientside_callback(
        """
        function(jsonStr) {
            try {
                const state = (jsonStr && jsonStr !== '{}') ? JSON.parse(jsonStr) : { status: 'stopped' };
                if (window.SmartFlowScene && window.SmartFlowScene.update) {
                    window.SmartFlowScene.update(state);
                }
            } catch(e) { console.error('[SmartFlow] Three.js error:', e); }
            return window.dash_clientside.no_update;
        }
        """,
        Output('three-container', 'style'),
        Input('engine-state-json', 'data'),
        prevent_initial_call=False
    )
