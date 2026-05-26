"""Simulation service — shared engine lifecycle manager.

Holds a single SimulationEngine instance accessible from any Dash callback.
"""

from typing import Optional
from simulation.engine import SimulationEngine

_engine: Optional[SimulationEngine] = None


def get_engine() -> SimulationEngine:
    global _engine
    if _engine is None:
        _engine = SimulationEngine(seed=42)
    return _engine


def reset_engine(seed: int = 42):
    global _engine
    _engine = SimulationEngine(seed=seed)


def start() -> str:
    get_engine().start()
    return get_engine().status


def pause() -> str:
    get_engine().pause()
    return get_engine().status


def resume() -> str:
    get_engine().resume()
    return get_engine().status


def stop() -> str:
    get_engine().stop()
    return get_engine().status


def reset() -> str:
    old = get_engine()
    reset_engine(seed=42)
    get_engine().configure(
        traffic_density=old.traffic_density,
        pedestrian_density=old.pedestrian_density,
        emergency_mode=old.emergency_mode,
    )
    return get_engine().status


def step(num_ticks: int = 1):
    get_engine().step(num_ticks)


def get_state() -> dict:
    return get_engine().to_dict()


def current_status() -> str:
    return get_engine().status


def configure(**kwargs):
    get_engine().configure(**kwargs)


def load_scenario(scenario_dict: dict):
    get_engine().configure_from_scenario(scenario_dict)
