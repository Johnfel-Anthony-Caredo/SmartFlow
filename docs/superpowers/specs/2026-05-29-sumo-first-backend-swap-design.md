# SUMO-First Backend Swap Design

## Purpose

Move SMARTFLOW from the custom no-SUMO runtime to a SUMO-first simulation backend while preserving the existing Dash application shell, SQLite workflows, authentication system, scenario pages, and current callback contract.

This design covers the first migration slice only:

- SUMO becomes the default simulation source of truth
- fixed-time traffic signal control remains the only active control mode
- the service layer contract stays stable for the dashboard and simulation page
- the custom Python simulation engine remains in the repository only as a temporary fallback/reference and is no longer the main execution path

This slice does not yet cover RL training, live-traffic page rewiring, or full Three.js synchronization.

## Scope

### In scope

- Replace the runtime behind `services/simulation_service.py`
- Launch and control SUMO through TraCI
- Use `sumo/intersection_1/inter.sumocfg` as the initial network/config entry point
- Read live simulation state from SUMO and map it into the existing dashboard-facing state shape
- Keep fixed-time signal control working through a Python-managed control loop
- Preserve existing callback and page integration points where possible
- Add tests for lifecycle, state mapping, and service compatibility

### Out of scope

- RL training or adaptive signal control
- Switching multiple pages to richer SUMO-only metrics beyond the current shared state contract
- Full 3D scene synchronization with exact SUMO geometry/positions
- Scenario-specific route file generation or complex network editing workflows
- Removal of the legacy custom simulation package from the repository

## Current State Summary

The current application already has a clean service boundary:

- `callbacks.py` interacts with `services/simulation_service.py`
- `services/simulation_service.py` currently wraps `simulation.engine.SimulationEngine`
- the dashboard and simulation page consume a stable state payload from `get_state()`
- SUMO files already exist under `sumo/intersection_1`

This means the migration can be handled as a backend layer swap rather than a UI rewrite.

## Chosen Approach

Use a full service-layer swap.

The app will continue calling:

- `start()`
- `pause()`
- `resume()`
- `stop()`
- `reset()`
- `step()`
- `get_state()`
- `configure()`
- `load_scenario()`

Those functions will delegate to a new SUMO-backed runtime adapter instead of the custom simulation engine.

### Why this approach

- It preserves the current app-facing contract
- It minimizes changes in `callbacks.py` and page files
- It makes the migration testable at a single seam
- It keeps RL integration easier later because TraCI ownership remains in the backend layer

### Rejected alternatives

#### Dual-backend runtime switch

Rejected for this slice because it adds branching complexity and increases maintenance cost while the team is trying to make SUMO the main path.

#### Direct callback-to-TraCI wiring

Rejected because it leaks simulation concerns into the UI layer and makes future control and testing harder.

## Target Architecture

### 1. App-facing service layer

`services/simulation_service.py` remains the single public runtime API for the Dash app.

Responsibilities:

- lazily create the active simulation runtime
- expose lifecycle methods used by callbacks
- keep the external interface stable
- fail fast if SUMO configuration cannot start

### 2. SUMO runtime adapter

Add a new runtime class in a file such as `simulation/sumo_engine.py`.

Responsibilities:

- own SUMO process and TraCI connection lifecycle
- launch the configured SUMO scenario
- step the simulation
- manage fixed-time signal updates
- collect runtime metrics
- build dashboard-facing state
- generate event feed entries
- close SUMO/TraCI cleanly on stop/reset/error

This adapter becomes the source of truth for:

- vehicle state
- pedestrian state
- signal phase
- queue length
- waiting time
- throughput
- event/status visibility in the UI

### 3. State-mapping helper

Add a helper module such as `simulation/sumo_state.py`.

Responsibilities:

- convert raw TraCI values into the payload shape already expected by callbacks
- normalize missing or unavailable values
- trim large entity lists for the dashboard/Three.js pipe
- keep serialization logic out of the service file

### 4. SUMO runtime configuration

Add a focused config/helper module such as `simulation/sumo_config.py`, or extend existing constants in a SUMO-specific section.

Responsibilities:

- define the absolute/relative location of `sumo/intersection_1/inter.sumocfg`
- define SUMO step length assumptions
- define fixed-time signal phase timing values used by the Python control loop
- define any lookup constants required for lane grouping, queue aggregation, or entity sampling

## Runtime Flow

### Start flow

1. User starts the simulation from the dashboard or simulation page.
2. `services/simulation_service.start()` requests the active runtime.
3. The SUMO runtime adapter validates the configured SUMO files.
4. The adapter launches SUMO and opens a TraCI connection.
5. The adapter initializes its internal state cache and sets status to `running`.
6. The adapter emits a startup event visible in the existing event feed.

### Step flow

Each `callbacks.py` interval tick continues to call `sim.step(num_ticks=1)`.

For each step, the SUMO adapter should:

1. apply any pending fixed-time signal change if a phase transition is due
2. advance the SUMO simulation by one timestep
3. read traffic light phase and remaining timing state
4. read vehicle and pedestrian IDs from SUMO
5. compute aggregate metrics:
   - active vehicle count
   - active pedestrian count
   - queue counts by approach
   - average waiting time
   - throughput/completed vehicles
6. build trimmed lists of active vehicles and pedestrians for UI consumers
7. append any notable event entries
8. refresh the cached state payload returned by `get_state()`

### Stop/reset flow

When the user stops or resets a run:

- the adapter closes TraCI cleanly if connected
- the adapter marks status as `stopped`
- the adapter resets cached runtime state
- the adapter preserves a readable terminal event for the UI where useful

## Fixed-Time Control Design

The first SUMO slice keeps control logic intentionally narrow.

Rules:

- SMARTFLOW remains fixed-time only in this migration slice
- Python owns the high-level controller timing loop
- TraCI applies signal phase changes into SUMO
- RL is not invoked

The runtime adapter should expose a phase model compatible with current dashboard expectations:

- `NS_GREEN`
- `NS_YELLOW`
- `ALL_RED`
- `EW_GREEN`
- `EW_YELLOW`

It should also continue exposing:

- `phase`
- `phase_remaining`
- `cycle_count`
- `controller_type`

If the underlying SUMO signal IDs or phase strings differ, the adapter must translate them into these canonical SMARTFLOW phase names.

## Dashboard State Contract

The most important compatibility rule is that `get_state()` continues returning the shape expected by `callbacks.py`.

Required top-level fields:

- `time`
- `status`
- `phase`
- `phase_remaining`
- `cycle_count`
- `controller_type`
- `vehicles`
- `vehicle_count`
- `pedestrians`
- `pedestrian_count`
- `metrics`
- `events`
- `scenario`

Required metric fields for this slice:

- `avg_wait`
- `avg_queue`
- `throughput`
- `step_count`
- `total_vehicles_spawned`
- `total_vehicles_completed`
- `total_pedestrians_spawned`
- `total_pedestrians_completed`

Entity serialization should stay lightweight. Vehicle and pedestrian lists should be trimmed to small dashboard-friendly samples rather than dumping the entire SUMO world.

## Scenario Handling

`services/scenario_service.py` and the scenarios database remain in place.

For this first slice, scenario application should continue to work through `simulation_service.configure()` and `load_scenario()` by translating DB-backed scenario options into runtime parameters such as:

- traffic density
- pedestrian density
- emergency mode
- road constraint

Important constraint:

This slice does not require generating new SUMO networks on the fly. Scenario application can begin as runtime parameter overlays and route-demand modifiers against the existing `sumo/intersection_1` assets.

If a scenario field has no valid SUMO implementation yet, it should be preserved in state and surfaced in configuration, but not faked as if it were fully active.

## Error Handling

### Startup failure

If SUMO or TraCI cannot start:

- status must become `stopped`
- the service must not silently fall back to the custom engine
- the state payload must remain valid and safe for callbacks
- an error event must describe the failure clearly

### Mid-run failure

If stepping or state collection fails:

- close TraCI if possible
- stop the runtime cleanly
- preserve the last known good state where practical
- append an error event for the UI

### Missing files or unsupported environment

If `sumo/intersection_1/inter.sumocfg` or related assets are missing, or if the SUMO Python bridge is unavailable:

- fail fast with a clear backend error message
- do not hide the failure by re-routing traffic back into the custom simulation engine

## Testing Strategy

The first migration slice should be tested at the seam where the app depends on the backend.

### Test layer 1: adapter lifecycle

Add focused tests for:

- creating the SUMO runtime
- starting a run
- stepping a run
- pausing/resuming if supported by the adapter design
- stopping/resetting cleanly
- returning a valid empty state before start and after stop

### Test layer 2: state contract

Add tests that assert `get_state()` returns the fields `callbacks.py` currently depends on.

These tests should verify:

- canonical phase naming
- status values
- numeric metric fields
- trimmed entity lists
- safe empty defaults on startup failure or stopped state

### Test layer 3: service compatibility

Update or replace the existing engine-centric tests so they validate the public behavior of `services/simulation_service.py` rather than the removed assumption that the custom `SimulationEngine` is the active runtime.

### Testing boundaries

For this slice, tests do not need to prove RL behavior, advanced disruption realism, or exact 3D synchronization.

## File-Level Change Plan

### New files

- `simulation/sumo_engine.py`
- `simulation/sumo_state.py`
- `simulation/sumo_config.py`
- one or more SUMO-focused tests under `tests/`

### Modified files

- `services/simulation_service.py`
- `simulation/__init__.py`
- `requirements.txt` if the SUMO Python tooling needs to be made explicit for the local environment
- existing tests that currently assume the custom engine is the main path

### Files intentionally left mostly unchanged in this slice

- `callbacks.py`
- page modules under `pages/`
- `services/scenario_service.py`
- `services/metrics_service.py`
- dashboard shell/UI components

## Risks and Mitigations

### Risk: SUMO environment mismatch

The repository contains SUMO network/config assets, but the runtime environment may still be missing the required SUMO Python/TraCI availability.

Mitigation:

- validate dependencies early
- fail with explicit messages
- keep the migration isolated to the service seam for easier debugging

### Risk: UI contract drift

SUMO exposes different raw concepts and names than the custom engine.

Mitigation:

- centralize translation inside the state-mapping helper
- test the contract used by `callbacks.py`

### Risk: scenario expectations exceed first-slice support

Some current scenario settings imply richer traffic behavior than the first SUMO slice can safely implement.

Mitigation:

- support only honest runtime overlays in this slice
- avoid pretending unsupported constraints are fully modeled

## Success Criteria

This design is successful for the first slice when all of the following are true:

- the active runtime behind `services/simulation_service.py` is SUMO-backed by default
- the app no longer depends on the custom simulation engine as the main traffic backend
- the dashboard and simulation page still function through the existing callback contract
- fixed-time control works against the SUMO network
- state and metrics shown in the UI come from SUMO/TraCI instead of the custom physics engine
- failures are explicit and safe rather than masked by fallback behavior

## Deferred Work After This Slice

- wire `pages/live_traffic.py` directly to richer SUMO state
- synchronize `assets/three-bridge.mjs` to consume real SUMO-backed positions consistently
- add RL controller integration focused only on signal timing decisions
- extend scenario execution into stronger disruption modeling and route/network variants
- save completed runs automatically into `simulation_runs` and `run_metrics` if not already completed during the SUMO swap
