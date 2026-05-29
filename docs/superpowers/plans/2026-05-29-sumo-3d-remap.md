# SUMO 3D Remap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the old client-side autonomous traffic scene with a SUMO-driven 3D renderer that uses the existing SMARTFLOW assets and renders live vehicles, pedestrians, emergency vehicles, traffic lights, and road-constraint markers from TraCI state.

**Architecture:** Keep the asset-loading and scene bootstrap responsibilities in `assets/three-bridge.mjs`, but turn the bridge into a pure renderer keyed by SUMO entity IDs. Extend the backend payload to include visual metadata such as `visual_type`, `emergency`, and a simple `visual.constraint_marker`, then remap the static scene to the current SUMO road structure.

**Tech Stack:** Python 3.13, Dash, SUMO, TraCI, Three.js, GLTFLoader, unittest

---

### Task 1: Add Failing Tests for Visual Payload and Bridge Direction

**Files:**
- Modify: `tests/test_sumo_simulation_service.py`
- Modify: `tests/test_three_bridge_scene_style.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_runtime_exposes_visual_payload_for_scene_rendering(self):
    sim.configure(traffic_density="heavy", pedestrian_density="medium", emergency_mode="enabled", road_constraint="Lane Closure")
    sim.start()
    sim.step(10)
    state = sim.get_state()
    self.assertIn("visual", state)
    self.assertIn("constraint_marker", state["visual"])
    if state["vehicles"]:
        self.assertIn("visual_type", state["vehicles"][0])
        self.assertIn("emergency", state["vehicles"][0])
```

```python
def test_three_bridge_uses_sumo_entity_registries(self):
    text = BRIDGE_PATH.read_text(encoding="utf-8")
    self.assertIn("vehicleRegistry", text)
    self.assertIn("pedestrianRegistry", text)
    self.assertIn("constraintMarker", text)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_sumo_simulation_service.TestSumoSimulationService.test_runtime_exposes_visual_payload_for_scene_rendering -v`
Expected: FAIL because the runtime does not yet expose a `visual` section or visual entity metadata.

Run: `python -m unittest tests.test_three_bridge_scene_style.TestThreeBridgeSceneStyle.test_three_bridge_uses_sumo_entity_registries -v`
Expected: FAIL because the current bridge is still built around client-side spawning loops.

- [ ] **Step 3: Write minimal implementation**

```python
# Extend the SUMO state payload and replace the bridge’s client-side
# traffic simulation with SUMO-driven registries.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS

Run: `python -m unittest tests.test_three_bridge_scene_style -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_sumo_simulation_service.py tests/test_three_bridge_scene_style.py
git commit -m "test: cover SUMO 3D visual payload"
```

### Task 2: Extend Backend State for 3D Rendering

**Files:**
- Modify: `simulation/sumo_state.py`
- Modify: `simulation/sumo_engine.py`

- [ ] **Step 1: Write the failing test**

```python
def test_runtime_marks_emergency_and_constraint_visuals(self):
    sim.configure(emergency_mode="enabled", road_constraint="Lane Closure")
    sim.start()
    sim.step(12)
    state = sim.get_state()
    self.assertTrue(state["visual"]["constraint_marker"]["active"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: FAIL until the runtime adds explicit visual metadata and road-constraint placement.

- [ ] **Step 3: Write minimal implementation**

```python
# In simulation/sumo_engine.py
# - maintain emergency vehicle ids while emergency_mode is enabled
# - include visual_type/emergency per vehicle
# - include a top-level visual.constraint_marker payload
#
# In simulation/sumo_state.py
# - serialize the new visual payload
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add simulation/sumo_state.py simulation/sumo_engine.py tests/test_sumo_simulation_service.py
git commit -m "feat: add SUMO visual payload for 3D scene"
```

### Task 3: Replace the Three.js Traffic Logic with a SUMO Renderer

**Files:**
- Modify: `assets/three-bridge.mjs`

- [ ] **Step 1: Write the failing test**

```python
def test_three_bridge_keeps_required_markers_and_uses_sumo_render_path(self):
    text = BRIDGE_PATH.read_text(encoding="utf-8")
    self.assertIn("traffic_light.gltf", text)
    self.assertIn("GLTFLoader", text)
    self.assertIn("syncVehiclesFromState", text)
    self.assertIn("syncPedestriansFromState", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_three_bridge_scene_style -v`
Expected: FAIL until the bridge contains the SUMO-driven renderer path.

- [ ] **Step 3: Write minimal implementation**

```javascript
// In assets/three-bridge.mjs
// - keep scene init, camera, lights, and asset loading
// - build a static road scene aligned to the current SUMO intersection
// - maintain vehicleRegistry and pedestrianRegistry keyed by SUMO ids
// - upsert/remove meshes directly from window.__smartflowState
// - render traffic lights from ns_state/ew_state
// - render a red X road constraint marker from visual.constraint_marker
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_three_bridge_scene_style -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add assets/three-bridge.mjs tests/test_three_bridge_scene_style.py
git commit -m "feat: remap 3D scene to SUMO state"
```

### Task 4: Final Verification

**Files:**
- Modify: `callbacks.py` only if the scene payload needs a small JSON extension

- [ ] **Step 1: Run focused tests**

Run: `python -m unittest tests.test_sumo_simulation_service -v`
Expected: PASS

Run: `python -m unittest tests.test_three_bridge_scene_style -v`
Expected: PASS

- [ ] **Step 2: Run JS syntax check**

Run: `node --check assets/three-bridge.mjs`
Expected: no syntax errors

- [ ] **Step 3: Run runtime smoke check**

Run: `python -c "import services.simulation_service as sim; sim.reset_engine(); sim.configure(traffic_density='heavy', pedestrian_density='medium', emergency_mode='enabled', road_constraint='Lane Closure'); sim.start(); sim.step(10); s=sim.get_state(); print(bool(s['visual']['constraint_marker']['active']), len(s['vehicles']), len(s['pedestrians']))"`
Expected: `True` plus non-negative counts

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "chore: verify SUMO 3D remap"
```
