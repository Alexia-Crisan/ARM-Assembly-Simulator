"""
Block data transfer (PSH, POP): cond|100|P|U|S|W|L|Rn|register_list
"""

from .helpers import register_to_number, COND_ALWAYS

def encode_stack_instruction(instruction: str, parts: list) -> int:
    """
      PSH {Rlist}
      POP {Rlist}
    """
    rn = 13   # Base register = stack pointer (R13)

    reg_list_str = " ".join(parts).strip("{} ").replace(" ", ",")
    reg_names = [r.strip().upper() for r in reg_list_str.split(",") if r.strip()]
    reg_mask = 0
    
    for reg in reg_names:
        reg_num = register_to_number(reg)
        reg_mask |= (1 << reg_num)

    if instruction.upper() in ["PSH", "PUSH"]:
        P, U, S, W, L = 1, 0, 0, 1, 0
    elif instruction.upper() in ["POP"]:
        P, U, S, W, L = 1, 0, 0, 1, 1
    else:
        raise ValueError(f"Unsupported block transfer instruction: {instruction}")

    machine_instruction =  COND_ALWAYS | (0b100 << 25) | (P << 24) | (U << 23) | (S << 22) | (W << 21) | (L << 20) | (rn << 16) | reg_mask

    return machine_instruction
