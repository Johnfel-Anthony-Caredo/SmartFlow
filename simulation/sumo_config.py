from pathlib import Path

try:
    from sumolib import checkBinary
except ImportError:  # pragma: no cover - handled at runtime
    checkBinary = None

ROOT = Path(__file__).resolve().parents[1]
SUMO_DIR = ROOT / "sumo" / "Tagum_1"
SUMO_CONFIG_PATH = SUMO_DIR / "tagum1.sumocfg"
SUMO_NET_PATH = SUMO_DIR / "tagum1.net.xml"
SUMO_ROUTE_PATH = SUMO_DIR / "tagum1.rou.xml"
SUMO_SCOPE_PATH = SUMO_DIR / "main_intersection_scope.json"
SUMO_STEP_LENGTH = 1.0

PHASE_SEQUENCE = (
    ("WEST_GREEN", 25.0),
    ("WEST_YELLOW", 10.0),
    ("EAST_GREEN", 25.0),
    ("EAST_YELLOW", 10.0),
    ("NS_GREEN", 35.0),
    ("NS_YELLOW", 10.0),
    ("PED_GREEN", 20.0),
    ("ALL_RED", 10.0),
)

CONTROLLED_TLS_IDS = ("J1",)

# Compatibility names used by the existing map renderer. Tagum_1 has one
# controlled 18-link traffic light, so "major" maps directly to J1.
MAJOR_TLS_IDS = CONTROLLED_TLS_IDS
MINOR_TLS_IDS = ()

TLS_STATE_MAP = {
    "WEST_GREEN": "rrrrrrrrrrGGGGrrrr",
    "WEST_YELLOW": "rrrrrrrrrryyyyrrrr",
    "EAST_GREEN": "rrrGGGGrrrrrrrrrrr",
    "EAST_YELLOW": "rrryyyyrrrrrrrrrrr",
    "NS_GREEN": "GGGrrrrGGGrrrrrrrr",
    "NS_YELLOW": "yyyrrrryyyrrrrrrrr",
    "PED_GREEN": "rrrrrrrrrrrrrrGGGG",
    "ALL_RED": "rrrrrrrrrrrrrrrrrr",
}

APPROACH_LANES = {
    "north": ("-E2_1",),
    "south": ("E3_1",),
    "east": ("-E1_1", "-E1_2"),
    "west": ("E0_1", "E0_2"),
}

DENSITY_SCALE = {
    "none": 0.0,
    "low": 0.5,
    "medium": 1.0,
    "high": 1.5,
    "heavy": 1.5,
}

VEHICLE_SAMPLE_LIMIT = 50
PEDESTRIAN_SAMPLE_LIMIT = 20
EVENT_LIMIT = 100
CHART_HISTORY_LIMIT = 30

PEDESTRIAN_SPAWN_INTERVALS = {
    "none": None,
    "low": 12.0,
    "medium": 8.0,
    "high": 5.0,
    "heavy": 4.0,
}

PEDESTRIAN_ROUTE_TEMPLATES = (
    {
        "name": "west_to_south",
        "from_edge": "E0",
        "to_edge": "-E3",
    },
    {
        "name": "west_to_east",
        "from_edge": "E0",
        "to_edge": "E1",
    },
    {
        "name": "north_to_south",
        "from_edge": "-E2",
        "to_edge": "-E3",
    },
    {
        "name": "east_to_west",
        "from_edge": "-E1",
        "to_edge": "-E0",
    },
    {
        "name": "south_to_north",
        "from_edge": "E3",
        "to_edge": "E2",
    },
)

DEFAULT_SCENARIO_NAME = "Tagum City - J1 Main Intersection"


def get_sumo_binary() -> str:
    if checkBinary is None:
        raise RuntimeError("sumolib is unavailable; cannot resolve the SUMO binary")
    return checkBinary("sumo")
