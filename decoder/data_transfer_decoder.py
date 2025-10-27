from memory import Memory

def decode_load_store(instruction: int, regs: list, memory: Memory):
    """
    Decode and execute LDR / STR
    """
    L = (instruction >> 20) & 1
    rn_idx = (instruction >> 16) & 0xF
    rd_idx = (instruction >> 12) & 0xF
    offset12 = instruction & 0xFFF
    addr = regs[rn_idx] + offset12
    if L:  # LDR
        regs[rd_idx] = memory.read_word(addr)
    else:  # STR
        memory.write_word(addr, regs[rd_idx])

def is_load_store_instruction(instruction: int) -> bool:
    top2 = (instruction >> 26) & 0b11  # bits [27:26]
    return top2 == 0b01