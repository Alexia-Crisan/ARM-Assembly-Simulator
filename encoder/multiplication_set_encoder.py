"""
Multiply (MUL, DIV): cond | 000000 | A | S | Rd | Rn | Rs | 1001 | Rm
"""

from .helpers import register_to_number, COND_ALWAYS

def encode_multiply_or_div_instruction(instruction: str, parts: list) -> int:
    """
    MUL Rd, Rn, Rm
    MUL Rd, Rn    
    DIV Rd, Rn, Rm
    DIV Rd, Rn

    A = 0 for MUL, 1 for DIV
    S = 0 (no update flags)
    """

    if instruction in ["MUL"] : A = 0
    else: A = 1

    S = 0

    if len(parts) == 2: 
        rd = register_to_number(parts[0].rstrip(","))
        rm = rd
        rs = register_to_number(parts[1].rstrip(","))
        rn = 0
    elif len(parts) == 3:
        rd = register_to_number(parts[0].rstrip(","))
        rm = register_to_number(parts[1].rstrip(","))
        rs = register_to_number(parts[2].rstrip(","))
        rn = 0
    else:
        raise ValueError(f"Invalid number of operands for {instruction}")

    machine_instruction = COND_ALWAYS | (0b000000 << 22) | (A << 21) | (S << 20) | (rd << 16) | (rn << 12) | (rs << 8) | (0b1001 << 4) | rm

    return machine_instruction
