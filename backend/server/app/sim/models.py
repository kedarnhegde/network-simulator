from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Set, List, Dict

Role = Literal["sensor", "subscriber", "mobile", "broker"]
PHYType = Literal["WiFi", "BLE"]

@dataclass
class Position:
    x: float
    y: float

@dataclass
class Message:
    id: str
    topic: str
    payload_bytes: int
    qos: int  # 0 or 1
    t_created: float
    from_id: int
    dup: bool = False

@dataclass
class DeliveryLog:
    id: str
    topic: str
    from_id: int
    to_id: int
    t_send: float
    t_recv: float
    latency: float
    dup: bool
    success: bool

@dataclass
class Node:
    id: int
    role: Role
    phy: PHYType
    pos: Position
    energy: float = 100.0
    awake: bool = True
    sleep_ratio: float = 0.2
    subscribed_topics: Set[str] = field(default_factory=set)
    is_broker: bool = False

# ---- API schemas (pydantic) ----
from pydantic import BaseModel, Field

class NodeCreate(BaseModel):
    role: Role
    phy: PHYType
    x: float = Field(ge=0)
    y: float = Field(ge=0)

class NodeView(BaseModel):
    id: int
    role: Role
    phy: PHYType
    x: float
    y: float
    energy: float
    awake: bool
    sleepRatio: float
    isBroker: bool

class MetricsView(BaseModel):
    now: float
    pdr: float
    avgLatencyMs: float
    delivered: int
    duplicates: int

class RouteEntryView(BaseModel):
    dest: int
    nextHop: int
    metric: int

class RoutingTableView(BaseModel):
    nodeId: int
    routes: List[RouteEntryView]
