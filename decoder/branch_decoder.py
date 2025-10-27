def decode_branch(instruction: int, regs: list, flags: dict):
    """
    Decode and execute all branches (B)
    """
    cond = (instruction >> 28) & 0xF
    offset24 = instruction & 0xFFFFFF

    if offset24 & (1 << 23):  
        offset24 -= 1 << 24
    target_address = regs[15] + 8 + (offset24 << 2)

    take_branch = False
    if cond == 0b0000:  # EQ
        take_branch = flags["Z"] == 1
    elif cond == 0b0001:  # NE
        take_branch = flags["Z"] == 0
    elif cond == 0b1010:  # GE
        take_branch = flags["N"] == flags["V"]
    elif cond == 0b1011:  # LT
        take_branch = flags["N"] != flags["V"]
    elif cond == 0b1110:  # AL
        take_branch = True

    if take_branch:
        regs[15] = target_address
    else:
        regs[15] += 4

def is_branch_instruction(instruction: int) -> bool:
    top3 = (instruction >> 25) & 0b111
    return top3 == 0b101 
