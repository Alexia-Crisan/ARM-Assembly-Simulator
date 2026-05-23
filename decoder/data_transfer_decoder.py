from memory import Memory

def decode_load_store(instruction: int, regs: list, memory):
    """
    Decode and execute LDR / STR / LDRB / STRB.
    Bit 22 (B) = 0 → word (4 bytes), B = 1 → byte (1 byte, zero-extended on load).
    """
    
    L        = (instruction >> 20) & 1
    B        = (instruction >> 22) & 1   # byte / word flag
    rn_idx   = (instruction >> 16) & 0xF
    rd_idx   = (instruction >> 12) & 0xF
    offset12 = instruction & 0xFFF
    addr     = (regs[rn_idx] + offset12) & 0xFFFFFFFF
 
    if L:   # load
        if B:   # LDRB — read 1 byte, zero-extend
            regs[rd_idx] = memory.memory[addr] & 0xFF
        else:   # LDR — read 4 bytes
            regs[rd_idx] = memory.read_word(addr)
    else:   # store
        if B:   # STRB — write lowest byte only
            memory.memory[addr] = regs[rd_idx] & 0xFF
        else:   # STR — write 4 bytes
            memory.write_word(addr, regs[rd_idx])
 
 
def is_load_store_instruction(instruction: int) -> bool:
    return (instruction >> 26) & 0b11 == 0b01