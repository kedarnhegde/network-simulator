from __future__ import annotations
import asyncio
from typing import List, Optional
from .models import Node, Position
from .engine import Engine

from .mac import Mac
from .types import Packet, MacConfig

class Store:
    def __init__(self):
        self.nodes: List[Node] = []
        self.logs = []  # DeliveryLog list (empty in PR1)
        self.running: bool = False
        self.engine = Engine()
        self.mac = Mac(seed=123, cfg=MacConfig())  
        self._next_id = 1
        self._next_seq = 1
        self._task: Optional[asyncio.Task] = None
        self._accum = 0.0  # for slot timing

    def add_node(self, role: str, phy: str, x: float, y: float) -> int:
        nid = self._next_id; self._next_id += 1
        node = Node(id=nid, role=role, phy=phy, pos=Position(x, y), is_broker=(role=="broker"))
        self.nodes.append(node)
        kind = "BLE" if phy == "BLE" else ("WiFi" if phy == "WiFi" else "Zigbee")
        self.mac.add_node(node_id=nid, kind=kind)
        return nid

    def remove_node(self, nid: int):
        self.nodes = [n for n in self.nodes if n.id != nid]

    def reset(self):
        self.nodes.clear()
        self.logs.clear()
        self.engine = Engine()
        self.mac = Mac(seed=123, cfg=MacConfig())
        self._next_id = 1
        self._next_seq = 1
        self.running = False
        self._accum = 0.0
    
    def enqueue(self, src_id: int, dst_id: int, n: int = 1, size: int = 100, kind: str = "WiFi") -> int:
        ok = 0
        for _ in range(n):
            if src_id not in [x.id for x in self.nodes]: break
            if dst_id not in [x.id for x in self.nodes]: break
            pkt = Packet(src_id=src_id, dst_id=dst_id, size_bytes=size, kind=kind, seq=self._next_seq, t_created=self.engine.now)
            self._next_seq += 1
            if self.mac.enqueue(pkt):
                ok += 1
        return ok

    async def loop(self):
        # basic discrete time loop
        dt = 0.02
        slot_s = self.mac.cfg.slot_ms / 1000.0
        while True:
            if self.running:
                self.engine.tick(self.nodes, dt)
                self._accum += dt
                while self._accum >= slot_s:
                    self.mac.tick()
                    self._accum -= slot_s
            await asyncio.sleep(dt)

store = Store()
