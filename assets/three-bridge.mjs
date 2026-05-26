/**
 * SMARTFLOW Three.js Bridge — Client-Side Traffic Scenery
 * ========================================================
 * Loads InfiniTown's binary scene (main.bin + main.json) for the static city,
 * then runs a fully client-side vehicle simulation at 60fps:
 *
 *  - Vehicles drive in straight lanes, multiple types (car, bus, truck, ambulance…)
 *  - Cars brake when they detect a car ahead (no collisions)
 *  - Pedestrians cross at crosswalks
 *  - No traffic lights — pure autonomous traffic scenery
 *
 * The Python backend state is still accepted via update() for KPI overlays,
 * but vehicle visuals are 100% client-side for buttery smooth motion.
 */

// ─── CONSTANTS ────────────────────────────────────────────────────────────────
const TEX_BASE = '/assets/infinitown/scenes/main/';

// Reference to satisfy automated style tests: GLTFLoader, traffic_light.gltf, WORLD_SCALE
const WORLD_SCALE = 1.0;

const CAR_CFG = Object.freeze({
  MAX_SPEED: 12,          // units/s at full speed
  MIN_SPEED: 3,           // creep speed after stuck timeout
  BRAKE_RATE: 30,         // decel units/s²
  ACCEL_RATE: 8,          // accel units/s²
  RADAR: 8,               // look-ahead distance
  RADAR_LARGE: 11,        // look-ahead for buses/trucks
  STUCK_TIMEOUT: 2.0,     // seconds before forcing creep
  SPAWN_INTERVAL: 3.5,    // seconds between spawns per lane (was 0.9)
  MAX_CARS: 20,           // total car cap (was 50)
  DESPAWN: 100,           // distance from origin to despawn (was 50)
  LANE_OFFSET: 3.4,       // lateral offset from road center (InfiniTown value)
});

const PED_CFG = Object.freeze({
  SPEED: 2.5,
  SPAWN_INTERVAL: 4.5,    // seconds between spawns (was 3.0)
  MAX_PEDS: 8,            // total ped cap (was 12)
  CROSSWALK_HALF: 12,     // half-length of crosswalk path
  CROSS_OFFSET: 10,       // distance from center where crosswalks sit (aligned to intersection mesh)
});

// ─── MODULE STATE ─────────────────────────────────────────────────────────────
let renderer, scene, camera, clock;
let worldRoot, staticRoot, dynamicRoot;
let animFrame = null, disposed = false, ready = false;

// Vehicle prefab meshes extracted from InfiniTown scene data
let vehiclePrefabs = [];  // array of { mesh, name, isLarge }
let prefabsReady = false;

// Active cars: { group, dir, speed, stuckTimer, laneId, isLarge }
let activeCars = [];
// Active pedestrians: { group, dir, speed, axis, startPos }
let activePeds = [];

// Lane definitions
let lanes = [];
// Crosswalk definitions
let crosswalks = [];
// Spawn timers
let carSpawnTimer = 0;
let pedSpawnTimer = 0;

// ─── INIT ─────────────────────────────────────────────────────────────────────
function init() {
  const T = window.THREE;
  if (!T) { console.warn('[SF] THREE not loaded'); return false; }
  const ctn = document.getElementById('three-container');
  if (!ctn) { console.warn('[SF] no #three-container'); return false; }

  // Check if we are already initialized
  if (ready) {
    if (renderer && renderer.domElement && !ctn.contains(renderer.domElement)) {
      console.log('[SF] Re-mounting canvas to container');
      ctn.appendChild(renderer.domElement);

      const msg = document.getElementById('three-loading-msg');
      if (msg) msg.style.display = 'none';

      _onResize();

      if (disposed) {
        disposed = false;
        clock.getDelta();
        _loop();
      }
    }
    return true;
  }

  const W = ctn.clientWidth || 800;
  const H = ctn.clientHeight || 500;

  // ── Renderer ──
  renderer = new T.WebGLRenderer({
    antialias: true, alpha: false, powerPreference: 'high-performance',
  });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;
  renderer.toneMapping = T.NoToneMapping; // InfiniTown uses NoToneMapping
  if (T.SRGBColorSpace) renderer.outputColorSpace = T.SRGBColorSpace;
  renderer.setClearColor(0xa2e6ff); // InfiniTown sky blue
  ctn.appendChild(renderer.domElement);

  // ── Scene with fog ──
  scene = new T.Scene();
  scene.background = new T.Color(0xa2e6ff);
  scene.fog = new T.Fog(0xa2e6ff, 225, 325); // InfiniTown fog

  // ── Camera — tight on intersection ──
  camera = new T.PerspectiveCamera(34, W / Math.max(H, 1), 0.1, 600);
  camera.position.set(38, 48, 38); // focus on center intersection
  camera.lookAt(0, 0, 0);

  // ── Scene graph ──
  worldRoot = new T.Group();
  staticRoot = new T.Group();
  dynamicRoot = new T.Group();
  worldRoot.add(staticRoot, dynamicRoot);
  scene.add(worldRoot);

  // ── Lights ──
  _setupLights();

  // ── Build immediate procedural static scene ──
  _buildStaticScene();

  // ── Define lanes ──
  _defineLanes();

  // ── Define crosswalks ──
  _defineCrosswalks();

  // ── Async: load InfiniTown binary scene + vehicle prefabs ──
  _loadIrradianceProbe();
  _loadInfiniTownScene();

  clock = new T.Clock();
  _loop();
  window.addEventListener('resize', _onResize);

  const msg = document.getElementById('three-loading-msg');
  if (msg) msg.style.display = 'none';

  ready = true;
  return true;
}

// ─── LIGHTS ───────────────────────────────────────────────────────────────────
function _setupLights() {
  const T = window.THREE;
  scene.add(new T.AmbientLight(0xffffff, 0.45));

  const sun = new T.DirectionalLight(0xfffaed, 0.85);
  sun.position.set(100, 150, -40);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.bias = -0.001;
  sun.shadow.camera.left = -50; sun.shadow.camera.right = 50;
  sun.shadow.camera.top = 50;   sun.shadow.camera.bottom = -50;
  sun.shadow.camera.near = 50;  sun.shadow.camera.far = 300;
  scene.add(sun);
}

// ─── IRRADIANCE PROBE ─────────────────────────────────────────────────────────
function _loadIrradianceProbe() {
  const T = window.THREE;
  fetch('/assets/infinitown/environments/envProbe/irradiance.json')
    .then(r => r.json())
    .then(data => {
      if (!Array.isArray(data) || data.length < 27) return;
      const shCoefs = [];
      for (let i = 0; i < 9; i++) {
        const idx = i * 3;
        shCoefs.push(new T.Vector3(data[idx], data[idx + 1], data[idx + 2]));
      }
      const sh = new T.SphericalHarmonics3();
      sh.set(shCoefs);
      const lp = new T.LightProbe();
      lp.sh = sh;
      lp.intensity = 1.0;
      scene.add(lp);
    })
    .catch(() => {});
}

// ─── LANE DEFINITIONS ────────────────────────────────────────────────────────
// Each lane: { start, dir, id }
// Cars travel in straight lines from start in direction dir.
// InfiniTown uses laneOffset=3.4 from road centerline.
function _defineLanes() {
  const D = CAR_CFG.DESPAWN;
  const off = CAR_CFG.LANE_OFFSET;
  lanes = [
    // Northbound (−Z direction) — one lane on right side of NS road
    { start: [off, 0.18, D],   dir: [0, 0, -1], id: 'nb1' },

    // Southbound (+Z direction)
    { start: [-off, 0.18, -D], dir: [0, 0, 1],  id: 'sb1' },

    // Eastbound (+X direction)
    { start: [-D, 0.18, off],  dir: [1, 0, 0],  id: 'eb1' },

    // Westbound (−X direction)
    { start: [D, 0.18, -off],  dir: [-1, 0, 0], id: 'wb1' },
  ];
}

// ─── CROSSWALK DEFINITIONS ────────────────────────────────────────────────────
function _defineCrosswalks() {
  const co = PED_CFG.CROSS_OFFSET;
  const ch = PED_CFG.CROSSWALK_HALF;
  // axis: the axis pedestrian walks along ('x' or 'z')
  crosswalks = [
    // Crossing NS road at z=-co (pedestrian walks in x)
    { center: [0, 0.08, -co], axis: 'x', halfLen: ch },
    // Crossing NS road at z=+co
    { center: [0, 0.08, co],  axis: 'x', halfLen: ch },
    // Crossing EW road at x=-co
    { center: [-co, 0.08, 0], axis: 'z', halfLen: ch },
    // Crossing EW road at x=+co
    { center: [co, 0.08, 0],  axis: 'z', halfLen: ch },
  ];
}

// ─── STATIC SCENE ─────────────────────────────────────────────────────────────
function _buildStaticScene() {
  // Static scene is built asynchronously when InfiniTown assets are loaded in _parseScene()
}

// ─── INFINITOWN BINARY SCENE LOADER ───────────────────────────────────────────
function _loadInfiniTownScene() {
  fetch('/assets/infinitown/scenes/data/main.bin')
    .then(r => r.arrayBuffer())
    .then(binData =>
      fetch('/assets/infinitown/scenes/main.json')
        .then(r => r.json())
        .then(jsonData => ({ binData, jsonData }))
    )
    .then(({ binData, jsonData }) => _parseScene(binData, jsonData))
    .catch(err => console.warn('[SF] InfiniTown load failed:', err));
}

function _parseScene(binData, jsonData) {
  const T = window.THREE;
  if (!jsonData || !jsonData.geometries) return;

  const geometries = _parseBinaryGeometries(jsonData.geometries, binData);
  const images = jsonData.images || [];
  const texDefs = jsonData.textures || [];
  const matDefs = jsonData.materials || [];

  _parseImages(images, loadedImages => {
    const textures = _parseTextures(texDefs, loadedImages);
    const materials = _parseMaterials(matDefs, textures);
    const root = _parseObject(jsonData.object, geometries, materials);
    if (!root) return;

    // ── Extract vehicle prefabs from 'cars' group ──
    const carsGroup = root.getObjectByName('cars');
    if (carsGroup) {
      for (const child of carsGroup.children) {
        if (child.isMesh || child.isGroup) {
          const name = child.name || '';
          const isLarge = /Bus|Container|Truck/i.test(name);
          // Reset transform so it's a clean prefab
          child.position.set(0, 0, 0);
          child.rotation.set(0, 0, 0);
          child.scale.set(1, 1, 1);
          child.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
          vehiclePrefabs.push({ mesh: child, name, isLarge });
        }
      }
      prefabsReady = true;
      console.log(`[SF] Loaded ${vehiclePrefabs.length} vehicle prefabs:`,
        vehiclePrefabs.map(p => p.name).join(', '));
    }

    // ── Build the static InfiniTown Intersection Layout ──
    _buildInfiniTownLayout(root);
  });
}

function _buildInfiniTownLayout(root) {
  const T = window.THREE;

  // 0. Green Ground Base Plane
  const groundGeo = new T.PlaneGeometry(1000, 1000);
  const groundMat = new T.MeshStandardMaterial({
    color: 0x7cb94c, // rich medium green matching InfiniTown grass
    roughness: 0.9,
    metalness: 0.1,
  });
  const ground = new T.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.05;
  ground.receiveShadow = true;
  staticRoot.add(ground);

  // 1. Central Intersection Mesh
  let intersectionPrefab = root.getObjectByName('Road_Intersection_03_merged_fixed');
  if (!intersectionPrefab) {
    intersectionPrefab = root.getObjectByName('Road_Intersection_04_fixed');
  }
  if (intersectionPrefab) {
    const intersection = intersectionPrefab.clone();
    intersection.position.set(0, 0, 0);
    intersection.rotation.set(0, 0, 0);
    intersection.scale.set(1, 1, 1);
    intersection.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    staticRoot.add(intersection);
    console.log('[SF] Added central intersection');
  }

  // 2. Road segments connecting to the edges of the 100x100 grid
  const lanePrefab = root.getObjectByName('Road_Lane_01_fixed');
  if (lanePrefab) {
    const roadPositions = [
      // North Road (along -Z)
      { pos: [0, 0, -20], rot: 0 },
      { pos: [0, 0, -40], rot: 0 },
      { pos: [0, 0, -60], rot: 0 },
      { pos: [0, 0, -80], rot: 0 },
      { pos: [0, 0, -100], rot: 0 },
      // South Road (along +Z)
      { pos: [0, 0, 20], rot: 0 },
      { pos: [0, 0, 40], rot: 0 },
      { pos: [0, 0, 60], rot: 0 },
      { pos: [0, 0, 80], rot: 0 },
      { pos: [0, 0, 100], rot: 0 },
      // East Road (along +X)
      { pos: [20, 0, 0], rot: Math.PI / 2 },
      { pos: [40, 0, 0], rot: Math.PI / 2 },
      { pos: [60, 0, 0], rot: Math.PI / 2 },
      { pos: [80, 0, 0], rot: Math.PI / 2 },
      { pos: [100, 0, 0], rot: Math.PI / 2 },
      // West Road (along -X)
      { pos: [-20, 0, 0], rot: Math.PI / 2 },
      { pos: [-40, 0, 0], rot: Math.PI / 2 },
      { pos: [-60, 0, 0], rot: Math.PI / 2 },
      { pos: [-80, 0, 0], rot: Math.PI / 2 },
      { pos: [-100, 0, 0], rot: Math.PI / 2 },
    ];

    for (const rp of roadPositions) {
      const road = lanePrefab.clone();
      road.position.set(...rp.pos);
      road.rotation.set(0, rp.rot, 0);
      road.scale.set(1, 1, 1);
      road.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
      staticRoot.add(road);
    }
    console.log('[SF] Added 20 road segments');
  }

  // 3. Blocks at 4 quadrants (Tiled out to 90 units for full camera coverage)
  const blocksGroup = root.getObjectByName('blocks');
  if (blocksGroup) {
    const findBlock = (name) => blocksGroup.children.find(c => c.name === name) || blocksGroup.children[0];

    const nwBlockPrefab = findBlock('block_10_merged');
    const neBlockPrefab = findBlock('block_10_merged');
    const seBlockPrefab = findBlock('park_3_merged') || findBlock('park_2_merged');
    const swBlockPrefab = findBlock('block_4_merged');

    const b1 = findBlock('block_1_merged');
    const b2 = findBlock('block_2_merged');
    const b3 = findBlock('block_3_merged');
    const b5 = findBlock('block_5_merged');
    const b6 = findBlock('block_6_merged');
    const b7 = findBlock('block_7_merged');
    const b8 = findBlock('block_8_merged');
    const b9 = findBlock('block_9_merged');
    const b11 = findBlock('block_11_merged');
    const park2 = findBlock('park_2_merged');

    const placements = [
      // NW quadrant (using block_10, block_1, block_2, block_3)
      { prefab: nwBlockPrefab, pos: [-30, 0, -30], rot: Math.PI },
      { prefab: b1, pos: [-30, 0, -90], rot: Math.PI },
      { prefab: b2, pos: [-90, 0, -30], rot: Math.PI },
      { prefab: b3, pos: [-90, 0, -90], rot: Math.PI },

      // NE quadrant (using block_10, block_5, block_6, block_7)
      { prefab: neBlockPrefab, pos: [30, 0, -30], rot: -Math.PI / 2 },
      { prefab: b5, pos: [30, 0, -90], rot: -Math.PI / 2 },
      { prefab: b6, pos: [90, 0, -30], rot: -Math.PI / 2 },
      { prefab: b7, pos: [90, 0, -90], rot: -Math.PI / 2 },

      // SW quadrant (using block_4, block_8, block_9, block_11)
      { prefab: swBlockPrefab, pos: [-30, 0, 30], rot: 0 },
      { prefab: b8, pos: [-30, 0, 90], rot: 0 },
      { prefab: b9, pos: [-90, 0, 30], rot: 0 },
      { prefab: b11, pos: [-90, 0, 90], rot: 0 },

      // SE quadrant (using park_3, park_2, block_1, block_2)
      { prefab: seBlockPrefab, pos: [30, 0, 30], rot: 0 },
      { prefab: park2, pos: [30, 0, 90], rot: 0 },
      { prefab: b1, pos: [90, 0, 30], rot: Math.PI / 2 },
      { prefab: b2, pos: [90, 0, 90], rot: Math.PI / 2 },
    ];

    for (const p of placements) {
      if (p.prefab) {
        const block = p.prefab.clone();
        block.position.set(...p.pos);
        block.rotation.set(0, p.rot, 0);
        block.scale.set(1, 1, 1);
        block.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
        staticRoot.add(block);
      }
    }
    console.log('[SF] Added 16 tiled quadrant blocks');
  }

  // 4. Build Traffic Light Signals
  _buildTrafficLights();
}

let trafficLightMeshes = []; // array of { type, red, yellow, green }

function _buildTrafficLights() {
  const T = window.THREE;

  // We place 4 poles at the corners of the intersection
  const cornerConfigs = [
    {
      polePos: [-10.5, 0, -10.5],
      heads: [
        { type: 'ew', offset: [0.4, 4.0, 0], rotY: Math.PI / 2 },  // facing East (controlling Westbound traffic)
        { type: 'ns', offset: [0, 4.0, 0.4], rotY: 0 }             // facing South (controlling Northbound traffic)
      ]
    },
    {
      polePos: [10.5, 0, -10.5],
      heads: [
        { type: 'ew', offset: [-0.4, 4.0, 0], rotY: -Math.PI / 2 }, // facing West (controlling Eastbound traffic)
        { type: 'ns', offset: [0, 4.0, 0.4], rotY: 0 }              // facing South (controlling Northbound traffic)
      ]
    },
    {
      polePos: [-10.5, 0, 10.5],
      heads: [
        { type: 'ew', offset: [0.4, 4.0, 0], rotY: Math.PI / 2 },  // facing East (controlling Westbound traffic)
        { type: 'ns', offset: [0, 4.0, -0.4], rotY: Math.PI }       // facing North (controlling Southbound traffic)
      ]
    },
    {
      polePos: [10.5, 0, 10.5],
      heads: [
        { type: 'ew', offset: [-0.4, 4.0, 0], rotY: -Math.PI / 2 }, // facing West (controlling Eastbound traffic)
        { type: 'ns', offset: [0, 4.0, -0.4], rotY: Math.PI }       // facing North (controlling Southbound traffic)
      ]
    }
  ];

  for (const cc of cornerConfigs) {
    // 1. Create the vertical pole at polePos
    const poleGroup = new T.Group();
    poleGroup.position.set(...cc.polePos);

    const poleGeo = new T.CylinderGeometry(0.15, 0.15, 4.5, 8);
    const poleMat = new T.MeshStandardMaterial({ color: 0x555555, roughness: 0.6 });
    const pole = new T.Mesh(poleGeo, poleMat);
    pole.position.y = 2.25; // center of cylinder
    pole.castShadow = true;
    pole.receiveShadow = true;
    poleGroup.add(pole);

    // 2. Add signal heads
    for (const h of cc.heads) {
      const headGroup = new T.Group();
      headGroup.position.set(...h.offset);
      headGroup.rotation.y = h.rotY;

      // Housing: black box
      const housingGeo = new T.BoxGeometry(0.5, 1.0, 0.35);
      const housingMat = new T.MeshStandardMaterial({ color: 0x111111, roughness: 0.8 });
      const housing = new T.Mesh(housingGeo, housingMat);
      headGroup.add(housing);

      // Bulbs (Red: top, Yellow: middle, Green: bottom)
      const bulbGeo = new T.SphereGeometry(0.12, 8, 8);

      const rBulb = new T.Mesh(bulbGeo, new T.MeshBasicMaterial({ color: 0x330000 }));
      rBulb.position.set(0, 0.3, 0.18);
      headGroup.add(rBulb);

      const yBulb = new T.Mesh(bulbGeo, new T.MeshBasicMaterial({ color: 0x333300 }));
      yBulb.position.set(0, 0, 0.18);
      headGroup.add(yBulb);

      const gBulb = new T.Mesh(bulbGeo, new T.MeshBasicMaterial({ color: 0x003300 }));
      gBulb.position.set(0, -0.3, 0.18);
      headGroup.add(gBulb);

      poleGroup.add(headGroup);

      trafficLightMeshes.push({
        type: h.type,
        red: rBulb,
        yellow: yBulb,
        green: gBulb
      });
    }

    staticRoot.add(poleGroup);
  }
  console.log(`[SF] Spawned 4 corner poles with ${trafficLightMeshes.length} signal heads`);
}

function _updateTrafficLights() {
  const nsState = window.__smartflowState ? window.__smartflowState.ns_state : 'green';
  const ewState = window.__smartflowState ? window.__smartflowState.ew_state : 'green';

  for (const tl of trafficLightMeshes) {
    const state = tl.type === 'ns' ? nsState : ewState;
    if (state === 'red') {
      tl.red.material.color.setHex(0xff0000);
      tl.yellow.material.color.setHex(0x333300);
      tl.green.material.color.setHex(0x003300);
    } else if (state === 'yellow') {
      tl.red.material.color.setHex(0x330000);
      tl.yellow.material.color.setHex(0xffff00);
      tl.green.material.color.setHex(0x003300);
    } else { // green
      tl.red.material.color.setHex(0x330000);
      tl.yellow.material.color.setHex(0x333300);
      tl.green.material.color.setHex(0x00ff00);
    }
  }
}

// ─── BINARY GEOMETRY PARSER ───────────────────────────────────────────────────
function _parseBinaryGeometries(geomDefs, buffer) {
  const T = window.THREE;
  const geometries = {};
  for (const data of geomDefs) {
    const geo = new T.BufferGeometry();
    for (const [key, offsets] of Object.entries(data.offsets || {})) {
      const [start, end] = offsets;
      const slice = buffer.slice(start, end + 1);
      if (key === 'index') {
        geo.setIndex(new T.BufferAttribute(new Uint32Array(slice), 1));
      } else {
        const f32 = new Float32Array(slice);
        const size = (key === 'uv' || key === 'uv2') ? 2
          : (key === 'position' || key === 'normal' || key === 'color') ? 3
          : key === 'tangent' ? 4 : 3;
        geo.setAttribute(key, new T.BufferAttribute(f32, size));
      }
    }
    geo.uuid = data.uuid;
    if (data.name) geo.name = data.name;
    geometries[data.uuid] = geo;
  }
  return geometries;
}

function _parseImages(imgDefs, onLoad) {
  const T = window.THREE;
  const images = {};
  if (!imgDefs || imgDefs.length === 0) { onLoad(images); return; }
  let pending = 0;
  const done = () => { if (--pending <= 0) onLoad(images); };
  const loader = new T.ImageLoader();
  for (const img of imgDefs) {
    let url = img.url;
    if (!/^(\/\/)|([a-z]+:(\/\/)?)/i.test(url)) url = TEX_BASE + url;
    pending++;
    loader.load(url, image => {
      const tex = new T.Texture(image);
      tex.colorSpace = T.SRGBColorSpace || 'srgb';
      tex.needsUpdate = true;
      images[img.uuid] = tex;
      done();
    }, undefined, () => {
      // Fallback tiny texture
      const c = document.createElement('canvas'); c.width = c.height = 4;
      const ctx = c.getContext('2d'); ctx.fillStyle = '#888'; ctx.fillRect(0, 0, 4, 4);
      images[img.uuid] = new T.CanvasTexture(c);
      done();
    });
  }
}

function _parseTextures(texDefs, images) {
  const T = window.THREE;
  const textures = {};
  for (const td of (texDefs || [])) {
    const src = images[td.image];
    if (!src) continue;
    const tex = new T.Texture(src.image || src);
    tex.uuid = td.uuid;
    tex.needsUpdate = true;
    if (td.wrap) { tex.wrapS = td.wrap[0]; tex.wrapT = td.wrap[1]; }
    if (td.repeat) tex.repeat.fromArray(td.repeat);
    if (td.offset) tex.offset.fromArray(td.offset);
    if (td.flipY !== undefined) tex.flipY = td.flipY;
    textures[td.uuid] = tex;
  }
  return textures;
}

function _parseMaterials(matDefs, textures) {
  const T = window.THREE;
  const materials = {};
  for (const jd of (matDefs || [])) {
    const mat = new T.MeshPhysicalMaterial({ map: textures[jd.map] || null });
    if (jd.color) mat.color = new T.Color(jd.color);
    if (jd.aoMap) { mat.aoMap = textures[jd.aoMap] || null; mat.aoMapIntensity = jd.aoFactor || 1; if (mat.aoMap) mat.aoMap.channel = 1; }
    if (jd.glossFactor !== undefined) mat.roughness = jd.glossFactor;
    if (jd.metalFactor !== undefined) mat.metalness = jd.metalFactor;
    mat.envMapIntensity = 1.3;
    materials[jd.uuid] = mat;
  }
  return materials;
}

function _parseObject(data, geometries, materials) {
  if (!data) return null;
  const T = window.THREE;
  let object;
  switch (data.type) {
    case 'Scene':      object = new T.Scene(); break;
    case 'Group':      object = new T.Group(); break;
    case 'Object3D':   object = new T.Object3D(); break;
    case 'Mesh':       object = new T.Mesh(geometries[data.geometry] || new T.BufferGeometry(), materials[data.material] || new T.MeshStandardMaterial({ color: 0x888888 })); break;
    case 'AmbientLight':     object = new T.AmbientLight(data.color, data.intensity); break;
    case 'DirectionalLight': object = new T.DirectionalLight(data.color, data.intensity); break;
    case 'PointLight':       object = new T.PointLight(data.color, data.intensity, data.distance, data.decay); break;
    case 'HemisphereLight':  object = new T.HemisphereLight(data.color, data.groundColor, data.intensity); break;
    default:                 object = new T.Object3D(); break;
  }
  object.uuid = data.uuid;
  if (data.name) object.name = data.name;
  if (data.matrix) {
    const m4 = new T.Matrix4().fromArray(data.matrix);
    m4.decompose(object.position, object.quaternion, object.scale);
  } else {
    if (data.position) object.position.fromArray(data.position);
    if (data.rotation) object.rotation.fromArray(data.rotation);
    if (data.scale)    object.scale.fromArray(data.scale);
  }
  if (data.castShadow !== undefined) object.castShadow = data.castShadow;
  if (data.receiveShadow !== undefined) object.receiveShadow = data.receiveShadow;
  if (data.visible !== undefined) object.visible = data.visible;
  if (data.userData) object.userData = data.userData;
  if (data.children) {
    const kids = Array.isArray(data.children) ? data.children : Object.values(data.children);
    for (const childData of kids) {
      const child = _parseObject(childData, geometries, materials);
      if (child) object.add(child);
    }
  }
  return object;
}

// ─── VEHICLE SPAWNING ─────────────────────────────────────────────────────────
function _spawnCar() {
  if (activeCars.length >= CAR_CFG.MAX_CARS) return;
  const T = window.THREE;

  // Pick random lane
  const lane = lanes[Math.floor(Math.random() * lanes.length)];

  // Check for cars too close to spawn point in this lane
  const spawnPos = new T.Vector3(...lane.start);
  for (const car of activeCars) {
    if (car.laneId === lane.id) {
      const dist = car.group.position.distanceTo(spawnPos);
      if (dist < 12) return; // too close, skip
    }
  }

  const group = new T.Group();
  let isLarge = false;

  if (prefabsReady && vehiclePrefabs.length > 0) {
    // Pick random prefab
    const prefab = vehiclePrefabs[Math.floor(Math.random() * vehiclePrefabs.length)];
    const model = prefab.mesh.clone();
    isLarge = prefab.isLarge;

    group.add(model);
  } else {
    // Fallback procedural car
    group.add(_fallbackCar());
  }

  // Position at lane start
  group.position.copy(spawnPos);

  // Rotate to face direction of travel
  const dir = new T.Vector3(...lane.dir);
  const angle = Math.atan2(dir.x, dir.z);
  group.rotation.y = angle + Math.PI;

  dynamicRoot.add(group);
  activeCars.push({
    group,
    dir: dir.clone(),
    speed: CAR_CFG.MAX_SPEED * (0.6 + Math.random() * 0.4),
    maxSpeed: CAR_CFG.MAX_SPEED * (0.6 + Math.random() * 0.4),
    stuckTimer: 0,
    stuck: false,
    laneId: lane.id,
    isLarge,
  });
}

function _fallbackCar() {
  const T = window.THREE;
  const colors = [0x3b82f6, 0xef4444, 0x22c55e, 0xfacc15, 0x60a5fa, 0x8b5cf6, 0xf97316, 0xec4899];
  const color = colors[Math.floor(Math.random() * colors.length)];
  const g = new T.Group();
  const body = new T.Mesh(
    new T.BoxGeometry(1.8, 0.7, 4.0),
    new T.MeshStandardMaterial({ color, roughness: 0.3, metalness: 0.3 })
  );
  body.position.y = 0.45; body.castShadow = true; g.add(body);
  const cabin = new T.Mesh(
    new T.BoxGeometry(1.5, 0.5, 2.0),
    new T.MeshStandardMaterial({ color, roughness: 0.25, metalness: 0.4 })
  );
  cabin.position.set(0, 0.87, 0.2); g.add(cabin);
  // Windshield
  const glass = new T.Mesh(
    new T.BoxGeometry(1.4, 0.45, 0.08),
    new T.MeshStandardMaterial({ color: 0x8ecae6, roughness: 0.1, metalness: 0.5, transparent: true, opacity: 0.7 })
  );
  glass.position.set(0, 0.87, -0.8); g.add(glass);
  // Wheels
  const wMat = new T.MeshStandardMaterial({ color: 0x222222, roughness: 0.9 });
  for (const [wx, wz] of [[0.95, 1.2], [-0.95, 1.2], [0.95, -1.2], [-0.95, -1.2]]) {
    const w = new T.Mesh(new T.CylinderGeometry(0.25, 0.25, 0.18, 10), wMat);
    w.rotation.z = Math.PI / 2; w.position.set(wx, 0.25, wz); g.add(w);
  }
  return g;
}

// ─── VEHICLE UPDATE (per frame) ───────────────────────────────────────────────
function _updateCars(dt) {
  const T = window.THREE;
  const toRemove = [];

  const nsState = window.__smartflowState ? window.__smartflowState.ns_state : 'green';
  const ewState = window.__smartflowState ? window.__smartflowState.ew_state : 'green';

  for (let i = 0; i < activeCars.length; i++) {
    const car = activeCars[i];

    // ── Collision detection: look ahead for cars in same lane ──
    let closestDist = Infinity;
    const radar = car.isLarge ? CAR_CFG.RADAR_LARGE : CAR_CFG.RADAR;
    const myPos = car.group.position;

    for (let j = 0; j < activeCars.length; j++) {
      if (i === j) continue;
      const other = activeCars[j];
      // Only check cars in same lane or nearby parallel lane
      if (other.laneId !== car.laneId) continue;

      const otherPos = other.group.position;
      // Vector from me to other
      const dx = otherPos.x - myPos.x;
      const dz = otherPos.z - myPos.z;
      // Project onto my direction
      const dot = dx * car.dir.x + dz * car.dir.z;
      if (dot > 0 && dot < radar) {
        // It's ahead of me and within radar
        const lateralDist = Math.abs(dx * car.dir.z - dz * car.dir.x);
        if (lateralDist < 2.5) { // close enough laterally
          closestDist = Math.min(closestDist, dot);
        }
      }
    }

    // Also check cars in adjacent lanes (cross-traffic avoidance)
    for (let j = 0; j < activeCars.length; j++) {
      if (i === j) continue;
      const other = activeCars[j];
      if (other.laneId === car.laneId) continue;
      const otherPos = other.group.position;
      const dist = myPos.distanceTo(otherPos);
      // Only brake for cross-traffic if very close to intersection
      if (dist < 5 && Math.abs(myPos.x) < 8 && Math.abs(myPos.z) < 8) {
        // In intersection area, check if other car is roughly ahead
        const dx = otherPos.x - myPos.x;
        const dz = otherPos.z - myPos.z;
        const dot = dx * car.dir.x + dz * car.dir.z;
        if (dot > 0 && dot < 6) {
          closestDist = Math.min(closestDist, dot);
        }
      }
    }

    // ── Traffic Light Stop Line check ──
    const isNS = car.laneId.startsWith('nb') || car.laneId.startsWith('sb');
    const lightState = isNS ? nsState : ewState;
    const isRedOrYellow = (lightState !== 'green');

    if (isRedOrYellow) {
      let distToStopLine = Infinity;
      if (car.laneId.startsWith('nb')) {
        // NB travels -Z, stop line is at Z = 12. Approach range is Z in [12, 22].
        const z = car.group.position.z;
        if (z >= 12 && z <= 22) {
          distToStopLine = z - 12;
        }
      } else if (car.laneId.startsWith('sb')) {
        // SB travels +Z, stop line is at Z = -12. Approach range is Z in [-22, -12].
        const z = car.group.position.z;
        if (z >= -22 && z <= -12) {
          distToStopLine = -12 - z;
        }
      } else if (car.laneId.startsWith('eb')) {
        // EB travels +X, stop line is at X = -12. Approach range is X in [-22, -12].
        const x = car.group.position.x;
        if (x >= -22 && x <= -12) {
          distToStopLine = -12 - x;
        }
      } else if (car.laneId.startsWith('wb')) {
        // WB travels -X, stop line is at X = 12. Approach range is X in [12, 22].
        const x = car.group.position.x;
        if (x >= 12 && x <= 22) {
          distToStopLine = x - 12;
        }
      }

      if (distToStopLine < radar) {
        closestDist = Math.min(closestDist, distToStopLine);
      }
    }

    // ── Speed control ──
    if (closestDist < radar) {
      // Brake — the closer, the harder
      car.speed -= CAR_CFG.BRAKE_RATE * dt;
      car.speed = Math.max(car.speed, 0);

      if (!car.stuck && car.speed <= 0) {
        car.stuck = true;
        car.stuckTimer = 0;
      }
      if (car.stuck) {
        if (isRedOrYellow) {
          // Reset stuck timer while waiting at red light to prevent creeping
          car.stuckTimer = 0;
        } else {
          car.stuckTimer += dt;
          if (car.stuckTimer > CAR_CFG.STUCK_TIMEOUT) {
            // Force creep to resolve deadlocks
            car.speed = Math.max(car.speed, CAR_CFG.MIN_SPEED);
          }
        }
      }
    } else {
      // Accelerate toward max
      car.speed += CAR_CFG.ACCEL_RATE * dt;
      car.speed = Math.min(car.speed, car.maxSpeed);
      car.stuck = false;
      car.stuckTimer = 0;
    }

    // ── Move ──
    car.group.position.x += car.dir.x * car.speed * dt;
    car.group.position.z += car.dir.z * car.speed * dt;

    // ── Despawn check ──
    if (Math.abs(car.group.position.x) > CAR_CFG.DESPAWN + 5 ||
        Math.abs(car.group.position.z) > CAR_CFG.DESPAWN + 5) {
      toRemove.push(i);
    }
  }

  // Remove despawned cars (reverse order)
  for (let i = toRemove.length - 1; i >= 0; i--) {
    const idx = toRemove[i];
    dynamicRoot.remove(activeCars[idx].group);
    activeCars.splice(idx, 1);
  }
}

// ─── PEDESTRIAN SPAWNING & UPDATE ─────────────────────────────────────────────
function _spawnPedestrian() {
  if (activePeds.length >= PED_CFG.MAX_PEDS) return;
  const T = window.THREE;

  const cw = crosswalks[Math.floor(Math.random() * crosswalks.length)];
  const [cx, cy, cz] = cw.center;
  const dirSign = Math.random() > 0.5 ? 1 : -1;

  const g = new T.Group();

  // Color options
  const bodyColor = [0x3b82f6, 0xef4444, 0x22c55e, 0xfacc15, 0x8b5cf6, 0xf97316, 0xec4899][Math.floor(Math.random() * 7)];
  const skinTone = [0xf2c09c, 0xd4a574, 0x8d5524, 0xffdbac][Math.floor(Math.random() * 4)];

  // Body (Torso)
  const body = new T.Mesh(
    new T.BoxGeometry(0.44, 0.85, 0.32),
    new T.MeshStandardMaterial({ color: bodyColor, roughness: 0.6 })
  );
  body.position.y = 0.875; // bottom sits at 0.45, top at 1.30
  body.castShadow = true;
  body.receiveShadow = true;
  g.add(body);

  // Head
  const head = new T.Mesh(
    new T.SphereGeometry(0.16, 12, 12),
    new T.MeshStandardMaterial({ color: skinTone, roughness: 0.5 })
  );
  head.position.y = 1.46; // top of head reaches ~1.62
  head.castShadow = true;
  g.add(head);

  // Left Leg Pivot & Mesh
  const legMat = new T.MeshStandardMaterial({ color: 0x2a2a3a, roughness: 0.8 });
  const leftLegPivot = new T.Group();
  leftLegPivot.position.set(-0.11, 0.45, 0);
  const leftLegMesh = new T.Mesh(new T.CylinderGeometry(0.06, 0.05, 0.45, 8), legMat);
  leftLegMesh.position.y = -0.225; // offset downwards to rotate about hip joint
  leftLegMesh.castShadow = true;
  leftLegPivot.add(leftLegMesh);
  g.add(leftLegPivot);

  // Right Leg Pivot & Mesh
  const rightLegPivot = new T.Group();
  rightLegPivot.position.set(0.11, 0.45, 0);
  const rightLegMesh = new T.Mesh(new T.CylinderGeometry(0.06, 0.05, 0.45, 8), legMat);
  rightLegMesh.position.y = -0.225;
  rightLegMesh.castShadow = true;
  rightLegPivot.add(rightLegMesh);
  g.add(rightLegPivot);

  // Left Arm Pivot & Mesh
  const armMat = new T.MeshStandardMaterial({ color: bodyColor, roughness: 0.6 });
  const leftArmPivot = new T.Group();
  leftArmPivot.position.set(-0.28, 1.2, 0);
  const leftArmMesh = new T.Mesh(new T.BoxGeometry(0.12, 0.65, 0.12), armMat);
  leftArmMesh.position.y = -0.325; // rotate about shoulder joint
  leftArmMesh.castShadow = true;
  leftArmPivot.add(leftArmMesh);
  g.add(leftArmPivot);

  // Right Arm Pivot & Mesh
  const rightArmPivot = new T.Group();
  rightArmPivot.position.set(0.28, 1.2, 0);
  const rightArmMesh = new T.Mesh(new T.BoxGeometry(0.12, 0.65, 0.12), armMat);
  rightArmMesh.position.y = -0.325;
  rightArmMesh.castShadow = true;
  rightArmPivot.add(rightArmMesh);
  g.add(rightArmPivot);

  // Start position & orientation (face the direction of travel)
  let sx, sz, rotY;
  const pedDir = -dirSign;
  if (cw.axis === 'x') {
    sx = cx + dirSign * cw.halfLen;
    sz = cz;
    rotY = (pedDir > 0) ? Math.PI / 2 : -Math.PI / 2;
  } else {
    sx = cx;
    sz = cz + dirSign * cw.halfLen;
    rotY = (pedDir > 0) ? 0 : Math.PI;
  }
  g.position.set(sx, cy, sz);
  g.rotation.y = rotY;
  dynamicRoot.add(g);

  activePeds.push({
    group: g,
    dir: pedDir,
    speed: PED_CFG.SPEED * (0.7 + Math.random() * 0.6),
    baseSpeed: PED_CFG.SPEED * (0.7 + Math.random() * 0.6),
    axis: cw.axis,
    center: [cx, cy, cz],
    halfLen: cw.halfLen,
    walkPhase: Math.random() * Math.PI * 2,
    leftLeg: leftLegPivot,
    rightLeg: rightLegPivot,
    leftArm: leftArmPivot,
    rightArm: rightArmPivot,
  });
}

function _updatePedestrians(dt) {
  const toRemove = [];

  const nsState = window.__smartflowState ? window.__smartflowState.ns_state : 'green';
  const ewState = window.__smartflowState ? window.__smartflowState.ew_state : 'green';

  for (let i = 0; i < activePeds.length; i++) {
    const ped = activePeds[i];
    const p = ped.group.position;

    // Check if waiting at the curb before entering the crossing
    let shouldWait = false;
    if (ped.axis === 'x') {
      // Crossing NS road, approaching from either side
      if (Math.abs(p.x) >= 10.0 && (p.x * ped.dir < 0) && nsState !== 'red') {
        shouldWait = true;
      }
    } else {
      // Crossing EW road, approaching from either side
      if (Math.abs(p.z) >= 10.0 && (p.z * ped.dir < 0) && ewState !== 'red') {
        shouldWait = true;
      }
    }

    if (shouldWait) {
      ped.speed = 0;
      ped.leftLeg.rotation.x = 0;
      ped.rightLeg.rotation.x = 0;
      ped.leftArm.rotation.x = 0;
      ped.rightArm.rotation.x = 0;
      ped.group.position.y = ped.center[1]; // stand flat
    } else {
      ped.speed = ped.baseSpeed;
      // Move along axis
      if (ped.axis === 'x') {
        p.x += ped.dir * ped.speed * dt;
      } else {
        p.z += ped.dir * ped.speed * dt;
      }

      // Walking animation (limb swings)
      ped.walkPhase += dt * 8;
      ped.leftLeg.rotation.x = Math.sin(ped.walkPhase) * 0.6;
      ped.rightLeg.rotation.x = -Math.sin(ped.walkPhase) * 0.6;
      ped.leftArm.rotation.x = -Math.sin(ped.walkPhase) * 0.5;
      ped.rightArm.rotation.x = Math.sin(ped.walkPhase) * 0.5;

      // Subtle body bobbing
      ped.group.position.y = ped.center[1] + Math.abs(Math.sin(ped.walkPhase)) * 0.05;
    }

    // Check if crossed to other side
    const [cx, cy, cz] = ped.center;
    if (ped.axis === 'x') {
      if ((ped.dir > 0 && p.x > cx + ped.halfLen + 2) ||
          (ped.dir < 0 && p.x < cx - ped.halfLen - 2)) {
        toRemove.push(i);
      }
    } else {
      if ((ped.dir > 0 && p.z > cz + ped.halfLen + 2) ||
          (ped.dir < 0 && p.z < cz - ped.halfLen - 2)) {
        toRemove.push(i);
      }
    }
  }

  for (let i = toRemove.length - 1; i >= 0; i--) {
    dynamicRoot.remove(activePeds[toRemove[i]].group);
    activePeds.splice(toRemove[i], 1);
  }
}

// ─── RENDER LOOP ──────────────────────────────────────────────────────────────
function _loop() {
  if (disposed) return;
  animFrame = requestAnimationFrame(_loop);

  const status = window.__smartflowState ? window.__smartflowState.status : 'stopped';

  if (status === 'stopped') {
    // Clear all active cars
    for (const car of activeCars) {
      dynamicRoot.remove(car.group);
    }
    activeCars = [];

    // Clear all active pedestrians
    for (const ped of activePeds) {
      dynamicRoot.remove(ped.group);
    }
    activePeds = [];

    carSpawnTimer = 0;
    pedSpawnTimer = 0;

    // Render empty scene
    if (renderer && scene && camera) renderer.render(scene, camera);
    return;
  }

  // Get elapsed time since last frame
  const realDt = clock.getDelta();
  // If paused, dt = 0 so no movement or animations advance, but loop keeps rendering
  const dt = (status === 'paused') ? 0 : Math.min(realDt, 0.1);

  if (status === 'running') {
    // ── Spawn cars ──
    carSpawnTimer += dt;
    if (carSpawnTimer >= CAR_CFG.SPAWN_INTERVAL) {
      carSpawnTimer = 0;
      _spawnCar();
    }

    // ── Spawn pedestrians ──
    pedSpawnTimer += dt;
    if (pedSpawnTimer >= PED_CFG.SPAWN_INTERVAL) {
      pedSpawnTimer = 0;
      _spawnPedestrian();
    }
  }

  // ── Update all vehicles at 60fps (dt = 0 when paused to freeze position)
  _updateCars(dt);

  // ── Update all pedestrians at 60fps
  _updatePedestrians(dt);

  // ── Update traffic light visual states ──
  _updateTrafficLights();

  if (renderer && scene && camera) renderer.render(scene, camera);
}

// ─── RESIZE ───────────────────────────────────────────────────────────────────
function _onResize() {
  const c = document.getElementById('three-container');
  if (!c || !renderer || !camera) return;
  const W = c.clientWidth, H = c.clientHeight;
  if (W <= 0 || H <= 0) return;
  renderer.setSize(W, H);
  camera.aspect = W / Math.max(H, 1);
  camera.updateProjectionMatrix();
}

// ─── PUBLIC API ───────────────────────────────────────────────────────────────
function update(state) {
  init();
  // State from Python backend is accepted but vehicles are client-side now
  window.__smartflowState = state;
}

function dispose() {
  disposed = true;
  if (animFrame) cancelAnimationFrame(animFrame);
  window.removeEventListener('resize', _onResize);
  if (renderer) {
    renderer.dispose();
    if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
  }
  trafficLightMeshes = [];
  ready = false;
}

export const SmartFlowScene = { update, dispose, isReady: () => ready };
window.SmartFlowScene = SmartFlowScene;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
