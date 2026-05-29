# SMARTFLOW - Codebase Status

**Generated:** 2026-05-29
**Last Updated:** 2026-05-29
**Project:** SMARTFLOW - AI-Driven Traffic Simulation and Signal Control Dashboard
**Workspace:** `C:\Users\jhepo\Desktop\trapik2`

---

## 1. Executive Summary

SMARTFLOW is no longer best described as a "no-SUMO dashboard shell." The current implementation is a **SUMO-first traffic simulation stack** with:

- Dash for the web app and operator dashboard
- SQLite for users, roles, scenarios, runs, and admin data
- TraCI for live simulation control and state extraction
- Three.js for the embedded 3D scene
- SUMO network geometry exported into JSON for the scene renderer

The main application shell is solid: authentication, admin tools, scenario CRUD, dashboard layout, and simulation controls are all in place. The live simulation path now runs through **`simulation/sumo_engine.py`** and **`services/simulation_service.py`**, not the old custom Python traffic engine.

The biggest remaining gap is **visual fidelity and calibration**, not basic connectivity. The system is already wired end-to-end; what still needs work is making the rendered scene better match the intended road structure and polishing the remaining pages that are still partially mock or stubbed.

---

## 2. Current Architecture

### Canonical Runtime Path

The active runtime path is:

1. SUMO network/config lives in `sumo/intersection_1/`
2. `simulation/sumo_engine.py` starts and steps SUMO through TraCI
3. `services/simulation_service.py` exposes a shared SUMO-backed engine to Dash callbacks
4. `callbacks.py` reads runtime state and updates dashboard KPIs, charts, status, and 3D payloads
5. `tools/export_sumo_visual_network.py` exports clipped SUMO geometry into `assets/generated/visual_network.json`
6. `assets/three-bridge.mjs` renders roads, crossings, sidewalks, signals, vehicles, pedestrians, emergency vehicles, and road constraints from exported geometry plus live runtime state

### Important Clarification

The repository still contains the earlier custom engine modules under `simulation/`:

- `engine.py`
- `network.py`
- `vehicles.py`
- `pedestrians.py`
- `traffic_light.py`
- `controllers.py`
- `metrics.py`

Those files are now **legacy/reference/fallback code**, not the intended primary simulation backend.

---

## 3. What Is Working

### 3.1 Authentication and Access Control

Implemented and usable:

- Login and registration flows
- Password hashing and session handling
- Rate-limited login protection
- First-login password change flow
- Role-based access control and permission checks
- Audit logging around auth/admin actions

Auth UI status:

- Login and register pages were redesigned into a **full-screen split layout**
- The extra hero CTA was removed
- Autofill styling was fixed so browsers do not paint bright white fields over the design

Primary files:

- `pages/login.py`
- `pages/register.py`
- `pages/change_password.py`
- `assets/auth.css`
- `auth.py`

### 3.2 Database and Admin Features

Working:

- SQLite schema and seed data
- User management
- Role and access control page
- Audit logs
- Backup/restore UI
- Scenario CRUD

Primary files:

- `database.py`
- `pages/admin_users.py`
- `pages/admin_roles.py`
- `pages/admin_audit.py`
- `pages/admin_backups.py`
- `pages/scenarios.py`

### 3.3 SUMO Runtime Integration

Implemented:

- Shared SUMO-backed engine instance
- Start, pause, resume, stop, reset lifecycle
- Fixed-time signal phase progression through TraCI
- Vehicle and pedestrian sampling from SUMO
- Dashboard-ready metrics payloads
- Scenario-based runtime configuration
- Emergency vehicle marking
- Road constraint marker payload generation

Primary files:

- `simulation/sumo_engine.py`
- `simulation/sumo_state.py`
- `simulation/sumo_config.py`
- `services/simulation_service.py`

### 3.4 Dashboard Wiring

Implemented:

- Dashboard stats update from live runtime state
- Dashboard chart update from runtime chart histories
- Simulation control buttons wired to runtime lifecycle
- Scenario application wired into runtime configuration
- Three.js state handoff through Dash callbacks

Primary file:

- `callbacks.py`

### 3.5 SUMO Geometry Export + Three.js Renderer

Implemented:

- Main intersection scope definition
- Exporter that converts SUMO geometry into a renderer-friendly JSON file
- Road, lane, crossing, walking area, and signal rendering from exported geometry
- Runtime-driven vehicles and pedestrians in the scene
- Emergency vehicle styling
- Constraint marker support

Primary files:

- `sumo/intersection_1/inter_ped.net.xml`
- `sumo/intersection_1/designed_routes.rou.xml`
- `sumo/intersection_1/inter.sumocfg`
- `sumo/intersection_1/main_intersection_scope.json`
- `tools/export_sumo_visual_network.py`
- `assets/generated/visual_network.json`
- `assets/three-bridge.mjs`

---

## 4. What Is Partially Complete

### 4.1 3D Visual Quality

The 3D scene is connected, but it is still **in a clarity-first procedural state** rather than a final polished city scene.

Current reality:

- Roads and crossings are rendered from SUMO geometry
- Buildings/context props are minimal and procedural
- The renderer is intentionally lightweight
- This is not yet a faithful, production-quality recreation of the surrounding real-world intersection

This is the main reason the simulation may feel "not going well" visually even though the backend connection itself is working.

### 4.2 Visual Alignment and Camera Tuning

Partially complete:

- The scene frames the exported intersection
- Runtime entities appear through the bridge

Still needs work:

- Fine camera angle and framing adjustments
- Better road-width / lane-width visual tuning
- Cleaner context asset placement around the clipped network
- Better visual matching to the intended Tagum road shape

### 4.3 Some Researcher Pages

Status by page:

- `dashboard` - live and actively wired
- `simulation` - live controls wired
- `scenarios` - real CRUD and scenario loading
- `runs-reports` - real data path exists, but still needs fuller runtime persistence and better exports
- `live-traffic` - not fully promoted as the main live page yet
- `performance` - still limited
- `ai-agent` - still mostly placeholder for future RL work

---

## 5. What Is Still Missing

### 5.1 RL Training Pipeline

Not implemented yet:

- Real DQN / Double DQN / PPO-style controller
- Observation space design
- Reward function training loop
- Model checkpoint lifecycle
- Training UI beyond placeholders

The project is currently **fixed-time SUMO control with RL-ready UI direction**, not a finished RL system.

### 5.2 Real Run Persistence Workflow

Still needs completion:

- Clear auto-save behavior when runs stop
- Stronger `simulation_runs` / `run_metrics` population from live sessions
- End-to-end report generation from those stored runs

### 5.3 Final Visual Asset Strategy

Still unresolved:

- Whether the final 3D scene should stay procedural and simple
- Whether custom low-poly assets should be built specifically for SMARTFLOW
- Whether older InfiniTown-derived resources should be reused at all

At the moment, the active bridge is **not** relying on a polished imported InfiniTown scene as the primary renderer.

---

## 6. Tests and Validation

Current targeted coverage includes:

- `tests/test_sumo_simulation_service.py`
  - Verifies the service is SUMO-backed
  - Verifies start/step/stop behavior
  - Verifies pedestrian spawning and dashboard metadata exposure
  - Verifies visual payload structure

- `tests/test_sumo_visual_network_export.py`
  - Verifies exporter output from `inter_ped.net.xml`
  - Verifies clipped intersection scope
  - Verifies crossings, walking areas, and signal IDs

- `tests/test_callbacks_chart_layout.py`
  - Guards the Plotly chart layout compatibility fix

- `tests/test_auth_page_design.py`
  - Verifies the new split auth shell
  - Verifies full-screen auth CSS markers
  - Verifies autofill styling fix
  - Verifies existing callback IDs stayed intact

This is good targeted coverage for the current migration stage, but it is not yet full-system validation.

---

## 7. Active Source of Truth vs Legacy

### Active / Canonical

- SUMO network files in `sumo/intersection_1/`
- `simulation/sumo_engine.py`
- `services/simulation_service.py`
- `callbacks.py`
- `tools/export_sumo_visual_network.py`
- `assets/generated/visual_network.json`
- `assets/three-bridge.mjs`

### Legacy / Reference Only

- Custom Python engine modules under `simulation/engine.py` and related files
- Older assumptions that the custom engine is the main traffic backend
- Older assumptions that a copied InfiniTown scene is the active final visual renderer

---

## 8. Known Issues and Tech Debt

### 8.1 Status Document Drift

This document previously drifted behind the codebase and overstated the old custom-engine path. That is now corrected here, but future updates should treat the SUMO path as canonical unless the architecture changes again.

### 8.2 Mixed Runtime History in `simulation/`

The folder contains both the old custom engine and the new SUMO runtime modules. That is useful for reference, but it also creates confusion about what is actually active.

Recommendation:

- Keep the old modules only if they are explicitly marked legacy, fallback, or experimental

### 8.3 Visual Expectations vs Current Renderer

The current Three.js bridge is technically connected but visually conservative. If the goal is a more presentation-ready scene, the next work should focus on:

- asset strategy
- visual tuning
- road-shape fidelity
- camera composition

not on redoing the dashboard plumbing again

### 8.4 RL Scope Is Still the Main Research Gap

The core capstone/research value of SMARTFLOW still depends on implementing and evaluating the RL controller. Everything around it is now much closer to ready than the RL portion itself.

---

## 9. Recommended Next Phases

### Phase 1: Finalize the Visual Network Path

Do next:

1. Confirm the project scope is **one intersection** first, not a corridor
2. Keep `inter_ped.net.xml` as the canonical network if that remains the chosen scope
3. Continue tuning the exported geometry and Three.js framing against that one network

### Phase 2: Improve Visual Clarity

Recommended:

1. Build simple custom SMARTFLOW assets for buildings, sidewalks, poles, signage, and landmarks
2. Keep the asset set minimal and readable
3. Avoid dropping in a heavy city pack before the road alignment is correct

### Phase 3: Strengthen Runtime Persistence

Recommended:

1. Save completed runs cleanly into the DB
2. Wire stored run metrics into reports/performance views
3. Replace fake or thin report outputs with real exports

### Phase 4: Implement RL for Signal Timing Only

Recommended:

1. Keep SUMO as the traffic source of truth
2. Keep RL focused only on signal timing decisions
3. Define observation, action, and reward based on the SUMO state already exposed to the dashboard

---

## 10. Bottom Line

SMARTFLOW is now best understood as:

> a working Dash + SUMO + TraCI + Three.js traffic simulation platform with strong admin/auth scaffolding, a live dashboard path, and an in-progress visual layer

It is **not** currently:

- a finished RL research platform
- a final polished city visualization
- a custom no-SUMO traffic engine project anymore

The highest-value next work is:

1. finish the visual/network fidelity pass
2. strengthen saved-run/report workflows
3. implement the actual RL controller
