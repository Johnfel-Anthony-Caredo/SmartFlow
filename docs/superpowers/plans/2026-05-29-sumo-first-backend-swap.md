# SUMO-First Backend Swap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the custom SMARTFLOW simulation runtime behind `services/simulation_service.py` with a SUMO + TraCI backend while preserving the existing dashboard callback contract.

**Architecture:** Introduce a focused SUMO runtime adapter plus a state-mapping helper, then swap the service layer to use that adapter as the default engine. Keep `callbacks.py` and the current pages stable by preserving the existing `get_state()` payload shape and fixed-time phase semantics.

**Tech Stack:** Python 3.13, Dash, SUMO, TraCI, SQLite, unittest/pytest-compatible tests

---

### Task 1: Add a Failing Service-Contract Test

**Files:**
- Create: `tests/test_sumo_simulation_service.py`
- Modify: `services/simulation_service.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
import services.simulation_service as sim


class TestSumoSimulationService(unittest.TestCase):
    def tearDown(self):
        try:
            sim.stop()
        except Exception:
            pass
        sim.reset_engine()

    def test_default_runtime_exposes_dashboard_state_contract(self):
        state = sim.get_state()
        self.assertIn("time", state)
        self.assertIn("status", state)
        self.assertIn("phase", state)
        self.assertIn("phase_remaining", state)
        self.assertIn("vehicle_count", state)
        self.assertIn("pedestrian_count", state)
        self.assertIn("metrics", state)
        self.assertIn("events", state)
        self.assertEqual(state["controller_type"], "fixed_time")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sumo_simulation_service.py -q`
Expected: FAIL because the current service is still coupled to the custom engine and does not yet prove the SUMO-backed runtime contract.

- [ ] **Step 3: Write minimal implementation**

```python
# In services/simulation_service.py
# Replace direct SimulationEngine construction with a SUMO-backed runtime factory.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sumo_simulation_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_sumo_simulation_service.py services/simulation_service.py
git commit -m "test: cover SUMO simulation service contract"
```

### Task 2: Implement the SUMO Runtime Adapter

**Files:**
- Create: `simulation/sumo_config.py`
- Create: `simulation/sumo_state.py`
- Create: `simulation/sumo_engine.py`
- Modify: `simulation/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
def test_sumo_runtime_can_step_and_return_state():
    runtime = SumoSimulationEngine()
    runtime.start()
    runtime.step(2)
    state = runtime.to_dict()
    assert state["status"] == "running"
    assert state["time"] >= 0
    assert state["phase"] in {"NS_GREEN", "NS_YELLOW", "ALL_RED", "EW_GREEN", "EW_YELLOW"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sumo_simulation_service.py -q`
Expected: FAIL with missing SUMO runtime implementation

- [ ] **Step 3: Write minimal implementation**

```python
# In simulation/sumo_engine.py
# - resolve the inter.sumocfg path
# - launch SUMO with TraCI
# - maintain status/time/phase/metrics/events
# - expose start/pause/resume/stop/reset/step/configure/configure_from_scenario/to_dict
#
# In simulation/sumo_state.py
# - map raw SUMO values into the existing dashboard state schema
#
# In simulation/sumo_config.py
# - define the config path, step length, phase durations, and TLS IDs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sumo_simulation_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add simulation/sumo_config.py simulation/sumo_state.py simulation/sumo_engine.py simulation/__init__.py tests/test_sumo_simulation_service.py
git commit -m "feat: add SUMO simulation runtime"
```

### Task 3: Swap the Service Layer to SUMO by Default

**Files:**
- Modify: `services/simulation_service.py`
- Modify: `services/scenario_service.py` if signature compatibility adjustments are required

- [ ] **Step 1: Write the failing test**

```python
def test_service_start_step_stop_uses_sumo_runtime():
    sim.reset_engine()
    assert sim.current_status() == "stopped"
    sim.start()
    sim.step(1)
    state = sim.get_state()
    assert state["status"] == "running"
    sim.stop()
    assert sim.current_status() == "stopped"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sumo_simulation_service.py -q`
Expected: FAIL until the service factory and lifecycle wrappers point at the SUMO runtime

- [ ] **Step 3: Write minimal implementation**

```python
# In services/simulation_service.py
# - replace SimulationEngine imports with SumoSimulationEngine
# - preserve the public method names already used by callbacks.py
# - make reset_engine() rebuild the SUMO runtime
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sumo_simulation_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/simulation_service.py services/scenario_service.py tests/test_sumo_simulation_service.py
git commit -m "feat: switch simulation service to SUMO runtime"
```

### Task 4: Verify Scenario and Callback Compatibility

**Files:**
- Modify: `tests/test_simulation_engine.py`
- Modify: `tests/test_sumo_simulation_service.py`
- Modify: `callbacks.py` only if a small compatibility fix is needed

- [ ] **Step 1: Write the failing test**

```python
def test_service_state_matches_callback_expectations():
    sim.reset_engine()
    state = sim.get_state()
    expected_metric_keys = {
        "avg_wait",
        "avg_queue",
        "throughput",
        "step_count",
        "total_vehicles_spawned",
        "total_vehicles_completed",
        "total_pedestrians_spawned",
        "total_pedestrians_completed",
    }
    assert expected_metric_keys.issubset(state["metrics"].keys())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_sumo_simulation_service.py tests/test_simulation_engine.py -q`
Expected: FAIL until the SUMO state mapper fully matches the callback-facing contract

- [ ] **Step 3: Write minimal implementation**

```python
# Ensure the SUMO state mapper returns:
# - top-level status/time/phase fields
# - a metrics payload compatible with callbacks.py
# - safe trimmed vehicle/pedestrian lists
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_sumo_simulation_service.py tests/test_simulation_engine.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_sumo_simulation_service.py tests/test_simulation_engine.py callbacks.py
git commit -m "test: verify callback compatibility for SUMO state"
```

### Task 5: Final Verification

**Files:**
- Modify: `requirements.txt` only if documentation of SUMO Python dependencies is needed

- [ ] **Step 1: Run focused tests**

Run: `python -m pytest tests/test_sumo_simulation_service.py tests/test_simulation_engine.py tests/test_admin_roles_helpers.py -q`
Expected: PASS

- [ ] **Step 2: Run a direct runtime smoke check**

Run: `python -c "import services.simulation_service as sim; sim.reset_engine(); print(sim.get_state()['status'])"`
Expected: `stopped`

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: finalize SUMO backend swap verification"
```
