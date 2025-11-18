from __future__ import annotations
import asyncio
from typing import List, Optional, Set
from .models import Node, Position
from .engine import Engine
import math

from .mac import Mac
from .types import Packet, MacConfig
from .network import NetworkLayer, RouteAdvertisement

class Store:
    def __init__(self):
        self.nodes: List[Node] = []
        self.logs = []  # DeliveryLog list (empty in PR1)
        self.running: bool = False
        self.engine = Engine()
        self.mac = Mac(seed=123, cfg=MacConfig())  
        self.network = NetworkLayer()  # Network layer routing
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
        self.network.init_node(nid)  # Initialize network layer routing
        return nid

    def remove_node(self, nid: int):
        self.nodes = [n for n in self.nodes if n.id != nid]
        self.network.remove_node(nid)  # Clean up routing state

    def reset(self):
        self.nodes.clear()
        self.logs.clear()
        self.engine = Engine()
        self.mac = Mac(seed=123, cfg=MacConfig())
        self.network = NetworkLayer()  # Reset network layer
        self._next_id = 1
        self._next_seq = 1
        self.running = False
        self._accum = 0.0
    
    def enqueue(self, src_id: int, dst_id: int, n: int = 1, size: int = 100, kind: str = "WiFi") -> int:
        """Enqueue packets with network layer routing"""
        ok = 0
        for _ in range(n):
            if src_id not in [x.id for x in self.nodes]: break
            if dst_id not in [x.id for x in self.nodes]: break
            
            # Check if we have a route to destination
            next_hop = self.network.get_next_hop(src_id, dst_id)
            if not next_hop and src_id != dst_id:
                # No route available yet - skip for now
                # (routes will be built via periodic advertisements)
                continue
            
            # If src == dst or we have a route, create packet
            pkt = Packet(src_id=src_id, dst_id=dst_id, size_bytes=size, kind=kind, seq=self._next_seq, t_created=self.engine.now)
            self._next_seq += 1
            if self.mac.enqueue(pkt):
                ok += 1
        return ok
    
    def get_neighbors(self, node_id: int) -> Set[int]:
        """Get set of neighbor node IDs in PHY range"""
        node = next((n for n in self.nodes if n.id == node_id), None)
        if not node:
            return set()
        
        neighbors = set()
        from .engine import in_range
        for other in self.nodes:
            if other.id != node_id and in_range(node, other):
                neighbors.add(other.id)
        return neighbors

    async def loop(self):
        # basic discrete time loop
        dt = 0.02
        slot_s = self.mac.cfg.slot_ms / 1000.0
        while True:
            if self.running:
                self.engine.tick(self.nodes, dt)
                
                # Network layer: periodic route advertisements
                if self.network.should_send_route_ad(self.engine.now):
                    for node in self.nodes:
                        # Each node broadcasts its routing table to neighbors
                        ad = self.network.generate_route_advertisement(node.id)
                        neighbors = self.get_neighbors(node.id)
                        
                        # All neighbors process the advertisement
                        for neighbor_id in neighbors:
                            self.network.process_route_advertisement(ad, neighbor_id, 
                                                                    self.get_neighbors(neighbor_id))
                
                # MAC layer slots
                self._accum += dt
                while self._accum >= slot_s:
                    self.mac.tick()
                    self._accum -= slot_s
            await asyncio.sleep(dt)

store = Store()
