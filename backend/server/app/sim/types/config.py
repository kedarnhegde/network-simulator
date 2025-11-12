from dataclasses import dataclass

@dataclass
class MacConfig:
    slot_ms: float = 10.0
    queue_capacity: int = 50
    cw_min: int = 16
    cw_max: int = 1024
    retry_limit: int = 7
    base_loss_prob: float = 0.01
    collision_losses: bool = True