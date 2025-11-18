"""
Minimal Network Layer Implementation
- Distance-vector routing (hop count metric)
- Periodic route advertisements
- Next-hop forwarding
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple
import math

@dataclass
class RouteEntry:
    """Single routing table entry"""
    dest: int           # Destination node ID
    next_hop: int       # Next hop to reach dest
    metric: int         # Hop count to destination
    seq: int = 0        # Sequence number (freshness)
    
@dataclass
class RoutingTable:
    """Node's routing table"""
    node_id: int
    routes: Dict[int, RouteEntry] = field(default_factory=dict)
    
    def get_next_hop(self, dest: int) -> Optional[int]:
        """Get next hop for destination, None if no route"""
        entry = self.routes.get(dest)
        return entry.next_hop if entry else None
    
    def update_route(self, dest: int, next_hop: int, metric: int, seq: int = 0) -> bool:
        """Update route if new route is better or fresher. Returns True if updated."""
        existing = self.routes.get(dest)
        
        # Always update if new destination
        if not existing:
            self.routes[dest] = RouteEntry(dest, next_hop, metric, seq)
            return True
        
        # Update if fresher sequence number
        if seq > existing.seq:
            self.routes[dest] = RouteEntry(dest, next_hop, metric, seq)
            return True
        
        # Update if same seq but better metric
        if seq == existing.seq and metric < existing.metric:
            self.routes[dest] = RouteEntry(dest, next_hop, metric, seq)
            return True
        
        return False
    
    def get_all_routes(self) -> Dict[int, Tuple[int, int]]:
        """Returns {dest: (next_hop, metric)} for all known routes"""
        return {dest: (r.next_hop, r.metric) for dest, r in self.routes.items()}

@dataclass 
class RouteAdvertisement:
    """Route advertisement packet (sent periodically)"""
    src: int                                    # Advertising node
    routes: Dict[int, int]                      # {dest: metric}
    seq: int = 0                                # Sequence number
    
@dataclass
class NetworkLayer:
    """
    Simple distance-vector network layer
    - Periodic route advertisements
    - Next-hop forwarding
    """
    routing_tables: Dict[int, RoutingTable] = field(default_factory=dict)
    route_ad_interval: float = 2.0              # Send route ads every 2 sec
    last_route_ad: float = 0.0
    seq_counter: Dict[int, int] = field(default_factory=dict)
    
    def init_node(self, node_id: int):
        """Initialize routing table for a node"""
        if node_id not in self.routing_tables:
            self.routing_tables[node_id] = RoutingTable(node_id)
            self.seq_counter[node_id] = 0
    
    def remove_node(self, node_id: int):
        """Remove node's routing state"""
        self.routing_tables.pop(node_id, None)
        self.seq_counter.pop(node_id, None)
        # Remove routes through this node from all other tables
        for table in self.routing_tables.values():
            to_remove = [dest for dest, entry in table.routes.items() 
                        if entry.next_hop == node_id]
            for dest in to_remove:
                table.routes.pop(dest)
    
    def get_next_hop(self, src: int, dest: int) -> Optional[int]:
        """Get next hop from src to dest, None if no route"""
        table = self.routing_tables.get(src)
        if not table:
            return None
        return table.get_next_hop(dest)
    
    def process_route_advertisement(self, ad: RouteAdvertisement, receiver_id: int, 
                                    neighbors: Set[int]) -> bool:
        """
        Process received route advertisement.
        Returns True if routing table changed.
        """
        if receiver_id not in self.routing_tables:
            return False
        
        table = self.routing_tables[receiver_id]
        changed = False
        
        # Add/update route to the advertising node (direct neighbor)
        if ad.src in neighbors:
            if table.update_route(ad.src, ad.src, metric=1, seq=ad.seq):
                changed = True
        
        # Update routes to destinations advertised by this neighbor
        for dest, metric in ad.routes.items():
            if dest == receiver_id:  # Don't route to self
                continue
            if ad.src in neighbors:  # Only trust advertisements from neighbors
                new_metric = metric + 1  # Add one hop
                if table.update_route(dest, next_hop=ad.src, metric=new_metric, seq=ad.seq):
                    changed = True
        
        return changed
    
    def generate_route_advertisement(self, node_id: int) -> RouteAdvertisement:
        """Generate route advertisement for a node"""
        table = self.routing_tables.get(node_id)
        if not table:
            return RouteAdvertisement(src=node_id, routes={}, seq=0)
        
        # Increment sequence number
        self.seq_counter[node_id] = self.seq_counter.get(node_id, 0) + 1
        seq = self.seq_counter[node_id]
        
        # Advertise all known routes
        routes = {dest: entry.metric for dest, entry in table.routes.items()}
        
        return RouteAdvertisement(src=node_id, routes=routes, seq=seq)
    
    def should_send_route_ad(self, now: float) -> bool:
        """Check if it's time to send periodic route advertisements"""
        if now - self.last_route_ad >= self.route_ad_interval:
            self.last_route_ad = now
            return True
        return False
    
    def get_routing_table(self, node_id: int) -> Dict[int, Tuple[int, int]]:
        """Get routing table for a node as {dest: (next_hop, metric)}"""
        table = self.routing_tables.get(node_id)
        if not table:
            return {}
        return table.get_all_routes()
