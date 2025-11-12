from dataclasses import dataclass

@dataclass
class Packet:
    src_id: int
    dst_id: int
    size_bytes: int
    kind: str
    seq: int = 0
    t_created: float = 0.0