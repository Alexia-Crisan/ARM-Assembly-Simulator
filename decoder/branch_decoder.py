
def decode_branch(instruction: int, regs: list):
    """
    Decode and execute branch (B)
    """
    offset24 = instruction & 0xFFFFFF

    if offset24 & (1 << 23):
        offset24 |= ~0xFFFFFF
    
    offset_bytes = offset24 << 2
    regs[15] = (regs[15] + 8 + offset_bytes) & 0xFFFFFFFF