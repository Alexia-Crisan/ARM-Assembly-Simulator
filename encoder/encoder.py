"""
- Data processing (ADD, SUB, MOV): cond|00|I|opcode|S|Rn|Rd|operand2
- Single data transfer (LDR, STR): cond|01|I|P|U|B|W|L|Rn|Rd|offset12
- Branch (B): cond|101|offset24
"""

from typing import Dict
from data_processing_encoder import encode_data_processing_instruction
from data_transfer_encoder import encode_load_store
from branch_encoder import encode_branch

OPCODES = {
    "ADD": 0b0100 << 21, # ADD (addition), Example: ADD R0, R1, R2 -> R0 = R1 + R2
    "SUB": 0b0010 << 21, # SUB (subtract), Example: SUB R2, R0, R1 -> R2 = R0 - R1
    "MOV": 0b1101 << 21, # MOV (move / immediate load), Example: MOV R0, #5 -> R0 = 5
}

def register_to_number(reg: str) -> int: #R2 -> 2
    if not reg.upper().startswith("R"):
        raise ValueError(f"Expected register like Rnum, got: {reg}")
    return int(reg[1:])

# immediate values are stored in 12 bits instead of 32: |rot|immediate_value(8 bits)| -> |11..8|7..0|
# immediate_value_32_bits = ROR(immediate_value_8_bits, 2 * rotate), ROR = right rotate
def encode_immediate_value(immediate_value: int) -> int:
    if immediate_value < 0:
        immediate_value &= 0xFFFFFFFF

    if 0 <= immediate_value <= 0xFF: # fits in 8 bits
        return immediate_value  # rotate = 0, immediate_value_8_bits = immediate_value

    # try rotate right to make immediate_value fit in 8 bits
    for rot in range(1, 16):
        rotate = rot * 2
        val = ((immediate_value >> rotate) | ((immediate_value << (32 - rotate)) & 0xFFFFFFFF)) & 0xFFFFFFFF # rotate right by rotate
        if val <= 0xFF:
            return (rotate << 8) | (val & 0xFF)

    raise ValueError(f"Immediate 0x{immediate_value:X} cannot be encoded in ARM rotate form")

def encode_instruction(line: str, current_place: int, labels: Dict[str, int]) -> int:
    """
    Encode a single line into a 32-bit word. current_place is the byte address of this instruction.
    """

    parts = [p for p in line.replace(',', ' , ').split() if p != '']
    tokens = []
    i = 0

    while i < len(parts):
        
        t = parts[i]
        if t == ',':
            i += 1
            continue

        # combine memory tokens: [R0,#4]
        if t.startswith('['):
            j = i
            mem = parts[j]
            while not mem.endswith(']'):
                j += 1
                mem += parts[j]
            tokens.append(mem)
            i = j + 1
            continue
        tokens.append(t)
        i += 1

    if not tokens:
        raise ValueError("Empty instruction")

    instruction = tokens[0].upper()
    args = tokens[1:]

    if instruction in OPCODES:
        return encode_data_processing_instruction(instruction, args)
    if instruction in ("LDR", "STR"):
        return encode_load_store(instruction, args)
    if instruction == "B":
        if len(args) != 1:
            raise ValueError("B takes a single label argument")
        return encode_branch(args[0], current_place, labels)

    raise ValueError(f"Unsupported instruction in this encoder: {instruction}")