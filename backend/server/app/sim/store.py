from __future__ import annotations
import asyncio
from typing import List, Optional
from .models import Node, Position
from .engine import Engine

class Store:
    def __init__(self):
        self.nodes: List[Node] = []
        self.logs = []  # DeliveryLog list (empty in PR1)
        self.running: bool = False
        self.engine = Engine()
        self._next_id = 1
        self._task: Optional[asyncio.Task] = None

    def add_node(self, role: str, phy: str, x: float, y: float) -> int:
        nid = self._next_id; self._next_id += 1
        node = Node(id=nid, role=role, phy=phy, pos=Position(x, y), is_broker=(role=="broker"))
        self.nodes.append(node)
        return nid

    def remove_node(self, nid: int):
        self.nodes = [n for n in self.nodes if n.id != nid]

    def reset(self):
        self.nodes.clear()
        self.logs.clear()
        self.engine = Engine()
        self._next_id = 1
        self.running = False

    async def loop(self):
        # basic discrete time loop
        dt = 0.02
        while True:
            if self.running:
                self.engine.tick(self.nodes, dt)
            await asyncio.sleep(dt)

store = Store()
