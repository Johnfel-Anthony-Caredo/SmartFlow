# SMARTFLOW Implementation Plan Without SUMO

## Overview

SMARTFLOW can be implemented as a complete local traffic simulation and decision-support system without relying on SUMO, while still preserving the original project intent of agent-based traffic modeling, adaptive traffic signal control, scenario testing, local authentication, and dashboard-based monitoring.[cite:1] The original project scope centers on a localized simulation environment, reinforcement learning for traffic signal optimization, a local dashboard, SQLite-based storage, and a live visualization layer; none of those core ideas strictly require SUMO if a custom simulation backend is built in Python.[cite:1]

This implementation plan reframes SMARTFLOW so that the traffic world, vehicle behavior, pedestrian behavior, signal logic, metrics engine, and scenario system are coded directly inside the project backend instead of being delegated to an external simulator.[cite:1] That approach aligns well with the current state of the project, because the dashboard structure, dark-mode visual identity, scenario controls, and visualization shell are already moving forward in Dash even before a live simulator is wired in.[cite:2][cite:3]

## Strategic Direction

The strongest implementation strategy at this stage is to treat SMARTFLOW as a **custom traffic simulation platform** rather than a SUMO integration project.[cite:1] This keeps the capstone focused on the parts that produce the most visible value: simulation logic, reinforcement learning, decision-support workflow, data storage, authentication, and a polished dashboard interface.[cite:1][cite:2]

The custom-backend version should still preserve the academic framing of the project.[cite:1] Vehicles and pedestrians remain autonomous agents, scenarios still represent real traffic and disruption conditions, the traffic signal controller still switches between fixed-time and RL-based logic, and the dashboard still functions as the control-and-analysis layer for experiments.[cite:1]

## Why This Version Is Viable

The project document defines SMARTFLOW through its goals and system architecture, not through a mandatory dependency on SUMO as the only valid engine.[cite:1] SUMO appears in the original stack as the simulation platform, but the deeper contribution of the project is the combination of localized traffic modeling, adaptive control, scenario testing, and dashboard-based decision support.[cite:1]

The current UI files also suggest that the project already has momentum in the dashboard, interaction, and visualization layers.[cite:2][cite:3] The existing Dash app already includes scenario controls, simulation controls, event panels, metric cards, and a stylized intersection scene, which makes it practical to attach a custom backend to the current frontend architecture instead of pausing development until a SUMO pipeline is complete.[cite:2][cite:3]

## System Goal in the New Architecture

The non-SUMO version of SMARTFLOW should simulate one selected or placeholder four-way signalized intersection and adjacent segments, generate vehicles and pedestrians with configurable behavior, evaluate traffic conditions under multiple disruption scenarios, and allow an RL or fixed-time signal controller to manage traffic phases while recording metrics and showing a live visual state inside the dashboard.[cite:1]

In this version, every part of the runtime stack stays inside the project codebase.[cite:1] Python becomes responsible not only for authentication, orchestration, and metrics, but also for the actual simulation engine that updates road-user movement and signal state every time step.[cite:1]

## Proposed Architecture

The revised architecture keeps the same high-level layers described in the project document but replaces the SUMO and TraCI runtime with a direct Python simulation core.[cite:1]

| Layer | Original direction | Revised implementation without SUMO |
|---|---|---|
| Authentication and access | Local login with SQLite.[cite:1] | Keep as-is using SQLite-backed local authentication.[cite:1] |
| Scenario and constraints | Scenario settings passed into SUMO-oriented runs.[cite:1] | Scenario settings passed into a Python simulation engine.[cite:1] |
| Traffic environment | SUMO microscopic simulation.[cite:1] | Custom Python engine with road graph, lane logic, vehicles, pedestrians, and signal phases. |
| Runtime communication | Python + TraCI bridge.[cite:1] | Direct in-process Python calls between engine, controller, and metrics pipeline. |
| RL decision engine | RL observes state and selects phases.[cite:1] | Keep the same concept; only the environment changes.[cite:1] |
| Dashboard and visualization | Dash + Three.js / embedded visualization.[cite:1] | Keep Dash and a browser-rendered live scene fed from Python state.[cite:1][cite:2] |
| Data layer | SQLite + local files.[cite:1] | Keep SQLite for users, runs, metrics, scenarios, and reports.[cite:1] |

## Core Modules to Build

The cleanest implementation is a modular backend organized around a small simulation package and a dashboard package.[cite:1][cite:2]

### Recommended folder structure

```text
smartflow/
├── app.py
├── auth.py
├── database.py
├── config.py
├── pages/
│   ├── login.py
│   ├── register.py
│   └── dashboard.py
├── simulation/
│   ├── engine.py
│   ├── network.py
│   ├── agents.py
│   ├── traffic_light.py
│   ├── scenarios.py
│   ├── metrics.py
│   ├── controllers.py
│   ├── state.py
│   └── serializer.py
├── services/
│   ├── run_manager.py
│   ├── rl_service.py
│   └── report_service.py
├── assets/
│   ├── style.css
│   ├── auth.css
│   ├── smartflow-three.js
│   └── models/
└── data/
    └── smartflow.db
```

This structure matches the project's need for authentication, simulation control, storage, and visualization without tightly coupling every feature into `app.py`.[cite:1][cite:2]

## Traffic Network Design

The custom engine should begin with a simplified but believable four-way signalized intersection, because the project scope already focuses on one selected intersection and nearby segments rather than a city-scale network.[cite:1] A single intersection with a few adjacent road segments is enough to support queue buildup, crossing conflicts, emergency prioritization, road constraints, and fixed-time-versus-RL comparison.[cite:1]

### Recommended network representation

Represent the road system as structured Python objects or JSON:

```python
network = {
    "nodes": {
        "N_IN": {"x": 0, "y": 100},
        "S_IN": {"x": 0, "y": -100},
        "E_IN": {"x": 100, "y": 0},
        "W_IN": {"x": -100, "y": 0},
        "CENTER": {"x": 0, "y": 0}
    },
    "edges": [
        {"id": "north_to_center", "from": "N_IN", "to": "CENTER", "lanes": 2, "speed_limit": 12},
        {"id": "center_to_south", "from": "CENTER", "to": "S_IN", "lanes": 2, "speed_limit": 12}
    ],
    "crosswalks": [
        {"id": "cw_north", "axis": "horizontal", "x1": -8, "x2": 8, "y": 12}
    ],
    "stop_lines": {
        "north": {"x": 0, "y": 16},
        "south": {"x": 0, "y": -16},
        "east": {"x": 16, "y": 0},
        "west": {"x": -16, "y": 0}
    }
}
```

This data model is enough to drive vehicles, define route entry points, set speed limits, place stop lines, and render a visual layout in the dashboard. The selected Tagum City geometry can later be approximated more closely by changing coordinates, lane counts, and turn permissions without redesigning the rest of the system.[cite:1]

## Agent Model

The project document already frames vehicles and pedestrians as autonomous heterogeneous agents.[cite:1] The custom backend should keep that exact concept and implement it directly.

### Vehicle agent design

Each vehicle agent should include:

- Unique ID
- Vehicle type, such as car, bus, truck, emergency vehicle.[cite:1]
- Position, speed, acceleration, and heading
- Current edge/lane
- Planned route, such as north-to-south or east-to-west
- Behavior profile, such as normal, aggressive, cautious, delayed-reacting.[cite:1]
- Waiting-time counters
- Queue-state flag
- Active flag for completion/removal

A basic car-following model is sufficient for this capstone implementation. The model only needs to do the following reliably:

- Slow down when another vehicle is too close
- Stop at a red signal or blocked lane
- Accelerate toward a target speed when clear
- Respect route direction and lane assignment
- Yield or respond differently under emergency or pedestrian-priority conditions

### Pedestrian agent design

Each pedestrian agent should include:

- Unique ID
- Spawn point and target crossing
- Walking speed
- Compliance type, such as compliant, slow, non-compliant, group-heavy.[cite:1]
- State, such as waiting, crossing, finished
- Delay timer

Pedestrians do not need full crowd simulation. For the scope of SMARTFLOW, they only need to spawn, wait for a permitted crossing or cross unsafely based on profile, and occupy the crosswalk long enough to affect signal decisions and delay metrics.[cite:1]

## Signal Control Model

The project requires comparison between fixed-time control and RL-based adaptive control.[cite:1] The traffic-light subsystem should therefore support both controller modes using the same signal state machine underneath.

### Fixed-time controller

Implement a standard cycle such as:

1. North-South green
2. Yellow transition
3. All-red clearance
4. East-West green
5. Yellow transition
6. All-red clearance

Store configurable durations in the database or a scenario configuration object so the baseline can be tuned and rerun consistently.[cite:1]

### RL controller

The RL controller should observe the live state of the custom environment and select an action such as:

- Switch to North-South green
- Switch to East-West green
- Extend current phase
- Trigger pedestrian-priority phase
- Apply emergency-priority handling

The project document proposes observation features such as queue length, waiting time, pedestrian demand, current phase, emergency presence, and disruption conditions, and those same features can be computed directly from the custom engine.[cite:1] This means the RL design can stay academically aligned with the original proposal even after removing SUMO.[cite:1]

## Simulation Loop

The custom engine should run at a fixed simulation step, such as 0.25 seconds, 0.5 seconds, or 1 second depending on the smoothness needed for visualization and metrics. At every step, the engine should:

1. Spawn new vehicles and pedestrians according to the selected scenario.[cite:1]
2. Update the signal controller.
3. Update each vehicle agent.
4. Update each pedestrian agent.
5. Resolve removals for completed trips.
6. Compute current metrics such as queue length, waiting time, throughput, and occupancy.[cite:1]
7. Build a serialized simulation-state payload for the dashboard.
8. Persist periodic snapshots and end-of-run summaries to SQLite.[cite:1]

### Example high-level engine loop

```python
while simulation_running:
    scenario_manager.spawn_agents(engine_state)
    controller.update(engine_state)
    vehicle_system.update_all(engine_state, dt)
    pedestrian_system.update_all(engine_state, dt)
    metrics_collector.update(engine_state)
    payload = serializer.to_dashboard_payload(engine_state)
    dashboard_state_cache.set(payload)
    clock += dt
```

This loop replaces the role that SUMO and TraCI would normally play.[cite:1]

## Scenario System

One of the strongest parts of SMARTFLOW is its scenario-based experimentation design.[cite:1] The non-SUMO version should preserve that strength by making scenarios first-class configuration objects.

### Base scenario fields

- Scenario name
- Traffic density level
- Pedestrian density level
- Emergency vehicle mode
- Construction flag
- Accident flag
- Flooding flag
- Temporary blockage flag
- Control mode, fixed-time or RL.[cite:1]

### How scenarios should affect the engine

| Scenario variable | Engine effect |
|---|---|
| Traffic density | Increase vehicle spawn rate |
| Pedestrian density | Increase pedestrian spawn rate |
| Emergency vehicle | Spawn priority vehicles with urgency rules |
| Lane closure | Disable one lane or reduce capacity |
| Construction | Reduce speed on an approach and add blockage zone |
| Accident | Block an edge partially or fully |
| Flooding | Lower speed and reduce usable lane count |
| Temporary blockage | Pause or compress flow on one segment |

This design keeps disruptions understandable, controllable, and easy to demonstrate during evaluation.[cite:1]

## Metrics and Evaluation Logic

The project document already specifies the main evaluation metrics, and the custom engine should compute the same outputs so the study remains aligned with its original objectives.[cite:1]

### Metrics to implement

- Average vehicle waiting time.[cite:1]
- Average queue length.[cite:1]
- Maximum queue length.[cite:1]
- Throughput.[cite:1]
- Average pedestrian delay.[cite:1]
- Emergency vehicle clearance time.[cite:1]
- Signal phase efficiency.[cite:1]
- Congestion severity under disruption conditions.[cite:1]

### Suggested logging layers

- Per-step in-memory metrics for live dashboard updates
- Per-interval summaries every few seconds for charting
- Per-run final metrics written to SQLite
- Optional CSV export per experiment

## Dashboard Integration

The current Dash app already has a strong shell for simulation control and display.[cite:2][cite:3] The custom backend should plug into that shell rather than replacing it.

### Existing dashboard elements that can be reused

- Scenario selector in the header.[cite:2]
- Simulation timer and status badge.[cite:2]
- Start, pause, stop, and reset controls.[cite:2]
- KPI cards for waiting time, queue length, throughput, pedestrians, and emergencies.[cite:2]
- RL panel and event list.[cite:2]
- Visualization panel with an intersection scene.[cite:2][cite:3]
- Dark-mode styling system with branded SMARTFLOW tokens and dashboard components.[cite:3]

### Required integration pattern

The engine should expose a compact state object such as:

```json
{
  "time": 123.5,
  "status": "running",
  "phase": "NS_GREEN",
  "vehicles": [
    {"id": "veh_1", "x": 12.4, "y": 6.8, "heading": 90, "type": "car"}
  ],
  "pedestrians": [
    {"id": "ped_1", "x": -4.1, "y": 8.3, "state": "crossing"}
  ],
  "metrics": {
    "avg_wait": 24.8,
    "avg_queue": 5.2,
    "throughput": 1842
  },
  "events": [
    {"kind": "warning", "message": "High congestion north approach"}
  ]
}
```

Dash callbacks or periodic polling can read this state and update both the card values and the visualization panel.[cite:2]

## Visualization Plan

The project document includes a Dash and Three.js user-interface layer, and the current stylesheet already reflects a strong intersection-based visual language.[cite:1][cite:3] For this implementation phase, there are two practical options.

### Option A: Start with the existing stylized 2D/2.5D dashboard scene

This is the fastest path because the current CSS already includes roads, sidewalks, lane markings, traffic lights, vehicles, pedestrians, crosswalks, overlays, and animated states.[cite:3] The custom engine can simply replace the hardcoded visual positions with live values over time through Dash-rendered components or a lightweight JS bridge.[cite:2][cite:3]

### Option B: Upgrade to Three.js with ready-made 3D assets

This is also viable, but it should be treated as a second-phase improvement rather than a blocker. The engine only needs to provide a real-time list of objects and positions; the frontend can then map those values to GLB car, bus, truck, traffic light, and road models rendered in Three.js.

The implementation rule should be simple: **the simulation engine owns behavior, the visualization layer only renders state**. That separation prevents the frontend from becoming responsible for traffic logic.

## Authentication and Access Control

The project document explicitly includes local authentication backed by SQLite.[cite:1] That should remain unchanged in the non-SUMO version because it still protects scenarios, simulation runs, stored reports, and experiment history.[cite:1]

The login and register pages should follow the SMARTFLOW dashboard visual identity rather than looking like a disconnected generic auth interface, because the stylesheet already establishes a dark, premium, control-center theme with strong branding and green accent tokens.[cite:3] Session storage should continue to protect routes and keep the dashboard available only to authenticated users.

## Database Design

SQLite remains the most suitable data layer for this project because the system is local, structured, and experiment-driven.[cite:1] The database should include at least the following tables.

### Recommended tables

| Table | Purpose |
|---|---|
| `users` | Store local accounts, password hashes, and roles.[cite:1] |
| `scenarios` | Save reusable scenario presets and demand settings.[cite:1] |
| `simulation_runs` | Record each experiment's metadata, timestamps, controller mode, and status.[cite:1] |
| `run_metrics` | Store final and interval-based metrics for each run.[cite:1] |
| `events` | Save major runtime events, warnings, and signal changes |
| `reports` | Track generated summaries and exported results |
| `rl_models` | Store model versions, checkpoints, or metadata if needed |

### Example minimum schema fields

- `users`: id, username, email, password_hash, role, created_at
- `scenarios`: id, name, traffic_density, pedestrian_density, emergency_mode, lane_closure, accident, flooding, control_mode
- `simulation_runs`: id, scenario_id, user_id, started_at, ended_at, status, control_mode, duration_seconds
- `run_metrics`: id, run_id, avg_wait, avg_queue, max_queue, throughput, ped_delay, emergency_clearance, phase_efficiency

## Reinforcement Learning Roadmap

The project document suggests DQN or Double DQN as a suitable RL approach for capstone-level adaptive signal control.[cite:1] That recommendation still fits this implementation path because the RL problem stays the same even though the environment changes.[cite:1]

### Suggested RL phases

#### Phase 1: Fixed-time only

Implement the environment, baseline controller, metrics collection, and dashboard updates first. This proves the engine and the evaluation pipeline work correctly before any AI is introduced.

#### Phase 2: Rule-based adaptive controller

Add a simple handcrafted adaptive controller, such as switching green based on queue thresholds. This creates an intermediate benchmark between fixed-time and RL.

#### Phase 3: RL environment wrapper

Wrap the simulation engine in an RL training interface that exposes:

- `reset()`
- `step(action)`
- `get_state()`
- `get_reward()`
- `done`

#### Phase 4: Train DQN/Double DQN

Train the controller on repeated episodes using the custom environment. Save checkpoints locally and evaluate the trained model across unseen scenarios.[cite:1]

#### Phase 5: Dashboard deployment of trained policy

Load the trained model during a live dashboard run and let it choose traffic signal actions in real time.

## Recommended Development Phases

The safest way to implement SMARTFLOW without SUMO is to build vertically in working slices.

### Phase 1: Project foundation

- Finalize folder structure
- Set up SQLite
- Complete login/register/logout/session routing
- Refactor dashboard pages into modular files
- Keep the current dark UI direction intact.[cite:2][cite:3]

### Phase 2: Static dashboard simulation shell

- Replace placeholder controls with real state containers
- Define scenario objects
- Add run status, timer, and reset flow
- Keep the current stylized intersection panel as the temporary visual layer.[cite:2][cite:3]

### Phase 3: Custom simulation engine

- Build network definitions
- Build vehicle and pedestrian agents
- Build signal state machine
- Build fixed-time controller
- Run the engine in Python without RL

### Phase 4: Metrics and storage

- Compute live metrics
- Save run summaries to SQLite
- Add charts based on real run data instead of mock/random data.[cite:2]

### Phase 5: Scenario system

- Implement density presets
- Add disruption effects
- Add emergency priority behavior
- Validate that scenarios visibly change output metrics

### Phase 6: Visualization upgrade

- Connect engine state to live frontend positions
- Decide whether to keep stylized CSS scene or move to Three.js
- If moving to Three.js, load ready-made GLB assets and bind them to simulation objects

### Phase 7: RL integration

- Add environment wrapper
- Train and save a DQN-based controller.[cite:1]
- Compare RL versus fixed-time across multiple scenarios.[cite:1]

### Phase 8: Reporting and capstone readiness

- Generate experiment summaries
- Add comparative charts and result export
- Write interpretation notes for thesis defense/demo use

## Minimum Viable Product Definition

A real MVP for SMARTFLOW without SUMO should include the following:

- Working local authentication and protected dashboard routes.[cite:1]
- One four-way intersection network.
- Vehicle spawning and movement.
- Pedestrian spawning and crossing.
- Fixed-time traffic light controller.
- At least three scenarios, such as low traffic, heavy traffic, and emergency vehicle.[cite:1]
- Live KPI updates for wait time, queue length, and throughput.[cite:1]
- Event logging panel.
- End-of-run metrics stored in SQLite.[cite:1]
- Visualization panel reflecting live engine state.

That MVP is already strong enough for a capstone demo because it proves end-to-end system integration even before RL is fully complete.[cite:1][cite:2]

## Stretch Goals

After the MVP, the project can be extended through:

- Three.js 3D visualization with downloaded GLB assets
- Multiple behavior profiles with more realistic car-following parameters
- A rule-based adaptive controller baseline
- RL training dashboard panel with checkpoint stats
- Experiment comparison page across scenarios
- Export to CSV or PDF summary files
- Role-based permissions for admin versus viewer users

## Risks and Mitigation

### Risk 1: Overbuilding the simulation engine

A custom engine can become too ambitious if it tries to match full traffic-simulator realism. The mitigation is to build only what the capstone needs: believable queueing, signal response, crossing conflicts, and measurable outputs.

### Risk 2: Coupling visualization with logic

If vehicle motion is computed in frontend JavaScript instead of the backend, the project becomes harder to debug and harder to evaluate. The mitigation is to compute all traffic behavior in Python and send only render-ready state to the dashboard.

### Risk 3: RL added too early

If RL is introduced before the environment is stable, debugging becomes confusing. The mitigation is to finish the fixed-time environment, metrics, and scenario system first.

### Risk 4: Dashboard still uses placeholder data too long

The current app uses mock/randomized chart values in places.[cite:2] The mitigation is to replace one UI area at a time with real simulation state as soon as the backend module becomes available.

## Suggested Implementation Priorities

If the project must move quickly, the recommended order is:

1. Finish authentication flow and route protection.
2. Refactor the dashboard into maintainable modules.
3. Implement the simulation engine with one fixed-time controller.
4. Replace dashboard mock metrics with real engine outputs.
5. Save runs and metrics to SQLite.
6. Add scenario effects.
7. Add rule-based adaptive control.
8. Add RL only after the environment is stable.
9. Upgrade visualization quality last.

This sequence gives the project visible progress early while protecting the core architecture from unnecessary rework.

## Definition of Done

The non-SUMO implementation of SMARTFLOW can be considered functionally complete when all of the following are true:

- A user can log in and access the dashboard securely.[cite:1]
- A user can select a scenario and start a simulation.[cite:1][cite:2]
- Vehicles and pedestrians are generated and updated by the custom Python backend.
- Signal phases influence movement and queueing.
- Live metrics update during the run.[cite:1]
- Results are saved to SQLite at the end of each experiment.[cite:1]
- The visualization reflects current state instead of hardcoded mock positions.[cite:2][cite:3]
- Fixed-time and RL-based control can be compared on the same scenarios.[cite:1]
- The system produces clear evidence of traffic-performance differences across scenarios.[cite:1]

## Final Recommendation

SMARTFLOW should move forward immediately as a custom Python-based agent simulation platform with Dash as the control interface, SQLite as the local data layer, and a live dashboard visualization driven directly by simulation state.[cite:1][cite:2] This path preserves the spirit and research objectives of the original project while removing the dependency that would otherwise delay implementation.[cite:1]

The most practical success strategy is to build the project in layers: stabilize authentication and dashboard flow first, implement a believable but intentionally simplified simulation core second, connect real metrics and storage third, and add RL and higher-fidelity visualization only after the environment is stable.[cite:1][cite:2][cite:3] That approach keeps the project demonstrable at every stage and gives the capstone a much higher chance of reaching a polished, defendable final system.[cite:1]
