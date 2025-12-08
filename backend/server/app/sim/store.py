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
        self.mqtt_pending_deliveries: List[tuple] = []  # (subscriber_id, message, effective_qos) pending delivery
        self.mqtt_pending_pub_acks: List[tuple] = []  # (publisher_id, broker_id, msg_id) pending publisher ACKs
        self.mqtt_pending_sub_acks: List[tuple] = []  # (sub_id, broker_id, msg_id, pkt_id) pending subscriber ACKs
        self.mqtt_sub_acks_received: Dict[int, set] = {}  # msg_id -> set of sub_ids that ACKed
        self.mqtt_pending_broker_publish: List[tuple] = []  # (broker_id, message, pub_pkt_id) waiting for pub->broker to complete
        self.mobility_models: Dict[int, MobilityModel] = {}  # node_id -> MobilityModel
        self.mqtt_packets_in_flight: List[dict] = []  # MQTT packet animations
        self.mac_packets_in_flight: List[dict] = []  # MAC packet animations
        self.mqtt_ack_packets: List[dict] = []  # ACK packet animations
        self.reconnection_wave: List[tuple] = []  # (node_id, timestamp) for reconnection tracking
        self.topic_message_counts: Dict[str, int] = {}  # topic -> message count (for heatmap)
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
        
        # Add animation for forwarded hop
        src_node = next((n for n in self.nodes if n.id == current_hop), None)
        dst_node = next((n for n in self.nodes if n.id == next_hop), None)
        if src_node and dst_node:
            self.mac_packets_in_flight.append({
                'src_id': current_hop,
                'dst_id': next_hop,
                'src_x': src_node.pos.x,
                'src_y': src_node.pos.y,
                'dst_x': dst_node.pos.x,
                'dst_y': dst_node.pos.y,
                'progress': 0.0,
                'kind': pkt.kind,
                'seq': pkt.seq
            })

    def add_node(self, role: str, phy: str, x: float, y: float, mobile: bool = False, speed: float = 0.0, sleep_ratio: float = 0.2) -> int:
        nid = self._next_id; self._next_id += 1
        node = Node(id=nid, role=role, phy=phy, pos=Position(x, y), is_broker=(role=="broker"), mobile=mobile, speed=speed, sleep_ratio=sleep_ratio)
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
        if nid in self.mqtt_brokers:
            del self.mqtt_brokers[nid]
        if nid in self.mqtt_clients:
            del self.mqtt_clients[nid]
        if nid in self.mobility_models:
            del self.mobility_models[nid]
    
    def relocate_broker(self, old_broker_id: int, new_x: float, new_y: float) -> int:
        """Relocate broker to new position (simulates failover)"""
        old_broker = next((n for n in self.nodes if n.id == old_broker_id), None)
        if not old_broker or not old_broker.is_broker:
            return old_broker_id
        
        # Transfer broker state
        old_broker_obj = self.mqtt_brokers.get(old_broker_id)
        if old_broker_obj:
            # Update position
            old_broker.pos.x = new_x
            old_broker.pos.y = new_y
            
            # Trigger reconnection wave for all clients
            for client_id in self.mqtt_clients.keys():
                client = self.mqtt_clients[client_id]
                if self._check_range(old_broker_id, client_id):
                    if not client.connected:
                        client.reconnect()
                        self.reconnection_wave.append((client_id, self.engine.now))
                else:
                    client.connected = False
        
        return old_broker_id

    def reset(self):
        self.nodes.clear()
        self.logs.clear()
        self.engine = Engine()
        self.mac = Mac(seed=123, cfg=MacConfig(), range_checker=self._check_range, forward_callback=self._forward_packet)
        self.network = NetworkLayer()  # Reset network layer
        self.mqtt_brokers.clear()
        self.mqtt_clients.clear()
        self.mqtt_pending_deliveries.clear()
        self.mqtt_pending_pub_acks.clear()
        self.mqtt_pending_sub_acks.clear()
        self.mqtt_sub_acks_received.clear()
        self.mqtt_pending_broker_publish.clear()
        self.mobility_models.clear()
        self.mqtt_packets_in_flight.clear()
        self.mac_packets_in_flight.clear()
        self.mqtt_ack_packets.clear()
        self.reconnection_wave.clear()
        self.topic_message_counts.clear()
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
        
        # Add initial animation for first hop (one per packet)
        next_hop_node = next((x for x in self.nodes if x.id == next_hop), None)
        if next_hop_node:
            for i in range(n):
                self.mac_packets_in_flight.append({
                    'src_id': src_id,
                    'dst_id': next_hop,
                    'src_x': src_node.pos.x,
                    'src_y': src_node.pos.y,
                    'dst_x': next_hop_node.pos.x,
                    'dst_y': next_hop_node.pos.y,
                    'progress': i * 0.02,
                    'kind': kind,
                    'seq': self._next_seq + i
                })
        
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
                            receiver_neighbors = self.get_neighbors(neighbor_id)
                            self.network.process_route_advertisement(ad, neighbor_id, receiver_neighbors)
                
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
                    self.reconnection_wave.append((client_id, current_time))
            elif not in_range and client.connected:
                # Moved out of range - disconnect
                client.connected = False
                client.stats['disconnects'] += 1
        
        # Process pending MQTT deliveries
        remaining_deliveries = []
        for sub_id, msg, effective_qos in self.mqtt_pending_deliveries:
            if sub_id not in self.mqtt_clients:
                continue
            
            client = self.mqtt_clients[sub_id]
            broker_id = next(iter(self.mqtt_brokers.keys()), None)
            
            # Only deliver if client is connected
            if client.connected and broker_id:
                # Add packet animation
                broker_node = next((n for n in self.nodes if n.id == broker_id), None)
                client_node = next((n for n in self.nodes if n.id == sub_id), None)
                if broker_node and client_node:
                    pkt_id = f"{broker_id}-{sub_id}-{msg.msg_id}"
                    self.mqtt_packets_in_flight.append({
                        'id': pkt_id,
                        'src_id': broker_id,
                        'dst_id': sub_id,
                        'src_x': broker_node.pos.x,
                        'src_y': broker_node.pos.y,
                        'dst_x': client_node.pos.x,
                        'dst_y': client_node.pos.y,
                        'progress': 0.0,
                        'kind': broker_node.phy,
                        'topic': msg.topic,
                        'needs_ack': effective_qos == 1,
                        'msg_id': msg.msg_id
                    })
                
                ack_msg_id = client.receive_message(msg, effective_qos)
                if ack_msg_id and broker_id in self.mqtt_brokers:
                    # Queue ACK to send after packet arrives
                    self.mqtt_pending_sub_acks.append((sub_id, broker_id, ack_msg_id, pkt_id))
                
                # Track expected ACKs for this message
                if msg.msg_id not in self.mqtt_sub_acks_received:
                    self.mqtt_sub_acks_received[msg.msg_id] = set()
                if effective_qos == 1:
                    # Mark that we expect an ACK from this subscriber
                    pass  # Will be added when ACK arrives
                
                # Track topic message count
                self.topic_message_counts[msg.topic] = self.topic_message_counts.get(msg.topic, 0) + 1
            else:
                # Not connected - keep in queue for later
                remaining_deliveries.append((sub_id, msg, effective_qos))
        
        self.mqtt_pending_deliveries = remaining_deliveries
        
        # Update MQTT packet animations (faster)
        self.mqtt_packets_in_flight = [
            {**p, 'progress': p['progress'] + 0.1} 
            for p in self.mqtt_packets_in_flight 
            if p['progress'] < 1.0
        ]
        
        # Update MAC packet animations
        self.mac_packets_in_flight = [
            {**p, 'progress': p['progress'] + 0.025}
            for p in self.mac_packets_in_flight
            if p['progress'] < 1.0
        ]
        
        # Check for completed publisher->broker packets and trigger broker publish
        completed_pub_packets = {p['id'] for p in self.mqtt_packets_in_flight if p.get('is_publish') and p['progress'] >= 0.95}
        remaining_broker_publish = []
        for broker_id, message, pub_pkt_id in self.mqtt_pending_broker_publish:
            if pub_pkt_id in completed_pub_packets:
                # Publisher->broker packet arrived, now broker can forward to subscribers
                if broker_id in self.mqtt_brokers:
                    broker = self.mqtt_brokers[broker_id]
                    deliveries, _ = broker.publish(message)
                    self.mqtt_pending_deliveries.extend(deliveries)
            else:
                # Still waiting for publisher->broker packet
                remaining_broker_publish.append((broker_id, message, pub_pkt_id))
        
        self.mqtt_pending_broker_publish = remaining_broker_publish
        
        # Update ACK packet animations (faster)
        self.mqtt_ack_packets = [
            {**p, 'progress': p['progress'] + 0.1} 
            for p in self.mqtt_ack_packets 
            if p['progress'] < 1.0
        ]
        
        # Check for completed MQTT packets and send subscriber ACKs
        completed_packets = {p['id'] for p in self.mqtt_packets_in_flight if p['progress'] >= 0.95}
        remaining_sub_acks = []
        for sub_id, broker_id, msg_id, pkt_id in self.mqtt_pending_sub_acks:
            if pkt_id in completed_packets:
                # Packet arrived, send ACK
                sub_node = next((n for n in self.nodes if n.id == sub_id), None)
                broker_node = next((n for n in self.nodes if n.id == broker_id), None)
                if sub_node and broker_node:
                    self.mqtt_ack_packets.append({
                        'id': f"ack-{sub_id}-{broker_id}-{msg_id}",
                        'src_id': sub_id,
                        'dst_id': broker_id,
                        'src_x': sub_node.pos.x,
                        'src_y': sub_node.pos.y,
                        'dst_x': broker_node.pos.x,
                        'dst_y': broker_node.pos.y,
                        'progress': 0.0,
                        'kind': 'ACK',
                        'msg_id': msg_id,
                        'from_sub': True
                    })
                
                # Track that this subscriber ACKed
                if msg_id not in self.mqtt_sub_acks_received:
                    self.mqtt_sub_acks_received[msg_id] = set()
                if sub_id not in self.mqtt_sub_acks_received[msg_id]:
                    self.mqtt_sub_acks_received[msg_id].add(sub_id)
                
                # Broker receives ACK
                if broker_id in self.mqtt_brokers:
                    self.mqtt_brokers[broker_id].receive_ack(msg_id, sub_id)
            else:
                # Packet not arrived yet, keep waiting
                remaining_sub_acks.append((sub_id, broker_id, msg_id, pkt_id))
        
        self.mqtt_pending_sub_acks = remaining_sub_acks
        
        # Process pending publisher ACKs (only after all subscriber ACKs received)
        completed_sub_acks = {p['id'] for p in self.mqtt_ack_packets if p.get('from_sub') and p['progress'] >= 0.95}
        remaining_pub_acks = []
        for pub_id, broker_id, msg_id in self.mqtt_pending_pub_acks:
            if pub_id not in self.mqtt_clients:
                continue
            
            # Check if all subscriber ACKs for this message have arrived at broker
            all_sub_acks_arrived = False
            
            # Count how many QoS 1 subscribers need to ACK
            expected_sub_acks = [ack for ack in self.mqtt_pending_sub_acks if ack[2] == msg_id]
            
            if len(expected_sub_acks) == 0 and msg_id in self.mqtt_sub_acks_received:
                # All expected ACKs have been processed
                expected_acks = self.mqtt_sub_acks_received[msg_id]
                if len(expected_acks) > 0:
                    # Check if all ACK packets have completed
                    all_arrived = all(
                        f"ack-{sub_id}-{broker_id}-{msg_id}" in completed_sub_acks
                        for sub_id in expected_acks
                    )
                    if all_arrived:
                        all_sub_acks_arrived = True
                else:
                    # No QoS 1 subscribers, but need to wait for packets to arrive
                    # Check if all message packets have been delivered
                    msg_packets_done = all(
                        p['progress'] >= 0.95 
                        for p in self.mqtt_packets_in_flight 
                        if p.get('msg_id') == msg_id
                    )
                    if msg_packets_done:
                        all_sub_acks_arrived = True
            
            if all_sub_acks_arrived:
                # Check if publisher is in range
                if self._check_range(pub_id, broker_id):
                    # Send ACK animation
                    pub_node = next((n for n in self.nodes if n.id == pub_id), None)
                    broker_node = next((n for n in self.nodes if n.id == broker_id), None)
                    if pub_node and broker_node:
                        self.mqtt_ack_packets.append({
                            'id': f"ack-{broker_id}-{pub_id}-{msg_id}",
                            'src_id': broker_id,
                            'dst_id': pub_id,
                            'src_x': broker_node.pos.x,
                            'src_y': broker_node.pos.y,
                            'dst_x': pub_node.pos.x,
                            'dst_y': pub_node.pos.y,
                            'progress': 0.0,
                            'kind': 'ACK',
                            'msg_id': msg_id,
                            'from_sub': False
                        })
                    
                    # Increment publisher ACK count
                    client = self.mqtt_clients[pub_id]
                    client.stats['acks_sent'] += 1
                    
                    # Clean up tracking
                    if msg_id in self.mqtt_sub_acks_received:
                        del self.mqtt_sub_acks_received[msg_id]
                else:
                    # Out of range, keep in queue
                    remaining_pub_acks.append((pub_id, broker_id, msg_id))
            else:
                # Not all subscriber ACKs received yet, keep waiting
                remaining_pub_acks.append((pub_id, broker_id, msg_id))
        
        self.mqtt_pending_pub_acks = remaining_pub_acks
        
        for broker_id, broker in self.mqtt_brokers.items():
            # Process broker queue to reduce queue depth
            broker.process_queue(count=5)
            
            # Check for retransmissions (QoS 1)
            retransmissions = broker.check_retransmissions(current_time)
            for sub_id, dup_msg in retransmissions:
                # Add to pending deliveries for range checking
                self.mqtt_pending_deliveries.append((sub_id, dup_msg))

store = Store()
