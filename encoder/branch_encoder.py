"""
Branch (B): cond|101|L|offset24
"""

from typing import Dict
from .helpers import CONDITION_CODES, COND_ALWAYS

def encode_branch(instruction: str, label: str, current_place: int, labels: Dict[str, int], cond: str = "AL") -> int:
    
    if instruction.upper() == "RET":
        # MOV PC, LR = cond|00|I|opcode|S|Rn|Rd|operand2
        I = 0
        opcode = 0b1101  # MOV
        S = 0
        rn = 0
        rd = 15  # PC
        rm = 14  # LR
        machine_instruction = COND_ALWAYS | (0 << 26) | (I << 25) | (opcode << 21) | (S << 20) | (rn << 16) | (rd << 12) | rm
        return machine_instruction 
    
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