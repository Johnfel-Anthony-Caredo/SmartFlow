# 2D Map Readability Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the shared SMARTFLOW 2D map into a focused, operator-readable intersection view with stronger geometry, clearer entities, and non-blocking host-page layout.

**Architecture:** Keep `components/traffic_map.py` as the shared Dash SVG renderer for both dashboard map view and the live traffic page, but refactor it around a focused intersection viewport and clearer static/live layer composition. Move map styling into a dedicated `assets/traffic-map.css`, keep page-level metadata outside the canvas, and preserve the existing `build_traffic_map(state)` callback seam.

**Tech Stack:** Python 3.13, Dash, dash-svg, CSS, SUMO/TraCI-backed state payloads, unittest

---

## File Map

- `components/traffic_map.py`
  - Shared SVG renderer
  - Focused viewport calculation
  - Static map aids such as stop bars, lane arrows, and edge labels
  - Minimal in-map empty-state banner only
- `assets/traffic-map.css`
  - Dedicated 2D map styling
  - Map-specific layout helpers tightly coupled to the renderer composition
- `assets/styles.css`
  - Keep only host-page shell rules that are not map-specific
  - Remove the large embedded traffic-map styling block
- `layout.py`
  - Dashboard simulation card map-mode shell
  - Map legend/footer placement outside the active canvas
  - IDs/classes needed to suppress floating overlays in 2D mode
- `callbacks.py`
  - Extend the 3D/Map toggle callback so the dashboard can switch shell classes along with the current display toggles
- `pages/live_traffic.py`
  - Map-first operator layout
  - External legend and metadata cards instead of map-covering overlay chrome
- `tests/test_traffic_map_renderer.py`
  - Shared renderer structure and viewport assertions
- `tests/test_live_traffic_integration.py`
  - Shared renderer use across dashboard and live page
  - Dashboard map-mode and live-page shell integration checks
- `tests/test_traffic_map_styles.py`
  - Dedicated stylesheet split and selector ownership checks

### Task 1: Focus The Shared Renderer On The Intersection And Remove Blocking Overlay Chrome

**Files:**
- Modify: `components/traffic_map.py`
- Modify: `tests/test_traffic_map_renderer.py`

- [ ] **Step 1: Write the failing test**

```python
def test_renderer_focuses_intersection_and_keeps_overlay_minimal(self):
    network = load_visual_network()
    component = build_traffic_map(
        {
            "status": "stopped",
            "phase": "NS_GREEN",
            "phase_remaining": 0,
            "vehicles": [],
            "pedestrians": [],
            "queues": {},
            "visual": {},
            "scenario": {},
        },
        network=network,
    )

    classes = " ".join(_class_names(component))
    svg_node = next(node for node in _walk(component) if getattr(node, "className", "") == "traffic-map-svg")
    full_width = (network["bounds"]["max_x"] - network["bounds"]["min_x"]) + 36.0
    focused_width = float(svg_node.viewBox.split()[2])

    self.assertLess(focused_width, full_width)
    self.assertIn("traffic-map-empty-banner", classes)
    self.assertNotIn("traffic-map-status-strip", classes)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_traffic_map_renderer.TestTrafficMapRenderer.test_renderer_focuses_intersection_and_keeps_overlay_minimal -v`
Expected: FAIL because the current renderer uses the full network bounds, renders `traffic-map-empty-state`, and still includes the status strip overlay.

- [ ] **Step 3: Write minimal implementation**

```python
# In components/traffic_map.py
# - add a focused viewport helper that derives bounds from signals, crossings,
#   walking areas, and immediate approach lanes instead of the full exported bounds
# - switch build_traffic_map() to use that focused transform
# - remove the status-strip overlay children from build_traffic_map()
# - replace the centered empty-state class with a minimal `traffic-map-empty-banner`
# - keep the shared build_traffic_map(state, network=...) signature unchanged
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_traffic_map_renderer.TestTrafficMapRenderer.test_renderer_focuses_intersection_and_keeps_overlay_minimal -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add components/traffic_map.py tests/test_traffic_map_renderer.py
git commit -m "feat: focus shared 2D map viewport"
```

### Task 2: Add Operator Aids To The Shared SVG Renderer

**Files:**
- Modify: `components/traffic_map.py`
- Modify: `tests/test_traffic_map_renderer.py`

- [ ] **Step 1: Write the failing test**

```python
def test_renderer_adds_stop_bars_lane_arrows_and_edge_labels(self):
    component = build_traffic_map(
        {
            "status": "running",
            "phase": "NS_GREEN",
            "phase_remaining": 14,
            "vehicles": [],
            "pedestrians": [],
            "queues": {"north": 3, "east": 2},
            "visual": {
                "constraint_marker": {
                    "active": True,
                    "label": "Lane Closure",
                    "x": 640.0,
                    "y": 790.0,
                }
            },
            "scenario": {},
        }
    )
    classes = " ".join(_class_names(component))

    self.assertIn("traffic-map-stop-bar", classes)
    self.assertIn("traffic-map-lane-arrow", classes)
    self.assertIn("traffic-map-edge-label", classes)
    self.assertIn("traffic-map-constraint-band", classes)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_traffic_map_renderer.TestTrafficMapRenderer.test_renderer_adds_stop_bars_lane_arrows_and_edge_labels -v`
Expected: FAIL because the current renderer does not build dedicated stop-bar or lane-arrow layers.

- [ ] **Step 3: Write minimal implementation**

```python
# In components/traffic_map.py
# - add _build_stop_bar_layers(network, transform)
# - add _build_lane_arrow_layers(network, transform)
# - upgrade _build_map_labels() into edge labels with className='traffic-map-edge-label'
# - upgrade the current point-style constraint marker into a short affected-segment band
#   by projecting the marker onto the nearest visible approach lane or crossing geometry
# - place stop bars and arrows between lane markings and crossings in the SVG layer order
# - keep lane arrows intentionally sparse: one helpful arrow per approach direction
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_traffic_map_renderer.TestTrafficMapRenderer.test_renderer_adds_stop_bars_lane_arrows_and_edge_labels -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add components/traffic_map.py tests/test_traffic_map_renderer.py
git commit -m "feat: add 2D map operator aids"
```

### Task 3: Split The Map Styling Into A Dedicated Stylesheet And Strengthen Contrast Hierarchy

**Files:**
- Create: `assets/traffic-map.css`
- Modify: `assets/styles.css`
- Create: `tests/test_traffic_map_styles.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import unittest


class TestTrafficMapStyles(unittest.TestCase):
    def test_map_styles_live_in_dedicated_stylesheet(self):
        traffic_css = Path("assets/traffic-map.css")
        global_css = Path("assets/styles.css").read_text(encoding="utf-8")

        self.assertTrue(traffic_css.exists())
        css = traffic_css.read_text(encoding="utf-8")
        self.assertIn(".traffic-map-road", css)
        self.assertIn(".traffic-map-crossing", css)
        self.assertIn(".traffic-map-stop-bar", css)
        self.assertIn(".traffic-map-constraint-band", css)
        self.assertIn(".traffic-map-empty-banner", css)
        self.assertNotIn(".traffic-map-road", global_css)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_traffic_map_styles -v`
Expected: FAIL because `assets/traffic-map.css` does not exist yet and the traffic-map selectors still live in `assets/styles.css`.

- [ ] **Step 3: Write minimal implementation**

```css
/* In assets/traffic-map.css
   - move all traffic-map selectors out of assets/styles.css
   - darken the background layer
   - widen and clarify road, sidewalk, and crossing contrast
   - style new stop-bar, lane-arrow, edge-label, and constraint-band selectors
   - style the minimal empty banner

   In assets/styles.css
   - delete the SUMO-BACKED 2D TRAFFIC MAP block
   - keep only non-map host shell rules that belong to shared page layout
*/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_traffic_map_styles -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add assets/traffic-map.css assets/styles.css tests/test_traffic_map_styles.py
git commit -m "feat: split 2D map stylesheet"
```

### Task 4: Clean Up The Dashboard Map View Shell And Suppress Floating Overlays In 2D Mode

**Files:**
- Modify: `layout.py`
- Modify: `callbacks.py`
- Modify: `tests/test_live_traffic_integration.py`
- Modify: `assets/styles.css`

- [ ] **Step 1: Write the failing test**

```python
def test_dashboard_map_view_has_dedicated_shell_and_toggle_hook(self):
    layout_text = Path("layout.py").read_text(encoding="utf-8")
    callback_text = Path("callbacks.py").read_text(encoding="utf-8")

    self.assertIn("simulation-map-shell", layout_text)
    self.assertIn("simulation-map-legend", layout_text)
    self.assertIn("sim-viewport", layout_text)
    self.assertIn("simulation-map-shell", callback_text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_live_traffic_integration.TestLiveTrafficIntegration.test_dashboard_map_view_has_dedicated_shell_and_toggle_hook -v`
Expected: FAIL because the dashboard layout still relies on the old floating overlays and the view-toggle callback only flips raw display styles.

- [ ] **Step 3: Write minimal implementation**

```python
# In layout.py
# - wrap the dashboard map view in a dedicated `simulation-map-shell`
# - add ids/classes such as `sim-viewport`, `simulation-map-overlays`, and `simulation-map-legend`
# - keep the existing 3D/Map toggle buttons but move map legend/help text outside the viewport
#
# In callbacks.py
# - extend the clientside toggle callback outputs so map mode can also set shell class names
# - hide dashboard floating overlays while the map is active
#
# In assets/styles.css
# - keep only dashboard shell rules such as `.simulation-map-shell`, `.simulation-map-legend`,
#   and map-mode visibility helpers that are not part of the shared SVG styling
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_live_traffic_integration.TestLiveTrafficIntegration.test_dashboard_map_view_has_dedicated_shell_and_toggle_hook -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add layout.py callbacks.py assets/styles.css tests/test_live_traffic_integration.py
git commit -m "feat: clean dashboard 2D map shell"
```

### Task 5: Rebuild The Live Traffic Page As A Map-First Operator Layout

**Files:**
- Modify: `pages/live_traffic.py`
- Modify: `assets/styles.css`
- Modify: `tests/test_live_traffic_integration.py`

- [ ] **Step 1: Write the failing test**

```python
def test_live_traffic_page_uses_map_first_operator_layout(self):
    page_text = Path("pages/live_traffic.py").read_text(encoding="utf-8")

    self.assertIn("lt-live-map-shell", page_text)
    self.assertIn("lt-live-map-meta", page_text)
    self.assertIn("lt-live-legend", page_text)
    self.assertNotIn("lt-live-phase-chip", page_text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_live_traffic_integration.TestLiveTrafficIntegration.test_live_traffic_page_uses_map_first_operator_layout -v`
Expected: FAIL because the page still uses the older toolbar/phase-chip composition and has no external map legend shell.

- [ ] **Step 3: Write minimal implementation**

```python
# In pages/live_traffic.py
# - replace the current map toolbar + phase chip with a map-first shell:
#   - title block
#   - external legend block
#   - map container as the dominant region
#   - metadata cards in the side column
# - keep the existing ids used by callbacks for status, signal state, metrics, and events
#
# In assets/styles.css
# - update `.lt-live-grid`, `.lt-live-map-section`, `.lt-live-side`,
#   `.lt-live-panel`, and related classes so the page reads as a map-first operator layout
# - preserve the dark SMARTFLOW theme while reducing noise around the map
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_live_traffic_integration.TestLiveTrafficIntegration.test_live_traffic_page_uses_map_first_operator_layout -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pages/live_traffic.py assets/styles.css tests/test_live_traffic_integration.py
git commit -m "feat: redesign live traffic map layout"
```

### Task 6: Final Verification

**Files:**
- Modify: none unless a compatibility fix is needed

- [ ] **Step 1: Run renderer tests**

Run: `python -m unittest tests.test_traffic_map_renderer -v`
Expected: PASS

- [ ] **Step 2: Run integration and stylesheet tests**

Run: `python -m unittest tests.test_live_traffic_integration tests.test_traffic_map_styles -v`
Expected: PASS

- [ ] **Step 3: Run a direct renderer smoke check**

Run: `python -c "from components.traffic_map import build_traffic_map, load_visual_network; c = build_traffic_map({'status':'running','phase':'NS_GREEN','phase_remaining':12,'vehicles':[],'pedestrians':[],'queues':{'north':2},'visual':{},'scenario':{}}, network=load_visual_network()); print(getattr(c, 'className', ''), 'ok')"`
Expected: `traffic-map ok`

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "chore: verify 2D map readability redesign"
```
