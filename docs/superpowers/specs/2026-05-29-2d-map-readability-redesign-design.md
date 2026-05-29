# 2D Map Readability Redesign Design

## Purpose

Redesign the shared SMARTFLOW 2D traffic map so it reads like a focused operator view rather than a decorative dashboard graphic.

The map should feel understandable in a plain 2D way, closer to the readability goals of the SUMO GUI:

- tight focus on the selected intersection instead of the whole corridor
- obvious road geometry, crossings, sidewalks, stop lines, and signal state
- moving vehicles and pedestrians that are easy to notice immediately
- page-level overlays that support the map without covering the active scene

This design keeps Dash as the UI shell and SUMO/TraCI as the source of truth. The work is limited to renderer layout, framing, SVG layer composition, styling, and host-page integration.

## Scope

### In scope

- Refactor the shared 2D map renderer in `components/traffic_map.py`
- Split the 2D map styling into a dedicated `assets/traffic-map.css`
- Tighten viewport framing so the main controlled intersection fills more of the canvas
- Improve visual hierarchy for roads, sidewalks, crossings, stop bars, signals, vehicles, pedestrians, queues, and constraints
- Move most runtime information out of the map canvas on both the dashboard map view and the live traffic page
- Preserve the current callback contract and shared renderer entry point `build_traffic_map(state)`
- Add or update renderer and integration tests

### Out of scope

- Replacing the Dash renderer with a canvas or WebGL map
- Changing SUMO geometry export format or TraCI state contract
- Rewriting dashboard metrics, chart logic, or simulation control flow
- Reworking the 3D view beyond hiding or suppressing conflicting overlays in map mode
- Making the 2D map a full SUMO GUI clone

## Current State Summary

The current map already uses a useful shared seam:

- `components/traffic_map.py` builds a shared SVG-based map
- `layout.py` uses that shared renderer inside the dashboard simulation card map view
- `pages/live_traffic.py` uses the same renderer in the dedicated live traffic page
- `callbacks.py` updates both views through the existing `build_traffic_map(state)` contract

That shared seam is the right foundation, but the current presentation still has several readability issues:

- the viewport is too loose, so the main junction feels small inside the canvas
- roads, sidewalks, and crossing layers do not form a strong visual hierarchy
- overlays still compete with map space
- the empty-state banner and status strip still behave like map-covering UI instead of supportive UI
- styles live inside the large global stylesheet, making focused map iteration harder

## Chosen Approach

Use a shared renderer and layout refactor.

Keep `build_traffic_map(state)` as the single renderer interface, but improve it in two coordinated layers:

1. the shared SVG renderer becomes a tighter, cleaner, more legible intersection map
2. the host pages move status and metadata out of the canvas so the map becomes the primary content

### Why this approach

- It improves both the dashboard map view and the live traffic page at once
- It preserves the current callback and state flow
- It solves the real framing problem instead of repainting the same zoomed-out scene
- It keeps the map understandable without needing a full architecture rewrite

### Rejected alternatives

#### CSS-only repaint

Rejected because it can improve contrast but cannot fully solve loose framing, oversized overlays, or cleaner composition.

#### Full SUMO GUI mimic

Rejected because the goal is readability and operator clarity, not a one-to-one SUMO interface clone that would fight the existing SMARTFLOW shell.

## User Experience Goals

The redesigned map should let a user:

- immediately understand the four-way intersection layout
- quickly distinguish road space from sidewalk and crossing space
- spot moving vehicles and pedestrians without searching
- read queues spatially along the approaches
- understand active constraints by looking at the affected segment
- monitor the map without floating cards blocking the active area

The user-approved behavior choices are:

- focus only on the main intersection, not the full surrounding road corridor
- keep the in-map UI minimal
- add approach labels and stop bars
- add only a few lane arrows where they improve orientation

## Target Architecture

### 1. Shared renderer

`components/traffic_map.py` remains the single shared renderer entry point.

Responsibilities:

- compute a focused intersection viewport from the exported SUMO geometry
- render a layered static road scene
- render live state entities from TraCI-backed state payloads
- keep in-map overlays minimal and non-blocking
- expose the same output shape used by dashboard and live traffic page callbacks

### 2. Dedicated map stylesheet

Add `assets/traffic-map.css` as the home for:

- traffic map SVG styling
- legend and empty-state styling
- map-specific host layout helpers where they are tightly coupled to the map composition

The large global `assets/styles.css` file should stop owning the core map styling block.

### 3. Host-page integration

`layout.py` and `pages/live_traffic.py` remain responsible for page-level metadata and controls.

Responsibilities:

- keep the map card visually dominant
- place runtime metadata at the page edge instead of over the map
- suppress bulky simulation overlays when the dashboard is in 2D map mode
- keep the live traffic page as a map-first operator layout

## Viewport And Framing Design

The map should no longer use the full exported network bounds as-is.

Instead, the renderer should compute a focused viewport around the selected intersection using:

- signal positions
- crossings
- walking areas
- the junction center
- immediate approach lanes used for queue readability

Viewport rules:

- include enough lane length to show queue buildup clearly
- exclude most extra corridor distance that makes the junction look tiny
- preserve breathing room with controlled padding rather than a large generic margin
- keep the framing stable so motion is trackable and the map does not feel jumpy

This change is the main reason the scene will feel larger and more understandable.

## Visual Hierarchy

The visual system should follow a strict darkest-to-brightest hierarchy:

1. background
2. sidewalks and walking areas
3. road shoulders and drivable surfaces
4. lane markings
5. stop bars and crosswalks
6. traffic signals
7. vehicles and pedestrians
8. active constraints and emergency emphasis

### Background

- darkest layer in the scene
- subtle texture or grid only if it does not compete with the road network
- no glowing decorative treatment that makes roads feel faint by comparison

### Sidewalks and walking areas

- visible and clearly distinct from roads
- muted slate treatment that stays subordinate to traffic movement
- enough contrast to make pedestrian space legible

### Roads

- broad real-surface look rather than thin glowing polylines
- outer shoulder and inner carriageway should read as intentional layers
- approach geometry should feel heavy enough to support signal control readability

### Lane markings

- crisp, brighter than the road but not brighter than vehicles
- dashed center or lane-divider treatment where useful
- no over-dense striping that turns the map noisy

### Crosswalks and stop bars

- crosswalks should be high-contrast zebra bands
- each controlled approach should have a clear stop bar before the crossing
- crossings should immediately anchor the eye near the center junction

### Labels and arrows

- edge labels for `North`, `South`, `East`, and `West`
- only a few lane arrows near stop lines where they help orientation
- no dense annotation field

### Signals

- larger and easier to scan than the current version
- clear red/yellow/green state with restrained glow
- signal state should be understandable at a glance without becoming decorative

### Vehicles

- larger and brighter so motion is easy to detect
- simpler, stronger top-down silhouettes
- emergency vehicles should be distinct immediately
- vehicle contrast should stay high against the road fill

### Pedestrians

- distinct walking markers that remain visible on sidewalks and crossings
- brighter than sidewalks but not brighter than signals or emergency emphasis
- obvious enough to confirm that pedestrian simulation is active

### Queues

- queue buildup should read spatially along the approaches
- queue overlays should reinforce density and position rather than hide lane detail
- approach congestion should be understandable without reading side-panel numbers

### Constraints

- closure, blockage, accident, or flooding should visually mark the affected road segment itself
- use localized marking rather than a generic scene-wide warning tone

## Renderer Composition

Refactor the SVG composition into clearer layers in this order:

1. ground
2. sidewalks and walking areas
3. road shoulders
4. road bodies
5. lane markings
6. stop bars
7. lane arrows
8. crosswalks
9. queue overlays
10. constraints
11. signals
12. vehicles
13. pedestrians
14. minimal labels

This composition makes the map easier to reason about in code and easier to refine visually later.

## Overlay And Layout Design

The map should be treated as primary content, not as a background behind floating cards.

### In-map UI

Keep only minimal in-map UI:

- a subtle top or corner empty-state banner when live state is missing
- no persistent in-map hint cards in this slice beyond the empty-state banner

Remove or relocate:

- the blocking center empty-state treatment
- the bottom status strip that occupies meaningful scene space
- any dashboard map-mode overlays that compete with the road view

### Dashboard map view

When the simulation card is showing `Map View`:

- the map should remain visually dominant
- the current floating overlays should be hidden, reduced, or moved outside the active map viewport
- the page should still preserve view toggle controls, but not at the cost of map readability

### Live traffic page

The live traffic page should become a map-first operator layout:

- map as the largest visual region
- title and mode context in the toolbar
- signal state, scenario state, and event feed in side cards
- metrics in supporting cards outside the canvas

## Behavior Design

### Empty state

If live state is empty:

- show a subtle empty-state banner outside the center of the map
- keep the junction visible so the user still understands the monitored location

### Active state

If live state is active:

- motion should be easy to detect immediately
- vehicles should feel visually trackable by size and contrast
- queue growth should be readable spatially

### Constraint state

If a scenario activates a closure, blockage, accident, or flooding condition:

- mark the affected segment clearly on the map
- preserve enough surrounding geometry so the user can understand its traffic impact

## Testing Strategy

Update and extend tests in:

- `tests/test_traffic_map_renderer.py`
- `tests/test_live_traffic_integration.py`

Focus areas:

- shared renderer still drives both dashboard and live traffic page
- focused intersection framing is applied
- stop bars, selective arrows, and labels exist in the composed renderer output
- empty state is no longer centered as blocking map content
- map-specific styling is separated from the large global stylesheet

Tests should favor stable structure and behavior assertions, not pixel-perfect visual matching.

## Risks And Mitigations

### Risk: focused framing still includes too much corridor

If the viewport calculation stays too loose, the redesign will still feel zoomed out even with better styling.

Mitigation:

- compute the viewport from intersection-centric geometry and immediate approaches rather than all exported bounds

### Risk: shared renderer change breaks one host page while fixing the other

Mitigation:

- keep the renderer shared but move page-specific metadata and overlays into host layouts
- verify both the dashboard map view and live traffic page in integration tests

### Risk: stronger overlays hide lane detail

Mitigation:

- keep queue and constraint treatments localized and translucent
- preserve lane and crossing readability beneath them

## Definition Of Done

The redesign is complete when:

- a user can instantly recognize the road layout of the selected intersection
- the intersection fills the canvas clearly enough to feel intentionally framed
- crosswalks, sidewalks, stop bars, vehicles, pedestrians, and signals are easy to see
- the dashboard map view no longer feels covered by floating overlays
- the live traffic page reads as a map-first operator interface
- the map communicates live traffic behavior, not just abstract geometry
- the result feels closer to SUMO GUI readability than to a decorative dashboard background
