from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Deque, Optional, Set, Tuple
from collections import deque
import random

from .types import Packet, MacConfig, MacKind

@dataclass
class TxQueue:
    """ 
    Transmit FIFO Queue for outgoing packets
    """
    capacity: int
    q: Deque[Packet] = field(default_factory=deque)
    drops: int = 0

    def enqueue(self, p: Packet) -> bool:               # methods used for transmit queue
        if len(self.q) >= self.capacity:
            self.drops += 1
            return False
        self.q.append(p)
        return True
    
    def peek(self) -> Optional[Packet]:
        return self.q[0] if self.q else None
    
    def pop(self) -> Optional[Packet]:
        return self.q.popleft() if self.q else None
    
@dataclass
class Channel:
    """
    Shared medium for slot for tracking transmission use and collisions
    """
    tx_in_slot: Dict[int, Packet] = field(default_factory=dict)

    def clear(self): self.tx_in_slot.clear()
    def is_busy(self) -> bool: return bool(self.tx_in_slot)
    def start_tx(self, nid: int, pkt: Packet): self.tx_in_slot[nid] = pkt           # marks node as transmitter
    def end_slot(self) -> Tuple[bool, Set[int]]:                                    # clears state and returns collisions (if any)
        nodes = set(self.tx_in_slot.keys())
        collision = len(nodes) > 1
        self.clear()
        return collision, nodes
        
@dataclass
class NodeMac:
    """
    Single Node MAC with queue, contention window, backoff, retry count, and ack handling
    """
    node_id: int
    kind: MacKind
    queue: TxQueue
    cw: int = 0                     # for CSMA/CA
    backoff: int = 0
    retry_count: int = 0
    awaiting_ack: Optional[Packet] = None

@dataclass
class MacMetrics:
    """""
    Tracking metrics for updating/evaluation
    """""
    enqueued: int = 0
    dequeued_ok: int = 0
    dequeued_fail: int = 0
    retries: int = 0
    collisions: int = 0
    duplicates: int = 0
    queue_drops: int = 0
    bytes_ok: int = 0
    rtt_ms_total: float = 0.0
    rtt_samples: int = 0
    pdr: float = 0.0

    def view(self):
        return { 
        "enqueued": self.enqueued,
        "dequeued_ok": self.dequeued_ok,
        "dequeued_fail": self.dequeued_fail,
        "retries": self.retries,
        "collisions": self.collisions,
        "duplicates": self.duplicates,
        "queue_drops": self.queue_drops,
        "bytes_ok": self.bytes_ok,
        "rtt_ms_total": self.rtt_ms_total,
        "rtt_samples": self.rtt_samples,
        "pdr": self.pdr,
        "avg_rtt": (self.rtt_ms_total / self.rtt_samples) if self.rtt_samples else None
        }

class Mac:
    """"
    Main MAC engine
    """
    def __init__(self, seed: int = 123, cfg: Optional[MacConfig] = None, range_checker=None, forward_callback=None):
        self.cfg = cfg or MacConfig()                               # initializer 
        self.rng = random.Random(seed)
        self.channel = Channel()
        self.nodes: Dict[int, NodeMac] = {}
        self.metrics = MacMetrics()
        self.seen: Set[Tuple[int, int, int]] = set()
        self.slot_index = 0
        self.range_checker = range_checker  # Callback to check if nodes are in range
        self.forward_callback = forward_callback  # Callback to forward packets at intermediate nodes

    def add_node(self, node_id: int, kind: MacKind = "WiFi"):
        if node_id in self.nodes: return                            # reguster node with empty TxQueue
        q = TxQueue(self.cfg.queue_capacity)
        self.nodes[node_id] = NodeMac(node_id=node_id, kind=kind, queue=q)

    def enqueue(self, pkt: Packet) -> bool:
        st = self.nodes[pkt.src_id]                                 # push packet to source node's TxQueue
        ok = st.queue.enqueue(pkt)
        if ok:
            self.metrics.enqueued += 1                              
            if st.cw == 0:
                st.cw = self.cfg.cw_min
                st.backoff = self.rng.randrange(st.cw)
            return True
        else:
            self.metrics.queue_drops += 1
            return False
        
    def tick(self):
        self.slot_index += 1                                        # move to next slot and advance channel state
        self.channel.clear()

        for st in self.nodes.values():
            if st.awaiting_ack is not None:                         # CSMA/CA per node
                continue
            head = st.queue.peek()
            if not head: continue

            if self.channel.is_busy():
                continue
            if st.backoff > 0:
                st.backoff -= 1
                continue
            self.channel.start_tx(st.node_id, head)
            st.awaiting_ack = head

        collision, tx_nodes = self.channel.end_slot()
        if collision: self.metrics.collisions += 1

        for nid in tx_nodes:                                        # resolve slot
            st = self.nodes[nid]
            pkt = st.awaiting_ack
            assert pkt is not None

            # Check if next hop is in range (for multi-hop)
            out_of_range = False
            if self.range_checker:
                out_of_range = not self.range_checker(pkt.src_id, pkt.next_hop_id)
            
            rand_loss = self.rng.random() < self.cfg.base_loss_prob
            failed = (collision and self.cfg.collision_losses) or rand_loss or out_of_range

            if failed:
                st.retry_count += 1
                self.metrics.retries += 1                           # increment/reset failure metrics
                if st.retry_count > self.cfg.retry_limit:
                    st.queue.pop()
                    self.metrics.dequeued_fail += 1
                    st.retry_count = 0
                    st.cw = self.cfg.cw_min
                else:
                    st.cw = min(self.cfg.cw_max, max(self.cfg.cw_min, st.cw *2))
                st.backoff= self.rng.randrange(st.cw)
                st.awaiting_ack = None
            else:
                self.delivered(st, pkt)
        
        sent = self.metrics.dequeued_ok + self.metrics.dequeued_fail
        self.metrics.pdr = (self.metrics.dequeued_ok / sent) if sent else 0.0

    def delivered(self, st: NodeMac, pkt: Packet):                  
        # Check if packet reached final destination or needs forwarding
        if pkt.next_hop_id == pkt.dst_id:
            # Reached final destination - check for duplicates
            key = (pkt.src_id, pkt.dst_id, pkt.seq)
            duplicate = key in self.seen
            if duplicate:
                self.metrics.duplicates += 1
            else:
                self.seen.add(key)
                self.metrics.dequeued_ok += 1
                self.metrics.bytes_ok += pkt.size_bytes
                now_ms = self.slot_index * self.cfg.slot_ms
                self.metrics.rtt_samples += 1
                self.metrics.rtt_ms_total += max(0.0, now_ms - pkt.t_created * 1000.0)
        elif self.forward_callback:
            # Intermediate hop - forward packet (not a duplicate, just forwarding)
            self.forward_callback(pkt)
        
        st.queue.pop()                                              # dequeue packet and reset backoff state
        st.retry_count = 0
        st.cw = self.cfg.cw_min
        st.backoff = self.rng.randrange(st.cw)
        st.awaiting_ack = None