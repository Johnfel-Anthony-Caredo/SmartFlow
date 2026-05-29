# SUMO Dashboard Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish wiring the dashboard and simulation page to live SUMO/TraCI state without changing the existing page structure or replacing the current dashboard shell.

**Architecture:** Extend the SUMO runtime state so it exposes lightweight dashboard-ready metadata and chart histories, then complete the callback layer so all existing widget IDs read live values instead of static layout defaults. Keep `services/simulation_service.py` as the only backend seam and leave the Three.js road-geometry rebuild for a later phase.

**Tech Stack:** Python 3.13, Dash, Plotly, SUMO, TraCI, unittest

---

### Task 1: Add Failing Tests for Dashboard-Facing SUMO State

**Files:**
- Modify: `tests/test_sumo_simulation_service.py`

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_exposes_dashboard_metadata_and_histories(self):
    sim.configure(traffic_density="heavy", pedestrian_density="medium", emergency_mode="enabled")
    sim.start()
    sim.step(6)
    state = sim.get_state()
    self.assertIn("dashboard", state)
    self.assertIn("charts", state)
    self.assertIn("current_scenario_name", state["dashboard"])
    self.assertIn("control_mode_label", state["dashboard"])
    self.assertIn("emergency_active_count", state["dashboard"])
    self.assertGreater(len(state["charts"]["traffic_flow"]), 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_sumo_simulation_service.TestSumoSimulationService.test_runtime_exposes_dashboard_metadata_and_histories -v`
Expected: FAIL because the current SUMO state payload does not yet expose dashboard metadata or chart series.

- [ ] **Step 3: Write minimal implementation**

```python
# Extend simulation/sumo_engine.py and simulation/sumo_state.py
# to include dashboard metadata and short rolling chart histories.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_sumo_simulation_service.TestSumoSimulationService.test_runtime_exposes_dashboard_metadata_and_histories -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_sumo_simulation_service.py simulation/sumo_engine.py simulation/sumo_state.py
git commit -m "test: cover dashboard-facing SUMO state"
```

### Task 2: Extend SUMO Runtime State for the Dashboard

**Files:**
- Modify: `simulation/sumo_config.py`
- Modify: `simulation/sumo_engine.py`
- Modify: `simulation/sumo_state.py`

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_tracks_chart_series_and_simulation_page_fields(self):
    sim.start()
    sim.step(8)
    state = sim.get_state()
    self.assertIn("wait_time", state["charts"])
    self.assertIn("queue_length", state["charts"])
    self.assertIn("throughput", state["charts"])
    self.assertIn("last_action", state["dashboard"])
    self.assertIn("run_id", state["dashboard"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: FAIL until the SUMO runtime maintains the extra dashboard metadata and rolling history buffers.

- [ ] **Step 3: Write minimal implementation**

```python
# In simulation/sumo_engine.py
# - add a generated run_id per start/reset cycle
# - track current scenario name and control mode label
# - count active emergency vehicles from live sampled vehicles
# - maintain short rolling series for traffic flow, wait time, queue length, throughput
# - track last_action and last_error in dashboard metadata
#
# In simulation/sumo_state.py
# - serialize the new dashboard and charts sections into get_state()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add simulation/sumo_config.py simulation/sumo_engine.py simulation/sumo_state.py tests/test_sumo_simulation_service.py
git commit -m "feat: add dashboard-ready SUMO state"
```

### Task 3: Complete Dashboard and Simulation Page Callbacks

**Files:**
- Modify: `callbacks.py`
- Modify: `pages/simulation.py`

- [ ] **Step 1: Write the failing test**

```python
def test_service_state_contains_values_needed_by_callbacks(self):
    sim.start()
    sim.step(4)
    state = sim.get_state()
    required = {
        "dashboard",
        "charts",
        "metrics",
        "events",
        "vehicles",
        "pedestrians",
    }
    self.assertTrue(required.issubset(state.keys()))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS on state only after Task 2, while the UI still shows static chart figures and some simulation-page fields remain unwired.

- [ ] **Step 3: Write minimal implementation**

```python
# In callbacks.py
# - extend dashboard callback outputs to include emergency KPI
# - add live figure callbacks for traffic-flow-chart and wait-time-chart
# - populate sim-active-scenario, sim-control-mode, sim-last-action, sim-last-error, sim-run-id
#
# In pages/simulation.py
# - add id='apply-btn' to the existing Apply button so the current callback can fire
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS for backend state; callback import may still be environment-limited if Dash is unavailable.

- [ ] **Step 5: Commit**

```bash
git add callbacks.py pages/simulation.py tests/test_sumo_simulation_service.py
git commit -m "feat: wire dashboard callbacks to SUMO state"
```

### Task 4: Final Verification

**Files:**
- Modify: none unless a compatibility fix is needed

- [ ] **Step 1: Run focused tests**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS

- [ ] **Step 2: Run existing SUMO/runtime regression check**

Run: `python -m unittest tests.test_simulation_engine -v`
Expected: PASS

- [ ] **Step 3: Run a direct smoke check**

Run: `python -c "import services.simulation_service as sim; sim.reset_engine(); sim.start(); sim.step(8); s=sim.get_state(); print(s['dashboard']['current_scenario_name'], len(s['charts']['traffic_flow']))"`
Expected: a scenario label and a non-zero chart-series length

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "chore: verify SUMO dashboard wiring"
```
