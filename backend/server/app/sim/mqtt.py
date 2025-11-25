from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional
from collections import defaultdict
import time

@dataclass
class MqttMessage:
    """MQTT message with QoS support"""
    topic: str
    payload: str
    qos: int  # 0 or 1
    msg_id: int
    publisher_id: int
    timestamp: float = field(default_factory=time.time)
    dup: bool = False  # Duplicate flag for QoS 1 retransmissions
    retained: bool = False

@dataclass
class Subscription:
    """Client subscription to a topic"""
    client_id: int
    topic: str
    qos: int

@dataclass
class PendingAck:
    """Pending acknowledgment for QoS 1 messages"""
    msg_id: int
    subscriber_id: int
    message: MqttMessage
    retry_count: int = 0
    last_sent: float = field(default_factory=time.time)

class MqttBroker:
    """MQTT Broker implementation"""
    
    def __init__(self, broker_id: int):
        self.broker_id = broker_id
        self.subscriptions: Dict[str, Set[int]] = defaultdict(set)  # topic -> set of client_ids
        self.retained_messages: Dict[str, MqttMessage] = {}  # topic -> last retained message
        self.pending_acks: Dict[tuple, PendingAck] = {}  # (msg_id, subscriber_id) -> PendingAck
        self.message_queue: List[MqttMessage] = []  # Broker's message queue
        self.next_msg_id = 1
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_delivered': 0,
            'qos0_messages': 0,
            'qos1_messages': 0,
            'duplicates_sent': 0,
            'acks_received': 0,
            'queue_depth': 0
        }
    
    def subscribe(self, client_id: int, topic: str, qos: int = 0):
        """Client subscribes to a topic"""
        self.subscriptions[topic].add(client_id)
        
        # Send retained message if exists
        if topic in self.retained_messages:
            return [self.retained_messages[topic]]
        return []
    
    def unsubscribe(self, client_id: int, topic: str):
        """Client unsubscribes from a topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(client_id)
    
    def publish(self, message: MqttMessage) -> List[tuple]:
        """
        Broker receives a published message and routes to subscribers
        Returns list of (subscriber_id, message) tuples to deliver
        """
        self.stats['messages_received'] += 1
        self.message_queue.append(message)
        self.stats['queue_depth'] = len(self.message_queue)
        
        # Handle retained messages
        if message.retained:
            self.retained_messages[message.topic] = message
        
        # Find subscribers for this topic
        subscribers = self.subscriptions.get(message.topic, set())
        deliveries = []
        
        for sub_id in subscribers:
            if message.qos == 0:
                # QoS 0: Fire and forget
                self.stats['qos0_messages'] += 1
                deliveries.append((sub_id, message))
            elif message.qos == 1:
                # QoS 1: At least once - track for ACK
                self.stats['qos1_messages'] += 1
                key = (message.msg_id, sub_id)
                if key not in self.pending_acks:
                    self.pending_acks[key] = PendingAck(
                        msg_id=message.msg_id,
                        subscriber_id=sub_id,
                        message=message
                    )
                deliveries.append((sub_id, message))
        
        return deliveries
    
    def receive_ack(self, msg_id: int, subscriber_id: int):
        """Receive ACK for QoS 1 message"""
        key = (msg_id, subscriber_id)
        if key in self.pending_acks:
            del self.pending_acks[key]
            self.stats['acks_received'] += 1
    
    def check_retransmissions(self, current_time: float, timeout: float = 5.0) -> List[tuple]:
        """Check for QoS 1 messages that need retransmission"""
        retransmissions = []
        
        for key, pending in list(self.pending_acks.items()):
            if current_time - pending.last_sent > timeout:
                if pending.retry_count < 3:  # Max 3 retries
                    # Retransmit with DUP flag
                    dup_msg = MqttMessage(
                        topic=pending.message.topic,
                        payload=pending.message.payload,
                        qos=pending.message.qos,
                        msg_id=pending.message.msg_id,
                        publisher_id=pending.message.publisher_id,
                        timestamp=pending.message.timestamp,
                        dup=True,
                        retained=pending.message.retained
                    )
                    retransmissions.append((pending.subscriber_id, dup_msg))
                    pending.retry_count += 1
                    pending.last_sent = current_time
                    self.stats['duplicates_sent'] += 1
                else:
                    # Give up after 3 retries
                    del self.pending_acks[key]
        
        return retransmissions
    
    def process_queue(self) -> Optional[MqttMessage]:
        """Process one message from queue"""
        if self.message_queue:
            msg = self.message_queue.pop(0)
            self.stats['queue_depth'] = len(self.message_queue)
            self.stats['messages_delivered'] += 1
            return msg
        return None

class MqttClient:
    """MQTT Client (Publisher/Subscriber)"""
    
    def __init__(self, client_id: int, role: str):
        self.client_id = client_id
        self.role = role  # 'publisher' or 'subscriber'
        self.subscribed_topics: Set[str] = set()
        self.received_messages: List[MqttMessage] = []
        self.received_msg_ids: Set[int] = set()  # For DUP detection
        
        # Statistics
        self.stats = {
            'messages_published': 0,
            'messages_received': 0,
            'duplicates_received': 0,
            'acks_sent': 0
        }
    
    def publish_message(self, topic: str, payload: str, qos: int = 0, retained: bool = False, msg_id: int = 0) -> MqttMessage:
        """Create and publish a message"""
        message = MqttMessage(
            topic=topic,
            payload=payload,
            qos=qos,
            msg_id=msg_id,
            publisher_id=self.client_id,
            retained=retained
        )
        self.stats['messages_published'] += 1
        return message
    
    def receive_message(self, message: MqttMessage) -> Optional[int]:
        """
        Receive a message
        Returns msg_id if ACK needed (QoS 1), None otherwise
        """
        # Check for duplicate
        if message.msg_id in self.received_msg_ids:
            self.stats['duplicates_received'] += 1
            if message.qos == 1:
                # Still send ACK for duplicates
                self.stats['acks_sent'] += 1
                return message.msg_id
            return None
        
        # New message
        self.received_msg_ids.add(message.msg_id)
        self.received_messages.append(message)
        self.stats['messages_received'] += 1
        
        # Send ACK if QoS 1
        if message.qos == 1:
            self.stats['acks_sent'] += 1
            return message.msg_id
        
        return None
