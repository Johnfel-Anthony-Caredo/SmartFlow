# InfiniTown Style Finalization Design

Date: 2026-05-26
Status: Draft
Owner: GitHub Copilot

## Summary
Update the SMARTFLOW Three.js scene to match the InfiniTown look: a tight, readable, isometric-like intersection with dense surroundings. Keep the Python engine as the source of truth and apply all visual scale and placement changes in the Three.js bridge only.

## Goals
- Match InfiniTown camera framing (fixed, perspective, close crop on one intersection).
- Replace procedural roads/crosswalks/lights with GLTF assets where available.
- Align world scale to engine meters and keep vehicles readable.
- Add compact environment props around the intersection to increase density.
- Preserve engine-to-client sync and dashboard layout.

## Non-Goals
- No changes to simulation logic, routes, or signal timing.
- No new RL features or training work.
- No additional pages or changes to non-dashboard layouts.

## References
- InfiniTownTS camera: Perspective camera, FOV ~30, position ~[70, 120, 70], fixed camera (no orbit).
- SMARTFLOW geometry constants in [simulation/constants.py](simulation/constants.py) and [simulation/network.py](simulation/network.py).
- Available assets:
  - Traffic: road.gltf, crosswalk.gltf, traffic_light.gltf, pedestrian_crossing_sign.gltf
  - Vehicles: car.gltf, car_v2.gltf, suv.gltf, taxi.gltf, bus.gltf, truck.gltf, ambulance.gltf, police_car.gltf
  - Pedestrians: pedestrian.gltf
  - Environment: apartments.gltf, coffeeshop.gltf, factory.gltf, fastfood.gltf, gas.gltf, house.gltf, house2.gltf, house3.gltf, park.gltf, residence.gltf, shoparea.gltf, shops.gltf, stadium.gltf, supermarket.gltf

## Current State (Baseline)
- Orthographic camera with auto-orbit motion.
- Procedural roads, crosswalks, traffic lights, and buildings.
- Vehicles and pedestrians are procedural meshes.
- Engine state drives positions; client reads window.__smartflowState.

## Proposed Architecture
- Keep state flow: engine -> engine-state-json -> window.__smartflowState -> SmartFlowScene.update().
- Add a root group: worldRoot.
  - staticRoot: roads, crosswalks, traffic lights, props.
  - dynamicRoot: vehicles, pedestrians.
- Apply scale and offsets at worldRoot to align GLTF assets to engine meters.

## Camera Plan
- Replace OrthographicCamera with PerspectiveCamera.
- Use FOV 30, near 0.1, far 500.
- Initial camera: position [70, 120, 70], lookAt [0, 0, 0].
- Fixed camera (no orbit animation).
- On resize, update aspect and projection matrix.

## Scale and Coordinate Mapping
- Engine coordinates are meters. Map (x, y) -> (x, z = -y) in Three.js.
- Compute WORLD_SCALE from road.gltf:
  - Load road model, compute bounding box width.
  - Scale to match ROAD_WIDTH = 7.0m.
  - Fallback to constant scale if box is invalid.
- Apply WORLD_SCALE to worldRoot so static and dynamic objects stay aligned.

## Scene Layout Plan
- Roads and intersection
  - Load road.gltf and crosswalk.gltf and position around origin.
  - Repeat and rotate road.gltf to build four approaches; if no dedicated
    intersection mesh exists, overlap road segments and crosswalks to form the
    center.
  - Align stop lines to STOP_LINE_OFFSET (14m) and CROSSWALK_WIDTH (3m).
  - Keep intersection centered at (0, 0).
- Crosswalks
  - Place four crosswalks at +/- STOP_LINE_OFFSET, aligned to each approach.
  - Rotate crosswalks for east/west approaches.
- Traffic lights
  - Load traffic_light.gltf and place near corners at consistent offsets.
  - Start offsets: x or z = +/- (STOP_LINE_OFFSET - 2), perpendicular offset
    = +/- (ROAD_WIDTH / 2 + 1). Tune after visual check.
  - Add emissive bulb meshes as children if the GLTF lacks distinct bulbs.
  - Maintain north/south vs east/west color updates from engine state.
- Environment props
  - Place 6-10 environment GLTFs around the edges to frame the intersection.
  - Keep center clear for traffic readability.

## Dynamic Agents
- Vehicles
  - Use vehicle GLTFs by type; fallback to boxes if loading fails.
  - Scale vehicle meshes to match VEHICLE_LENGTH and VEHICLE_WIDTH.
  - Apply heading rotation from engine state.
- Pedestrians
  - Use pedestrian.gltf; fallback to boxes if loading fails.
  - Apply light smoothing (lerp) to reduce teleport feel without changing engine.

## Lighting and Atmosphere
- Ambient light: soft, neutral (0xcccccc ~ 0.7-0.9).
- Directional light: warm, cast shadows, tuned for clarity.
- Optional fill light for contrast on the shadow side.
- Reduce fog density or disable if it reduces readability.

## Error Handling and Fallbacks
- All GLTF loads are non-blocking.
- If a GLTF fails to load, keep a procedural fallback for that asset.
- If scale measurement fails, use a single tweakable constant.

## Acceptance Criteria
- Intersection fills most of the simulation viewport.
- Camera is fixed and close, matching InfiniTown perspective.
- Crosswalks and traffic lights are aligned to stop lines and readable.
- Vehicles follow lanes visually with correct scale.
- Environment feels compact and city-like, not empty.
- Engine synchronization remains intact.

## Verification
- Manual visual check against InfiniTown screenshot.
- Confirm loading message hides after init.
- Confirm dashboard remains functional and responsive.
