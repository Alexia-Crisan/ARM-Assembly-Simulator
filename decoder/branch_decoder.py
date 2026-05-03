def decode_branch(instruction: int, regs: list, flags: dict):
    """
    Decode and execute all branches (B, BL / JMS)
        Condition table (bits [31:28]):
        0000 EQ   Z=1
        0001 NE   Z=0
        1010 GE   N=V
        1011 LT   N≠V
        1100 GT   Z=0 and N=V
        1101 LE   Z=1 or  N≠V
        1110 AL   always
    """

    cond = (instruction >> 28) & 0xF
    L = (instruction >> 24) & 1
    offset24 = instruction & 0xFFFFFF

    if offset24 & (1 << 23):
        offset24 -= 1 << 24

    # ARM pipeline: PC is already 8 bytes ahead when branch executes
    target_address = (regs[15] + 8 + (offset24 << 2)) & 0xFFFFFFFF

    N, Z, C, V = flags["N"], flags["Z"], flags["C"], flags["V"]

    take_branch = False
    if   cond == 0b0000: take_branch = Z == 1             # EQ
    elif cond == 0b0001: take_branch = Z == 0             # NE
    elif cond == 0b1010: take_branch = N == V             # GE
    elif cond == 0b1011: take_branch = N != V             # LT
    elif cond == 0b1100: take_branch = Z == 0 and N == V  # GT
    elif cond == 0b1101: take_branch = Z == 1 or N != V   # LE
    elif cond == 0b1110: take_branch = True               # AL
 
    if take_branch:
        if L == 1:
            regs[14] = (regs[15]) & 0xFFFFFFFF
        regs[15] = target_address
    else:
        regs[15] = (regs[15] + 4) & 0xFFFFFFFF

def is_branch_instruction(instruction: int) -> bool:
    top3 = (instruction >> 25) & 0b111
    return top3 == 0b101
