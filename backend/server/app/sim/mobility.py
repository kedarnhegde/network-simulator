from __future__ import annotations
import random
import math
from dataclasses import dataclass
from typing import Tuple

@dataclass
class Waypoint:
    """Target waypoint for mobile node"""
    x: float
    y: float

class MobilityModel:
    """Base mobility model"""
    
    def __init__(self, node_id: int, speed: float = 1.0):
        self.node_id = node_id
        self.speed = speed  # m/s
    
    def update_position(self, current_x: float, current_y: float, dt: float, bounds: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """Update position based on mobility model. Returns (new_x, new_y)"""
        return current_x, current_y

class RandomWaypointMobility(MobilityModel):
    """Random Waypoint mobility model"""
    
    def __init__(self, node_id: int, speed: float = 1.0, pause_time: float = 5.0, max_radius: float = None, center_x: float = None, center_y: float = None):
        super().__init__(node_id, speed)
        self.waypoint: Waypoint | None = None
        self.pause_time = pause_time
        self.pause_remaining = 0.0
        self.rng = random.Random(node_id)  # Deterministic per node
        self.max_radius = max_radius  # Max distance from center (None = unbounded)
        self.center_x = center_x  # Center point X
        self.center_y = center_y  # Center point Y
    
    def update_position(self, current_x: float, current_y: float, dt: float, bounds: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """
        Random Waypoint: Move to random waypoint, pause, pick new waypoint
        bounds: (min_x, min_y, max_x, max_y)
        """
        min_x, min_y, max_x, max_y = bounds
        
        # If paused, wait
        if self.pause_remaining > 0:
            self.pause_remaining -= dt
            return current_x, current_y
        
        # If no waypoint, pick one
        if self.waypoint is None:
            if self.max_radius and self.center_x is not None and self.center_y is not None:
                # Bounded: pick waypoint within radius of center
                angle = self.rng.uniform(0, 2 * math.pi)
                distance = self.rng.uniform(0, self.max_radius)
                wx = self.center_x + distance * math.cos(angle)
                wy = self.center_y + distance * math.sin(angle)
                # Keep within bounds
                wx = max(min_x, min(max_x, wx))
                wy = max(min_y, min(max_y, wy))
                self.waypoint = Waypoint(x=wx, y=wy)
            else:
                # Unbounded: pick anywhere
                self.waypoint = Waypoint(
                    x=self.rng.uniform(min_x, max_x),
                    y=self.rng.uniform(min_y, max_y)
                )
        
        # Move towards waypoint
        dx = self.waypoint.x - current_x
        dy = self.waypoint.y - current_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < self.speed * dt:
            # Reached waypoint
            new_x, new_y = self.waypoint.x, self.waypoint.y
            self.waypoint = None
            self.pause_remaining = self.pause_time
        else:
            # Move towards waypoint
            direction_x = dx / distance
            direction_y = dy / distance
            new_x = current_x + direction_x * self.speed * dt
            new_y = current_y + direction_y * self.speed * dt
        
        # Keep within bounds
        new_x = max(min_x, min(max_x, new_x))
        new_y = max(min_y, min(max_y, new_y))
        
        return new_x, new_y

class GridMobility(MobilityModel):
    """Grid-based mobility (moves in straight lines, turns at intersections)"""
    
    def __init__(self, node_id: int, speed: float = 1.0, grid_size: float = 50.0):
        super().__init__(node_id, speed)
        self.grid_size = grid_size
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])  # Right, Left, Down, Up
        self.rng = random.Random(node_id)
    
    def update_position(self, current_x: float, current_y: float, dt: float, bounds: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """
        Grid mobility: Move in current direction, change direction at grid intersections
        """
        min_x, min_y, max_x, max_y = bounds
        
        # Move in current direction
        new_x = current_x + self.direction[0] * self.speed * dt
        new_y = current_y + self.direction[1] * self.speed * dt
        
        # Check if hit boundary
        if new_x <= min_x or new_x >= max_x:
            self.direction = (self.rng.choice([-1, 1]) if self.direction[0] == 0 else 0,
                            self.rng.choice([-1, 1]) if self.direction[1] == 0 else 0)
            new_x = max(min_x, min(max_x, new_x))
        
        if new_y <= min_y or new_y >= max_y:
            self.direction = (self.rng.choice([-1, 1]) if self.direction[0] == 0 else 0,
                            self.rng.choice([-1, 1]) if self.direction[1] == 0 else 0)
            new_y = max(min_y, min(max_y, new_y))
        
        # Random direction change at grid intersections
        if abs(new_x % self.grid_size) < self.speed * dt or abs(new_y % self.grid_size) < self.speed * dt:
            if self.rng.random() < 0.1:  # 10% chance to change direction
                self.direction = self.rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        
        return new_x, new_y
