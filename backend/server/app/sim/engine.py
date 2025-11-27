from __future__ import annotations
from typing import Dict, List, Optional
import math

from .models import Node, Position

# PHY profiles (tweak later)
PHY_PROFILES: Dict[str, dict] = {
    "WiFi": {"range": 55.0, "data_rate": 54_000, "idle_energy": 0.5,  "sleep_energy": 0.05},
    "BLE":  {"range": 15.0, "data_rate":  1_000, "idle_energy": 0.1, "sleep_energy": 0.01},
}

def dist(a: Position, b: Position) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)

def in_range(a: Node, b: Node) -> bool:
    ra = PHY_PROFILES[a.phy]["range"]
    rb = PHY_PROFILES[b.phy]["range"]
    return dist(a.pos, b.pos) <= min(ra, rb)

def energy_tick(n: Node, dt: float, sim_time: float):
    prof = PHY_PROFILES[n.phy]
    
    # Duty cycle: node sleeps based on sleep_ratio
    # Simple model: sleep for sleep_ratio fraction of time
    cycle_time = 1.0  # 1 second cycle
    time_in_cycle = sim_time % cycle_time
    n.awake = time_in_cycle > (cycle_time * n.sleep_ratio)
    
    n.energy -= (prof["idle_energy"] if n.awake else prof["sleep_energy"]) * dt
    if n.energy < 0:
        n.energy = 0

class Engine:
    def __init__(self):
        self.now: float = 0.0

    def tick(self, nodes: List[Node], dt: float):
        self.now += dt
        for n in nodes:
            energy_tick(n, dt, self.now)
