from pathlib import Path

try:
    from sumolib import checkBinary
except ImportError:  # pragma: no cover - handled at runtime
    checkBinary = None


SUMO_CONFIG_PATH = Path(__file__).resolve().parents[1] / "sumo" / "intersection_1" / "inter.sumocfg"
SUMO_STEP_LENGTH = 1.0

PHASE_SEQUENCE = (
    ("NS_GREEN", 82.0),
    ("NS_YELLOW", 3.0),
    ("ALL_RED", 5.0),
    ("EW_GREEN", 5.0),
    ("EW_YELLOW", 5.0),
)

MAJOR_TLS_IDS = (
    "7900968103",
    "7900968104",
)

MINOR_TLS_IDS = (
    "7900968105",
    "7900968106",
)

TLS_STATE_MAP = {
    "NS_GREEN": {
        "major": "GGGGr",
        "minor": "GGr",
    },
    "NS_YELLOW": {
        "major": "yyyyr",
        "minor": "yyr",
    },
    "ALL_RED": {
        "major": "rrrrr",
        "minor": "rrr",
    },
    "EW_GREEN": {
        "major": "rrrrG",
        "minor": "rrG",
    },
    "EW_YELLOW": {
        "major": "rrrrr",
        "minor": "rrr",
    },
}

APPROACH_LANES = {
    "north": ("180969633#0_0",),
    "south": ("-180970197#1_0",),
    "east": ("-1337657045#3_0", "-1337657045#3_1"),
    "west": ("1337657045#0_0", "1337657045#0_1"),
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
        "name": "west_to_north",
        "from_edge": "1337657045#0",
        "to_edge": "180969633#0",
    },
    {
        "name": "north_to_east",
        "from_edge": "180969633#0",
        "to_edge": "-1337657045#3",
    },
    {
        "name": "east_to_south",
        "from_edge": "-1337657045#3",
        "to_edge": "-180970197#1",
    },
    {
        "name": "south_to_west",
        "from_edge": "-180970197#1",
        "to_edge": "1337657045#0",
    },
)

DEFAULT_SCENARIO_NAME = "Tagum City - SUMO Intersection"


def get_sumo_binary() -> str:
    if checkBinary is None:
        raise RuntimeError("sumolib is unavailable; cannot resolve the SUMO binary")
    return checkBinary("sumo")
