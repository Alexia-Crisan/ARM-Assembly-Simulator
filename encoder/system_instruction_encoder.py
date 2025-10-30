"""
System instructions (HLT, INP, OUT, NOP, etc.)
Encoding: 1111|opcode(3)|operand(25)
"""

from .helpers import register_to_number

def encode_system_instruction(instruction: str, parts: list) -> int:

    instruction = instruction.upper().strip()
    base = 0xF0000000  # system instruction prefix

    if instruction == "HLT":
        opcode = 0b000
        return base | (opcode << 25)

    elif instruction == "INP":
        opcode = 0b001
        
        if len(parts) != 1:
            raise ValueError("INP expects 1 operand (destination register)")
        rd = register_to_number(parts[0])

        return base | (opcode << 25) | (rd & 0xF)

    elif instruction == "OUT":
        opcode = 0b010

        joined = " ".join(parts)
        if "{" not in joined or "}" not in joined:
            raise ValueError("OUT expects register list in braces, e.g. OUT {R0, R1, R2}")

        reg_list_str = joined.strip("{} ").replace(" ", ",")
        reg_names = [r.strip().upper() for r in reg_list_str.split(",") if r.strip()]

        if not reg_names:
            raise ValueError("OUT expects a list of registers, e.g. OUT {R0, R1, R2}")

        reg_mask = 0
        for reg_name in reg_names:
            reg_mask |= 1 << register_to_number(reg_name)

        return base | (opcode << 25) | (reg_mask & 0x1FFFFFF)

    else:
        raise ValueError(f"Unknown system instruction: {instruction}")
