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
        self.mac = Mac(seed=123, cfg=MacConfig(), range_checker=self._check_range, forward_callback=self._forward_packet)  
        self.network = NetworkLayer()  # Network layer routing
        self._next_id = 1
        self._next_seq = 1
        self._task: Optional[asyncio.Task] = None
        self._accum = 0.0  # for slot timing
    
    def _check_range(self, src_id: int, dst_id: int) -> bool:
        """Check if two nodes are within PHY range of each other"""
        src = next((n for n in self.nodes if n.id == src_id), None)
        dst = next((n for n in self.nodes if n.id == dst_id), None)
        if not src or not dst:
            return False
        from .engine import in_range
        return in_range(src, dst)
    
    def _forward_packet(self, pkt: Packet):
        """Forward packet to next hop (multi-hop routing)"""
        current_hop = pkt.next_hop_id
        final_dest = pkt.dst_id
        
        # Get next hop from current node's routing table
        next_hop = self.network.get_next_hop(current_hop, final_dest)
        if not next_hop:
            # No route available, drop packet
            return
        
        # Check if next hop is reachable
        if not self._check_range(current_hop, next_hop):
            # Out of range, drop packet
            return
        
        # Create forwarded packet with current hop as new source for MAC layer
        forwarded_pkt = Packet(
            src_id=current_hop,  # Current hop becomes MAC source
            dst_id=pkt.dst_id,   # Keep final destination
            size_bytes=pkt.size_bytes,
            kind=pkt.kind,
            seq=pkt.seq,
            t_created=pkt.t_created,
            next_hop_id=next_hop  # Next hop in the route
        )
        
        # Enqueue at current hop for forwarding
        self.mac.enqueue(forwarded_pkt)

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
        self.mac = Mac(seed=123, cfg=MacConfig(), range_checker=self._check_range, forward_callback=self._forward_packet)
        self.network = NetworkLayer()  # Reset network layer
        self._next_id = 1
        self._next_seq = 1
        self.running = False
        self._accum = 0.0
    
    def enqueue(self, src_id: int, dst_id: int, n: int = 1, size: int = 100, kind: str = "WiFi") -> int:
        """Enqueue packets for MAC layer transmission"""
        ok = 0
        
        # Validate source and destination nodes exist
        src_node = next((x for x in self.nodes if x.id == src_id), None)
        dst_node = next((x for x in self.nodes if x.id == dst_id), None)
        if not src_node or not dst_node:
            return 0
        
        # Validate PHY type matches source node's PHY
        if src_node.phy != kind:
            # PHY mismatch - source node can't transmit this type
            return 0
        
        # Determine next hop for routing
        next_hop = self.network.get_next_hop(src_id, dst_id)
        if not next_hop:
            next_hop = dst_id  # Direct transmission
        
        # Check if source can reach next hop
        if not self._check_range(src_id, next_hop):
            return 0
        
        for _ in range(n):
            # Create packet with next_hop_id for MAC layer
            pkt = Packet(
                src_id=src_id, 
                dst_id=dst_id,  # Final destination
                size_bytes=size, 
                kind=kind, 
                seq=self._next_seq, 
                t_created=self.engine.now,
                next_hop_id=next_hop  # MAC destination
            )
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
