"""
SMARTFLOW — Dash Callbacks
All interactive callbacks wired to the real simulation engine.
"""

from datetime import datetime
from dash import callback, Output, Input, State, html, no_update, ctx
from flask import session

import services.simulation_service as sim
import services.metrics_service as metrics_svc
import services.scenario_service as scenario_svc


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
         Output('kpi-wait-time-value', 'children'),
         Output('kpi-queue-length-value', 'children'),
         Output('kpi-throughput-value', 'children'),
         Output('kpi-pedestrians-value', 'children'),
         Output('events-feed', 'children')],
        Input('sim-engine-tick', 'data'),
        State('url', 'pathname'),
        prevent_initial_call=True
    )
    def update_dashboard_stats(_ts, pathname):
        path = pathname.rstrip('/') if pathname else ''
        if path not in ('/dashboard', '/simulation'):
            return [no_update] * 9

        state = sim.get_state()
        m = state['metrics']

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

        # Events feed
        raw_events = state.get('events', [])
        event_items = []
        for ev in raw_events[-10:]:
            ev_kind = ev.get('kind', 'info')
            ev_msg = ev.get('message', '')
            et = ev.get('time', 0)
            ft = f"{int(et // 60):02d}:{int(et % 60):02d}:{int((et % 1) * 60):02d}" if isinstance(et, (int, float)) else str(et)
            icon_map = {
                'priority': 'fa-solid fa-truck-medical',
                'signal': 'fa-solid fa-traffic-light',
                'warning': 'fa-solid fa-triangle-exclamation',
                'info': 'fa-solid fa-circle-info',
            }
            event_items.append(
                html.Div(className=f'event-item {ev_kind}', children=[
                    html.Span(ft, className='event-time'),
                    html.Span(className='event-icon', children=[html.I(className=icon_map.get(ev_kind, 'fa-solid fa-circle-info'))]),
                    html.Span(ev_msg, className='event-text'),
                ])
            )

        return (
            [phase_icon, phase_text],
            phase_rem,
            f' {v_count} vehicles',
            f' {p_count} peds',
            avg_wait, avg_queue, throughput, ped_completed,
            event_items,
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
         Output('sim-current-status', 'children'),
         Output('sim-current-status', 'className'),
         Output('simulation-log', 'children')],
        Input('sim-engine-tick', 'data'),
        prevent_initial_call=True
    )
    def update_simulation_page(_ts):
        state = sim.get_state()
        s = state['status']
        t = state['time']
        m = state['metrics']

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

        return elapsed, elapsed, steps, status_text, status_cls, log_items

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
        ns_state, ew_state = 'red', 'red'
        if phase == 'NS_GREEN':
            ns_state, ew_state = 'green', 'red'
        elif phase == 'NS_YELLOW':
            ns_state, ew_state = 'yellow', 'red'
        elif phase == 'EW_GREEN':
            ns_state, ew_state = 'red', 'green'
        elif phase == 'EW_YELLOW':
            ns_state, ew_state = 'red', 'yellow'
        payload = {
            'time': state.get('time', 0),
            'status': state.get('status', 'stopped'),
            'phase': phase,
            'ns_state': ns_state,
            'ew_state': ew_state,
            'vehicles': state.get('vehicles', [])[:50],
            'pedestrians': state.get('pedestrians', [])[:20],
        }
        return json.dumps(payload)

    # ── VIEW TOGGLE (3D / Map) ────────────────────────────────
    app.clientside_callback(
        """
        function(n_3d, n_map) {
            const img = document.getElementById('sim-image');
            const c3d = document.getElementById('three-container');
            if (!img || !c3d) return ['toggle-btn active', 'toggle-btn'];

            const triggered = dash_clientside.callback_context.triggered_id;
            if (triggered === 'btn-map-view') {
                img.style.display = 'block';
                c3d.style.display = 'none';
                return ['toggle-btn', 'toggle-btn active'];
            }
            // Default or btn-3d-view
            img.style.display = 'none';
            c3d.style.display = 'block';
            return ['toggle-btn active', 'toggle-btn'];
        }
        """,
        [Output('btn-3d-view', 'className'),
         Output('btn-map-view', 'className')],
        [Input('btn-3d-view', 'n_clicks'),
         Input('btn-map-view', 'n_clicks')],
        prevent_initial_call=True
    )

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
