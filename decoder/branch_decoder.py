def decode_branch(instruction: int, regs: list, flags: dict):
    """
    Decode and execute all branches (B, BL / JMS)
    """
    cond = (instruction >> 28) & 0xF
    L = (instruction >> 24) & 1
    offset24 = instruction & 0xFFFFFF

    if offset24 & (1 << 23):
        offset24 -= 1 << 24

    target_address = (regs[15] + 8 + (offset24 << 2)) & 0xFFFFFFFF

    take_branch = False
    if cond == 0b0000:      # EQ
        take_branch = flags["Z"] == 1
    elif cond == 0b0001:    # NE
        take_branch = flags["Z"] == 0
    elif cond == 0b1010:    # GE
        take_branch = flags["N"] == flags["V"]
    elif cond == 0b1011:    # LT
        take_branch = flags["N"] != flags["V"]
    elif cond == 0b1110:    # AL
        take_branch = True

    if take_branch:
        if L == 1:
            regs[14] = (regs[15]) & 0xFFFFFFFF
        regs[15] = target_address
    else:
        regs[15] = (regs[15] + 4) & 0xFFFFFFFF

def is_branch_instruction(instruction: int) -> bool:
    top3 = (instruction >> 25) & 0b111
    return top3 == 0b101
