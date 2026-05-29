# ADR-001: Use SUMO Geometry as the Three.js Visualization Source

## Status
Accepted

## Date
2026-05-29

## Context
SmartFlow uses SUMO and TraCI for traffic behavior, Dash for the dashboard shell, and Three.js for the live visual layer. The previous visual path mixed hand-placed roads, imported scenery, and simulated client-side motion, which made vehicles appear disconnected from the actual SUMO road structure.

## Decision
SUMO is the source of truth for road geometry and live entity positions. A deterministic exporter reads the scoped SUMO network and writes `assets/generated/visual_network.json`. The Three.js bridge renders roads, lanes, sidewalks, crossings, signals, cars, pedestrians, emergency vehicles, and road constraints from that exported geometry plus the live Dash/TraCI state.

The first visual asset layer is procedural and intentionally simple. It favors clear movement, visible roads, and debuggable geometry over realistic imported city assets.

## Alternatives Considered

### Keep hand-placed Three.js roads
- Pros: Fast to tweak visually.
- Cons: Drifts from SUMO geometry, causing vehicles to look random or off-road.
- Rejected because correctness and debuggability matter more than decorative layout at this phase.

### Load full InfiniTown assets as the main scene
- Pros: Polished city look.
- Cons: Hard to align with SUMO coordinates and easy to block the camera or hide traffic.
- Rejected for the first integration phase. Decorative assets can be reintroduced later after geometry alignment is stable.

## Consequences
- Regenerate `visual_network.json` whenever the SUMO network scope changes.
- Three.js should not own traffic physics or route layout.
- Future visual improvements should attach to exported SUMO geometry, not replace it.
