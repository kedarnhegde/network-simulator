from dataclasses import dataclass

@dataclass
class Packet:
    src_id: int
    dst_id: int  # Final destination
    size_bytes: int
    kind: str
    seq: int = 0
    t_created: float = 0.0
    next_hop_id: int = 0  # MAC-level destination (for multi-hop)
    
    def __post_init__(self):
        if self.next_hop_id == 0:
            self.next_hop_id = self.dst_id  # Default to direct transmission