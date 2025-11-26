from __future__ import annotations
import asyncio
from typing import List, Optional, Set, Dict
from .models import Node, Position
from .engine import Engine
import math

from .mac import Mac
from .types import Packet, MacConfig
from .network import NetworkLayer, RouteAdvertisement
from .mqtt import MqttBroker, MqttClient, MqttMessage
from .mobility import RandomWaypointMobility, GridMobility, MobilityModel

class Store:
    def __init__(self):
        self.nodes: List[Node] = []
        self.logs = []  # DeliveryLog list (empty in PR1)
        self.running: bool = False
        self.engine = Engine()
        self.mac = Mac(seed=123, cfg=MacConfig(), range_checker=self._check_range, forward_callback=self._forward_packet)  
        self.network = NetworkLayer()  # Network layer routing
        self.mqtt_brokers: Dict[int, MqttBroker] = {}  # node_id -> MqttBroker
        self.mqtt_clients: Dict[int, MqttClient] = {}  # node_id -> MqttClient
        self.mqtt_pending_deliveries: List[tuple] = []  # (subscriber_id, message) pending delivery
        self.mobility_models: Dict[int, MobilityModel] = {}  # node_id -> MobilityModel
        self._next_id = 1
        self._next_seq = 1
        self._next_msg_id = 1
        self._task: Optional[asyncio.Task] = None
        self._accum = 0.0  # for slot timing
        self._mqtt_accum = 0.0  # for MQTT processing
        self.bounds = (0, 0, 400, 233)  # Canvas bounds for mobility (matches 1200x700 canvas / 3 scale)
    
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

    def add_node(self, role: str, phy: str, x: float, y: float, mobile: bool = False, speed: float = 0.0) -> int:
        nid = self._next_id; self._next_id += 1
        node = Node(id=nid, role=role, phy=phy, pos=Position(x, y), is_broker=(role=="broker"), mobile=mobile, speed=speed)
        self.nodes.append(node)
        kind = "BLE" if phy == "BLE" else ("WiFi" if phy == "WiFi" else "Zigbee")
        self.mac.add_node(node_id=nid, kind=kind)
        self.network.init_node(nid)  # Initialize network layer routing
        
        # Initialize MQTT components
        if role == "broker":
            self.mqtt_brokers[nid] = MqttBroker(nid)
        elif role in ["publisher", "subscriber"]:
            self.mqtt_clients[nid] = MqttClient(nid, role)
        
        # Initialize mobility if mobile
        if mobile and speed > 0:
            # Use bounded mobility: nodes stay within 70 units of starting position
            # This ensures they go out of range (>55 for WiFi) and come back
            self.mobility_models[nid] = RandomWaypointMobility(
                nid, speed, pause_time=2.0, 
                max_radius=70.0, center_x=x, center_y=y
            )
        
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
        self.mqtt_brokers.clear()
        self.mqtt_clients.clear()
        self.mqtt_pending_deliveries.clear()
        self.mobility_models.clear()
        self._next_id = 1
        self._next_seq = 1
        self._next_msg_id = 1
        self.running = False
        self._accum = 0.0
        self._mqtt_accum = 0.0
    
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
        mqtt_interval = 0.1  # Process MQTT every 100ms
        
        while True:
            if self.running:
                # Update mobile node positions
                for node in self.nodes:
                    if node.mobile and node.id in self.mobility_models:
                        model = self.mobility_models[node.id]
                        new_x, new_y = model.update_position(node.pos.x, node.pos.y, dt, self.bounds)
                        node.pos.x = new_x
                        node.pos.y = new_y
                
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
                
                # MQTT layer: process messages and retransmissions
                self._mqtt_accum += dt
                if self._mqtt_accum >= mqtt_interval:
                    self._process_mqtt()
                    self._mqtt_accum = 0.0
            await asyncio.sleep(dt)
    
    def _process_mqtt(self):
        """Process MQTT messages and retransmissions"""
        current_time = self.engine.now
        
        # Check keep-alive for all clients
        for client_id, client in self.mqtt_clients.items():
            if not client.check_keep_alive(current_time):
                # Client disconnected, attempt reconnect
                if client.reconnect():
                    # Reconnected successfully
                    pass
        
        # Check connectivity for all MQTT clients (with hysteresis to prevent rapid toggling)
        for client_id, client in self.mqtt_clients.items():
            broker_id = next(iter(self.mqtt_brokers.keys()), None)
            if not broker_id:
                continue
            
            in_range = self._check_range(broker_id, client_id)
            
            # Only change state if it's different from current state
            if in_range and not client.connected:
                # Back in range - reconnect!
                if client.reconnect():
                    pass  # Reconnected successfully
            elif not in_range and client.connected:
                # Moved out of range - disconnect
                client.connected = False
                client.stats['disconnects'] += 1
        
        # Process pending MQTT deliveries
        remaining_deliveries = []
        for sub_id, msg in self.mqtt_pending_deliveries:
            if sub_id not in self.mqtt_clients:
                continue
            
            client = self.mqtt_clients[sub_id]
            
            # Only deliver if client is connected
            if client.connected:
                ack_msg_id = client.receive_message(msg)
                broker_id = next(iter(self.mqtt_brokers.keys()), None)
                if ack_msg_id and broker_id in self.mqtt_brokers:
                    self.mqtt_brokers[broker_id].receive_ack(ack_msg_id, sub_id)
            else:
                # Not connected - keep in queue for later
                remaining_deliveries.append((sub_id, msg))
        
        self.mqtt_pending_deliveries = remaining_deliveries
        
        for broker_id, broker in self.mqtt_brokers.items():
            # Check for retransmissions (QoS 1)
            retransmissions = broker.check_retransmissions(current_time)
            for sub_id, dup_msg in retransmissions:
                # Add to pending deliveries for range checking
                self.mqtt_pending_deliveries.append((sub_id, dup_msg))

store = Store()
