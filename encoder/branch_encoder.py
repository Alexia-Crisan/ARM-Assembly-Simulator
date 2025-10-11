"""
Branch (B): cond|101|offset24
"""

from typing import Dict
from .helpers import register_to_number, encode_immediate_value, COND_ALWAYS

def encode_branch(label: str, current_place: int, labels: Dict[str, int]) -> int:
    if label not in labels:
        raise ValueError(f"Unknown label: {label}")
    
    target = labels[label]

    offset = (target - (current_place + 8)) >> 2
 
    if not (- (1 << 23) <= offset < (1 << 23)):
        raise ValueError("Branch offset out of range")
    
    offset24 = offset & 0xFFFFFF
    machine_instruction = COND_ALWAYS | (0b101 << 25) | offset24
    return machine_instruction