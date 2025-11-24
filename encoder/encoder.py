"""
- Data processing (ADD, SUB, MOV): cond|00|I|opcode|S|Rn|Rd|operand2
- Single data transfer (LDR, STR): cond|01|I|P|U|B|W|L|Rn|Rd|offset12
- Branch (B): cond|101|offset24
"""

from typing import Dict
from .data_processing_encoder import encode_data_processing_instruction
from .data_transfer_encoder import encode_load_store
from .branch_encoder import encode_branch
from .multiplication_set_encoder import encode_multiply_or_div_instruction
from .stack_set_encoder import encode_stack_instruction
from .system_instruction_encoder import encode_system_instruction
from .pseudo_instruction_encoder import encode__pseudo_instruction
from .helpers import OPCODES, BRANCH_COND_MAP

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

    if instruction in ["INC", "DEC", "CLR", "LSL", "LSR", "MOD", "SWAP", "SWP", "LOOP"]:
        return encode__pseudo_instruction(instruction, args, current_place, labels)
    if instruction in OPCODES:
        return encode_data_processing_instruction(instruction, args)
    if instruction in ("LDR", "STR"):
        return encode_load_store(instruction, args)
    if instruction.startswith("B") or instruction in ["JMS", "RET"]:  # any branch
        if instruction == "RET":
            return encode_branch(instruction, None, current_place, labels)
        cond = BRANCH_COND_MAP.get(instruction.upper(), "AL")
        if len(args) != 1 and instruction != "RET":
            raise ValueError(f"{instruction} takes a single label argument")
        return encode_branch(instruction, args[0], current_place, labels, cond)
    if instruction in ["MUL", "DIV"]:
        return encode_multiply_or_div_instruction(instruction, args)
    if instruction in ["PSH", "PUSH", "POP"]:
        return encode_stack_instruction(instruction, args)
    if instruction in ["HLT", "OUT", "INP"]:
        return encode_system_instruction(instruction, args)

    raise ValueError(f"Unsupported instruction in this encoder: {instruction}")