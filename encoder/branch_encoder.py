"""
Branch (B): cond|101|L|offset24
"""

from typing import Dict
from .helpers import CONDITION_CODES

def encode_branch(instruction: str, label: str, current_place: int, labels: Dict[str, int], cond: str = "AL") -> int:
    
    if instruction == "RET":
        # MOV PC, LR = 0xE12FFF1E
        return 0xE12FFF1E
    
    if label not in labels:
        raise ValueError(f"Unknown label: {label}")
    
    instruction = instruction.upper()
    cond_bits = CONDITION_CODES.get(cond.upper(), CONDITION_CODES["AL"])
    
    target = labels[label]

    offset = (target - (current_place + 8)) >> 2
 
    if not (- (1 << 23) <= offset < (1 << 23)):
        raise ValueError("Branch offset out of range")
    
    if instruction in ["JMS", "BL"]:
        L = 1
    else:
        L = 0

    offset24 = offset & 0xFFFFFF

    machine_instruction = cond_bits | (0b101 << 25) | (L << 24) | offset24
    return machine_instruction