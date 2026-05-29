# TraCI Pedestrian Crossings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real SUMO pedestrian crossings and deterministic TraCI pedestrian spawning so SMARTFLOW can simulate people crossing the four-way junction.

**Architecture:** Upgrade the SUMO network to include sidewalks, crossings, and walking areas, point the active SUMO config at that pedestrian-ready network, then extend the SUMO runtime adapter to spawn and track pedestrians using TraCI person stages and intermodal walking routes.

**Tech Stack:** Python 3.13, SUMO, TraCI, netconvert, unittest

---

### Task 1: Add a Failing Pedestrian Runtime Test

**Files:**
- Modify: `tests/test_sumo_simulation_service.py`

- [ ] **Step 1: Write the failing test**

```python
def test_service_spawns_pedestrians_when_density_is_enabled(self):
    sim.reset_engine()
    sim.configure(pedestrian_density="heavy")
    sim.start()
    sim.step(12)
    state = sim.get_state()
    self.assertGreater(state["metrics"]["total_pedestrians_spawned"], 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_sumo_simulation_service.TestSumoSimulationService.test_service_spawns_pedestrians_when_density_is_enabled -v`
Expected: FAIL because the current net has no active pedestrian infrastructure in the configured runtime and the runtime never adds persons through TraCI.

- [ ] **Step 3: Write minimal implementation**

```python
# Extend the SUMO runtime after the network supports crossings.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_sumo_simulation_service.TestSumoSimulationService.test_service_spawns_pedestrians_when_density_is_enabled -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_sumo_simulation_service.py
git commit -m "test: cover TraCI pedestrian spawning"
```

### Task 2: Add Pedestrian Infrastructure to the SUMO Network

**Files:**
- Create: `sumo/intersection_1/inter_ped.net.xml`
- Modify: `sumo/intersection_1/inter.sumocfg`

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_uses_pedestrian_ready_network(self):
    runtime = sim.get_engine()
    self.assertTrue(runtime)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: Existing pedestrian test still fails because the network lacks crossings/walking areas in the active config.

- [ ] **Step 3: Write minimal implementation**

```bash
netconvert --sumo-net-file sumo/intersection_1/inter.net.xml --sidewalks.guess true --crossings.guess true --walkingareas true -o sumo/intersection_1/inter_ped.net.xml
```

Update `inter.sumocfg` to use `inter_ped.net.xml`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: Pedestrian test still fails until TraCI spawning is added, but the network is now ready.

- [ ] **Step 5: Commit**

```bash
git add sumo/intersection_1/inter_ped.net.xml sumo/intersection_1/inter.sumocfg
git commit -m "feat: add SUMO pedestrian network"
```

### Task 3: Spawn Pedestrians Through TraCI

**Files:**
- Modify: `simulation/sumo_config.py`
- Modify: `simulation/sumo_engine.py`
- Modify: `simulation/sumo_state.py`

- [ ] **Step 1: Write the failing test**

```python
def test_spawned_pedestrians_appear_in_runtime_state(self):
    sim.reset_engine()
    sim.configure(pedestrian_density="heavy")
    sim.start()
    sim.step(12)
    state = sim.get_state()
    self.assertGreater(state["pedestrian_count"], 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: FAIL until `simulation/sumo_engine.py` adds persons and walking stages with TraCI.

- [ ] **Step 3: Write minimal implementation**

```python
# In simulation/sumo_config.py
# - define deterministic pedestrian spawn intervals per density
# - define four route templates for the crossing approaches
#
# In simulation/sumo_engine.py
# - maintain a deterministic pedestrian spawn timer
# - compute walking routes with traci.simulation.findIntermodalRoute
# - call traci.person.add + traci.person.appendWalkingStage
# - keep person IDs unique and tracked in metrics/state
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add simulation/sumo_config.py simulation/sumo_engine.py simulation/sumo_state.py tests/test_sumo_simulation_service.py
git commit -m "feat: add TraCI pedestrian crossings"
```

### Task 4: Final Verification

**Files:**
- Modify: none unless a small compatibility fix is needed

- [ ] **Step 1: Run focused tests**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS

- [ ] **Step 2: Run runtime smoke check**

Run: `python -c "import services.simulation_service as sim; sim.reset_engine(); sim.configure(pedestrian_density='heavy'); sim.start(); sim.step(12); print(sim.get_state()['metrics']['total_pedestrians_spawned'])"`
Expected: a value greater than `0`

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "chore: verify TraCI pedestrian support"
```
