# SUMO Geometry First Visual Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hand-tuned Three.js road drawing with a SUMO-geometry-driven visual system and custom simple procedural assets optimized for readability.

**Architecture:** SUMO owns the network, routes, traffic lights, vehicles, pedestrians, and constraints. Python exports scoped SUMO geometry into a browser-friendly JSON file, and Three.js renders that geometry plus live TraCI entity state using simple generated meshes instead of mixed external model packs.

**Tech Stack:** Python 3.13, SUMO 1.26, TraCI, Dash, Three.js, unittest, XML/JSON standard libraries

---

## File Structure

**Create:**
- `sumo/intersection_1/main_intersection_scope.json`
- `sumo/intersection_1/designed_routes.rou.xml`
- `tools/export_sumo_visual_network.py`
- `assets/generated/visual_network.json`
- `tests/test_sumo_network_scope.py`
- `tests/test_sumo_visual_network_export.py`

**Modify:**
- `sumo/intersection_1/inter.sumocfg`
- `simulation/sumo_config.py`
- `assets/three-bridge.mjs`
- `tests/test_three_bridge_scene_style.py`
- `tests/test_sumo_simulation_service.py`

**Do not modify for this phase unless tests reveal a direct contract mismatch:**
- Authentication, SQLite schema, Dash page layout, reports, role/access modules
- RL policy internals

## Architecture Decisions

- Use a **single main intersection scope** for the capstone demo, not a corridor. The current network contains far traffic-light junctions, but the research objective is one selected high-volume intersection with adjacent road segments.
- Keep `inter_ped.net.xml` as the active network because it already contains pedestrian crossings and walking areas.
- Replace `inter.rou.xml` random-trip demand with `designed_routes.rou.xml` flow demand so scenarios are explainable and repeatable.
- Export `assets/generated/visual_network.json` from SUMO XML so Three.js draws roads, crossings, walking areas, junctions, and signal positions from the same geometry SUMO uses.
- Build vehicles, pedestrians, signals, and road constraints as procedural Three.js meshes first. Imported GLTF assets may be reintroduced only after the generated geometry path is stable.

---

### Task 1: Lock the Main Intersection Scope

**Files:**
- Create: `sumo/intersection_1/main_intersection_scope.json`
- Create: `tests/test_sumo_network_scope.py`

- [ ] **Step 1: Write the failing scope test**

```python
import json
import unittest
from pathlib import Path


SCOPE_PATH = Path("sumo/intersection_1/main_intersection_scope.json")


class TestSumoNetworkScope(unittest.TestCase):
    def test_scope_selects_one_main_intersection(self):
        scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(scope["mode"], "single_intersection")
        self.assertEqual(
            scope["controlled_tls_ids"],
            ["7900968103", "7900968104", "7900968105", "7900968106"],
        )
        self.assertIn("1337657045#0", scope["route_edges"])
        self.assertIn("-1337657045#3", scope["route_edges"])
        self.assertNotIn("1337657045#5", scope["route_edges"])
        self.assertNotIn("-1337657045#5", scope["route_edges"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_sumo_network_scope -v`

Expected: FAIL because `main_intersection_scope.json` does not exist.

- [ ] **Step 3: Add the scope file**

Create `sumo/intersection_1/main_intersection_scope.json`:

```json
{
  "mode": "single_intersection",
  "description": "Main Tagum City intersection only, with short adjacent approach roads for queue formation.",
  "net_file": "inter_ped.net.xml",
  "route_file": "designed_routes.rou.xml",
  "controlled_tls_ids": ["7900968103", "7900968104", "7900968105", "7900968106"],
  "route_edges": [
    "1337657045#0",
    "1337657045#1",
    "1337657045#2",
    "1337657045#3",
    "-1337657045#3",
    "-1337657045#2",
    "-1337657045#1",
    "-1337657045#0",
    "180969633#0",
    "180969633#1",
    "-180969633#1",
    "-180969633#0",
    "180970197#0",
    "180970197#1",
    "-180970197#1",
    "-180970197#0"
  ],
  "approaches": {
    "west": { "entry_edge": "1337657045#0", "exit_edge": "-1337657045#0" },
    "east": { "entry_edge": "-1337657045#3", "exit_edge": "1337657045#3" },
    "north": { "entry_edge": "180969633#0", "exit_edge": "-180969633#0" },
    "south": { "entry_edge": "-180970197#1", "exit_edge": "180970197#1" }
  }
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_sumo_network_scope -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sumo/intersection_1/main_intersection_scope.json tests/test_sumo_network_scope.py
git commit -m "docs: define main SUMO intersection scope"
```

---

### Task 2: Replace Random Trips with Designed SUMO Flows

**Files:**
- Create: `sumo/intersection_1/designed_routes.rou.xml`
- Modify: `sumo/intersection_1/inter.sumocfg`
- Modify: `tests/test_sumo_network_scope.py`

- [ ] **Step 1: Add the failing route test**

Append this test to `tests/test_sumo_network_scope.py`:

```python
import xml.etree.ElementTree as ET


ROUTES_PATH = Path("sumo/intersection_1/designed_routes.rou.xml")
CONFIG_PATH = Path("sumo/intersection_1/inter.sumocfg")


class TestDesignedRoutes(unittest.TestCase):
    def test_designed_routes_use_named_flows_instead_of_random_vehicle_list(self):
        root = ET.parse(ROUTES_PATH).getroot()
        route_ids = {route.get("id") for route in root.findall("route")}
        flow_ids = {flow.get("id") for flow in root.findall("flow")}
        vehicles = root.findall("vehicle")

        self.assertIn("west_to_east", route_ids)
        self.assertIn("east_to_west", route_ids)
        self.assertIn("north_to_south", route_ids)
        self.assertIn("south_to_north", route_ids)
        self.assertIn("emergency_west_to_east", route_ids)
        self.assertIn("flow_west_to_east", flow_ids)
        self.assertEqual(len(vehicles), 0)

    def test_sumo_config_uses_designed_routes(self):
        text = CONFIG_PATH.read_text(encoding="utf-8")
        self.assertIn('<route-files value="designed_routes.rou.xml"/>', text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_sumo_network_scope -v`

Expected: FAIL because `designed_routes.rou.xml` does not exist and `inter.sumocfg` still references `inter.rou.xml`.

- [ ] **Step 3: Create designed routes**

Create `sumo/intersection_1/designed_routes.rou.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<routes>
    <vType id="car" vClass="passenger" accel="2.6" decel="4.5" sigma="0.5" length="4.5" minGap="2.5" maxSpeed="13.89"/>
    <vType id="bus" vClass="bus" accel="1.2" decel="3.5" sigma="0.45" length="11.0" minGap="3.0" maxSpeed="11.11"/>
    <vType id="truck" vClass="truck" accel="1.1" decel="3.0" sigma="0.45" length="8.5" minGap="3.0" maxSpeed="10.0"/>
    <vType id="emergency" vClass="emergency" accel="3.0" decel="5.0" sigma="0.2" length="5.5" minGap="2.0" maxSpeed="16.67" color="1,0,0"/>

    <route id="west_to_east" edges="1337657045#0 1337657045#1 1337657045#2 1337657045#3"/>
    <route id="east_to_west" edges="-1337657045#3 -1337657045#2 -1337657045#1 -1337657045#0"/>
    <route id="north_to_south" edges="180969633#0 180969633#1 180970197#0 180970197#1"/>
    <route id="south_to_north" edges="-180970197#1 -180970197#0 -180969633#1 -180969633#0"/>
    <route id="west_to_south" edges="1337657045#0 1337657045#1 180970197#0 180970197#1"/>
    <route id="south_to_east" edges="-180970197#1 -180970197#0 1337657045#2 1337657045#3"/>
    <route id="emergency_west_to_east" edges="1337657045#0 1337657045#1 1337657045#2 1337657045#3"/>

    <flow id="flow_west_to_east" type="car" route="west_to_east" begin="0" end="10000" vehsPerHour="420" departLane="best"/>
    <flow id="flow_east_to_west" type="car" route="east_to_west" begin="0" end="10000" vehsPerHour="390" departLane="best"/>
    <flow id="flow_north_to_south" type="car" route="north_to_south" begin="0" end="10000" vehsPerHour="180" departLane="best"/>
    <flow id="flow_south_to_north" type="car" route="south_to_north" begin="0" end="10000" vehsPerHour="180" departLane="best"/>
    <flow id="flow_west_to_south" type="car" route="west_to_south" begin="0" end="10000" vehsPerHour="80" departLane="best"/>
    <flow id="flow_south_to_east" type="car" route="south_to_east" begin="0" end="10000" vehsPerHour="80" departLane="best"/>
    <flow id="flow_bus_east_to_west" type="bus" route="east_to_west" begin="0" end="10000" vehsPerHour="36" departLane="best"/>
    <flow id="flow_truck_west_to_east" type="truck" route="west_to_east" begin="0" end="10000" vehsPerHour="30" departLane="best"/>
</routes>
```

- [ ] **Step 4: Point SUMO config at designed routes**

Change `sumo/intersection_1/inter.sumocfg` route input to:

```xml
<route-files value="designed_routes.rou.xml"/>
```

- [ ] **Step 5: Run the route tests**

Run: `python -m unittest tests.test_sumo_network_scope -v`

Expected: PASS.

- [ ] **Step 6: Run SUMO startup smoke test**

Run: `python -m unittest tests.test_sumo_simulation_service.TestSumoSimulationService.test_service_can_start_step_and_stop_a_sumo_run -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add sumo/intersection_1/designed_routes.rou.xml sumo/intersection_1/inter.sumocfg tests/test_sumo_network_scope.py
git commit -m "feat: use designed SUMO route flows"
```

---

### Task 3: Export SUMO Geometry to Browser JSON

**Files:**
- Create: `tools/export_sumo_visual_network.py`
- Create: `assets/generated/visual_network.json`
- Create: `tests/test_sumo_visual_network_export.py`

- [ ] **Step 1: Write the failing exporter test**

```python
import json
import subprocess
import sys
import unittest
from pathlib import Path


VISUAL_NETWORK_PATH = Path("assets/generated/visual_network.json")
EXPORTER_PATH = Path("tools/export_sumo_visual_network.py")


class TestSumoVisualNetworkExport(unittest.TestCase):
    def test_exporter_generates_visual_network_json(self):
        subprocess.run(
            [sys.executable, str(EXPORTER_PATH)],
            check=True,
            cwd=Path.cwd(),
        )
        data = json.loads(VISUAL_NETWORK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["scope"], "single_intersection")
        self.assertGreaterEqual(len(data["roads"]), 4)
        self.assertGreaterEqual(len(data["crossings"]), 4)
        self.assertGreaterEqual(len(data["signals"]), 4)
        self.assertIn("bounds", data)

    def test_visual_network_contains_no_far_corridor_edges(self):
        data = json.loads(VISUAL_NETWORK_PATH.read_text(encoding="utf-8"))
        edge_ids = {road["edge_id"] for road in data["roads"]}
        self.assertNotIn("1337657045#5", edge_ids)
        self.assertNotIn("-1337657045#5", edge_ids)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_sumo_visual_network_export -v`

Expected: FAIL because `tools/export_sumo_visual_network.py` does not exist.

- [ ] **Step 3: Implement the exporter**

Create `tools/export_sumo_visual_network.py`:

```python
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMO_DIR = ROOT / "sumo" / "intersection_1"
SCOPE_PATH = SUMO_DIR / "main_intersection_scope.json"
NET_PATH = SUMO_DIR / "inter_ped.net.xml"
OUTPUT_PATH = ROOT / "assets" / "generated" / "visual_network.json"


def parse_points(shape):
    return [
        [round(float(x), 2), round(float(y), 2)]
        for x, y in (point.split(",") for point in shape.split())
    ]


def collect_bounds(items):
    xs = []
    ys = []
    for item in items:
        for x, y in item["shape"]:
            xs.append(x)
            ys.append(y)
    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
    }


def main():
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    route_edges = set(scope["route_edges"])
    controlled_tls_ids = set(scope["controlled_tls_ids"])
    net = ET.parse(NET_PATH).getroot()

    roads = []
    crossings = []
    walking_areas = []
    signals = []

    for edge in net.findall("edge"):
        edge_id = edge.get("id")
        function = edge.get("function")
        if function == "crossing":
            for lane in edge.findall("lane"):
                crossings.append({
                    "id": lane.get("id"),
                    "shape": parse_points(lane.get("shape")),
                    "width": float(lane.get("width", "4.0")),
                })
        elif function == "walkingarea":
            for lane in edge.findall("lane"):
                walking_areas.append({
                    "id": lane.get("id"),
                    "shape": parse_points(lane.get("shape")),
                    "width": float(lane.get("width", "2.0")),
                })
        elif edge_id in route_edges:
            lanes = []
            for lane in edge.findall("lane"):
                shape = lane.get("shape")
                if shape:
                    lanes.append({
                        "id": lane.get("id"),
                        "shape": parse_points(shape),
                        "width": float(lane.get("width", "3.2")),
                        "allow": lane.get("allow", ""),
                        "disallow": lane.get("disallow", ""),
                    })
            if lanes:
                roads.append({"edge_id": edge_id, "lanes": lanes, "shape": lanes[0]["shape"]})

    for junction in net.findall("junction"):
        junction_id = junction.get("id")
        if junction_id in controlled_tls_ids:
            signals.append({
                "id": junction_id,
                "x": round(float(junction.get("x")), 2),
                "y": round(float(junction.get("y")), 2),
                "shape": parse_points(junction.get("shape")),
            })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "scope": scope["mode"],
        "source_net": scope["net_file"],
        "bounds": collect_bounds(roads),
        "roads": roads,
        "crossings": crossings,
        "walking_areas": walking_areas,
        "signals": signals,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the exporter test**

Run: `python -m unittest tests.test_sumo_visual_network_export -v`

Expected: PASS and `assets/generated/visual_network.json` exists.

- [ ] **Step 5: Commit**

```bash
git add tools/export_sumo_visual_network.py assets/generated/visual_network.json tests/test_sumo_visual_network_export.py
git commit -m "feat: export SUMO visual network geometry"
```

---

### Task 4: Replace Imported Dynamic Assets with Procedural Meshes

**Files:**
- Modify: `assets/three-bridge.mjs`
- Modify: `tests/test_three_bridge_scene_style.py`

- [ ] **Step 1: Write the failing procedural asset test**

Add this test to `tests/test_three_bridge_scene_style.py`:

```python
def test_three_bridge_uses_procedural_clarity_assets(self):
    text = BRIDGE_PATH.read_text(encoding="utf-8")
    self.assertIn("function createVehicleMesh", text)
    self.assertIn("function createPedestrianMesh", text)
    self.assertIn("function createTrafficSignalMesh", text)
    self.assertIn("function createConstraintMesh", text)
    self.assertNotIn("VEHICLE_MODEL_URLS", text)
    self.assertNotIn("PEDESTRIAN_MODEL_URL", text)
    self.assertNotIn("TRAFFIC_LIGHT_MODEL_URL", text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_three_bridge_scene_style.TestThreeBridgeSceneStyle.test_three_bridge_uses_procedural_clarity_assets -v`

Expected: FAIL because the bridge still references imported vehicle, pedestrian, and traffic light GLTF models.

- [ ] **Step 3: Replace dynamic GLTF usage with procedural factories**

In `assets/three-bridge.mjs`, replace imported dynamic asset constants and loaders with:

```javascript
const VEHICLE_STYLE = Object.freeze({
  car: { width: 1.2, height: 0.55, length: 2.3, color: 0x3b82f6 },
  suv: { width: 1.3, height: 0.65, length: 2.6, color: 0x86efac },
  taxi: { width: 1.2, height: 0.55, length: 2.3, color: 0xfacc15 },
  pickup: { width: 1.35, height: 0.65, length: 2.8, color: 0xf97316 },
  truck: { width: 1.55, height: 0.95, length: 4.0, color: 0x64748b },
  bus: { width: 1.7, height: 1.0, length: 4.8, color: 0x38bdf8 },
  ambulance: { width: 1.35, height: 0.8, length: 3.0, color: 0xffffff },
});

function createVehicleMesh(type, emergency = false) {
  const T = window.THREE;
  const style = VEHICLE_STYLE[type] || VEHICLE_STYLE.car;
  const group = new T.Group();
  const body = new T.Mesh(
    new T.BoxGeometry(style.width, style.height, style.length),
    new T.MeshStandardMaterial({ color: emergency ? 0xffffff : style.color, roughness: 0.42 }),
  );
  body.position.y = style.height / 2;
  group.add(body);

  const cabin = new T.Mesh(
    new T.BoxGeometry(style.width * 0.72, style.height * 0.55, style.length * 0.42),
    new T.MeshStandardMaterial({ color: 0xdbeafe, roughness: 0.25 }),
  );
  cabin.position.set(0, style.height + 0.16, -style.length * 0.08);
  group.add(cabin);

  if (emergency) {
    const stripe = new T.Mesh(
      new T.BoxGeometry(style.width * 1.02, 0.04, style.length * 0.18),
      new T.MeshStandardMaterial({ color: 0xef4444, emissive: 0x330000 }),
    );
    stripe.position.set(0, style.height + 0.44, 0);
    group.add(stripe);
  }
  return group;
}
```

Also add `createPedestrianMesh`, `createTrafficSignalMesh`, and `createConstraintMesh` using only `BoxGeometry`, `SphereGeometry`, and `CylinderGeometry`.

- [ ] **Step 4: Run the procedural asset test**

Run: `python -m unittest tests.test_three_bridge_scene_style -v`

Expected: PASS.

- [ ] **Step 5: Run JS syntax check**

Run: `node --check assets/three-bridge.mjs`

Expected: no syntax errors.

- [ ] **Step 6: Commit**

```bash
git add assets/three-bridge.mjs tests/test_three_bridge_scene_style.py
git commit -m "feat: use procedural clarity assets"
```

---

### Task 5: Render Roads from `visual_network.json`

**Files:**
- Modify: `assets/three-bridge.mjs`
- Modify: `tests/test_three_bridge_scene_style.py`

- [ ] **Step 1: Write the failing geometry-rendering test**

Add this test to `tests/test_three_bridge_scene_style.py`:

```python
def test_three_bridge_loads_exported_sumo_visual_network(self):
    text = BRIDGE_PATH.read_text(encoding="utf-8")
    self.assertIn("VISUAL_NETWORK_URL = '/assets/generated/visual_network.json'", text)
    self.assertIn("loadVisualNetwork", text)
    self.assertIn("buildRoadsFromNetwork", text)
    self.assertIn("buildCrossingsFromNetwork", text)
    self.assertNotIn("const ROAD_PATHS", text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_three_bridge_scene_style.TestThreeBridgeSceneStyle.test_three_bridge_loads_exported_sumo_visual_network -v`

Expected: FAIL because roads are still hard-coded in `three-bridge.mjs`.

- [ ] **Step 3: Add visual network loading**

In `assets/three-bridge.mjs`, add:

```javascript
const VISUAL_NETWORK_URL = '/assets/generated/visual_network.json';
let visualNetwork = null;

async function loadVisualNetwork() {
  if (visualNetwork) return visualNetwork;
  const response = await fetch(VISUAL_NETWORK_URL, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Failed to load visual network: ${response.status}`);
  }
  visualNetwork = await response.json();
  return visualNetwork;
}
```

Call `loadVisualNetwork()` during init before static geometry is built. If loading fails, show a console warning and build a small fallback cross so the canvas is not blank.

- [ ] **Step 4: Build roads and crossings from JSON**

Replace hard-coded road constants with:

```javascript
function buildRoadsFromNetwork(network) {
  for (const road of network.roads || []) {
    for (const lane of road.lanes || []) {
      staticRoot.add(createPolylineRoad(lane.shape, Math.max(lane.width || 3.2, 2.4)));
    }
  }
}

function buildCrossingsFromNetwork(network) {
  for (const crossing of network.crossings || []) {
    staticRoot.add(createCrosswalkFromShape(crossing.shape, crossing.width || 4.0));
  }
}
```

- [ ] **Step 5: Run tests and syntax check**

Run: `python -m unittest tests.test_three_bridge_scene_style -v`

Expected: PASS.

Run: `node --check assets/three-bridge.mjs`

Expected: no syntax errors.

- [ ] **Step 6: Commit**

```bash
git add assets/three-bridge.mjs tests/test_three_bridge_scene_style.py
git commit -m "feat: render Three.js roads from SUMO geometry"
```

---

### Task 6: Align Live Entities and Signals to Exported Geometry

**Files:**
- Modify: `assets/three-bridge.mjs`
- Modify: `simulation/sumo_config.py`
- Modify: `tests/test_sumo_simulation_service.py`
- Modify: `tests/test_three_bridge_scene_style.py`

- [ ] **Step 1: Add failing tests for scoped signals and visible entity contract**

Add to `tests/test_sumo_simulation_service.py`:

```python
def test_sumo_controller_uses_main_intersection_tls_only(self):
    from simulation.sumo_config import MAJOR_TLS_IDS, MINOR_TLS_IDS
    all_tls = set(MAJOR_TLS_IDS) | set(MINOR_TLS_IDS)
    self.assertEqual(all_tls, {"7900968103", "7900968104", "7900968105", "7900968106"})
```

Add to `tests/test_three_bridge_scene_style.py`:

```python
def test_three_bridge_syncs_signals_from_exported_network(self):
    text = BRIDGE_PATH.read_text(encoding="utf-8")
    self.assertIn("signalRegistry", text)
    self.assertIn("syncSignalsFromState", text)
    self.assertIn("network.signals", text)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_sumo_simulation_service.TestSumoSimulationService.test_sumo_controller_uses_main_intersection_tls_only -v`

Expected: FAIL while far traffic-light IDs remain in controller constants.

Run: `python -m unittest tests.test_three_bridge_scene_style.TestThreeBridgeSceneStyle.test_three_bridge_syncs_signals_from_exported_network -v`

Expected: FAIL until the bridge creates signal meshes from `visual_network.json`.

- [ ] **Step 3: Scope SUMO TLS constants**

In `simulation/sumo_config.py`, set:

```python
MAJOR_TLS_IDS = (
    "7900968103",
    "7900968104",
)

MINOR_TLS_IDS = (
    "7900968105",
    "7900968106",
)
```

- [ ] **Step 4: Build signal meshes from exported network**

In `assets/three-bridge.mjs`, create `signalRegistry = new Map()` and build one procedural signal node per `network.signals` item. `syncSignalsFromState(state)` should update lamp emissive colors using `state.ns_state` and `state.ew_state`.

- [ ] **Step 5: Run full focused tests**

Run: `python -m unittest tests.test_sumo_simulation_service -v`

Expected: PASS.

Run: `python -m unittest tests.test_three_bridge_scene_style -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add simulation/sumo_config.py assets/three-bridge.mjs tests/test_sumo_simulation_service.py tests/test_three_bridge_scene_style.py
git commit -m "feat: align signals to scoped SUMO geometry"
```

---

### Task 7: Browser Verification and Visual Acceptance

**Files:**
- Modify: none unless the verification exposes a concrete defect

- [ ] **Step 1: Run all focused automated checks**

Run: `python -m unittest tests.test_sumo_network_scope tests.test_sumo_visual_network_export tests.test_sumo_simulation_service tests.test_three_bridge_scene_style tests.test_callbacks_chart_layout -v`

Expected: PASS.

Run: `node --check assets/three-bridge.mjs`

Expected: no syntax errors.

- [ ] **Step 2: Start the Dash app**

Run: `python app.py`

Expected: server starts at `http://localhost:8050` or the configured Dash URL.

- [ ] **Step 3: Verify in browser**

Open `http://localhost:8050/dashboard`.

Expected visible result:
- The road shape matches `visual_network.json`.
- Vehicles are visible on roads within five seconds after Start Simulation.
- Pedestrians are visible on crossings when pedestrian density is not `none`.
- Signal lights change with backend phase state.
- Emergency vehicle appears with clear red/white styling when emergency mode is enabled.
- Road constraint appears as a visible barrier/red marker when selected.

- [ ] **Step 4: Commit final verification changes if files changed**

```bash
git add assets/three-bridge.mjs tests/test_three_bridge_scene_style.py tests/test_sumo_network_scope.py tests/test_sumo_visual_network_export.py
git commit -m "chore: verify geometry-first visualization"
```

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| SUMO network still contains extra traffic lights outside the selected intersection | RL state and visual behavior feel like a corridor instead of one intersection | Scope runtime routes and controlled TLS IDs first; only physically clip the network if scoped routing still produces visual confusion |
| Designed flows produce too many vehicles | The dashboard looks crowded and motion is hard to read | Keep base flows moderate and continue using scenario density scaling |
| Browser cannot fetch `assets/generated/visual_network.json` | The 3D panel may render fallback geometry only | Write the file under Dash-served `assets/` and use `/assets/generated/visual_network.json` |
| Procedural assets look too simple | Visual presentation may feel unfinished | Prioritize clarity for defense/demo first; replace individual procedural meshes with polished GLTF assets only after geometry is correct |
| Pedestrians route away from central crossings | Pedestrian counts do not match visible crossing behavior | Keep TraCI pedestrian templates tied to scoped edge IDs and verify active person positions against exported crossings |

## Checkpoints

- **After Task 2:** SUMO has one-intersection scope and explainable vehicle demand.
- **After Task 3:** The browser has a geometry file generated from SUMO, not hand-coded road coordinates.
- **After Task 5:** Three.js roads, crossings, and walking areas come from SUMO geometry.
- **After Task 7:** The live dashboard shows readable roads, moving vehicles, pedestrians, signals, emergency vehicles, and constraints.

