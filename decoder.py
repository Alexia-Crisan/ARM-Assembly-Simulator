from memory import Memory

def execute_data_processing(instruction: int, regs: list):
    """
    Decode and execute data processing instruction (ADD, SUB, MOV)
    """
    opcode = (instruction >> 21) & 0xF
    I = (instruction >> 25) & 1
    rn_idx = (instruction >> 16) & 0xF
    rd_idx = (instruction >> 12) & 0xF
    operand2 = instruction & 0xFFF

    if I:
        rotate = ((operand2 >> 8) & 0xF) * 2
        imm8 = operand2 & 0xFF
        val2 = ((imm8 >> rotate) | ((imm8 << (32 - rotate)) & 0xFFFFFFFF)) & 0xFFFFFFFF
    else:
        val2 = regs[operand2 & 0xF]

    if opcode == 0b0100:  # ADD
        regs[rd_idx] = (regs[rn_idx] + val2) & 0xFFFFFFFF
    elif opcode == 0b0010:  # SUB
        regs[rd_idx] = (regs[rn_idx] - val2) & 0xFFFFFFFF
    elif opcode == 0b1101:  # MOV
        regs[rd_idx] = val2
    else:
        raise NotImplementedError(f"Opcode {opcode} not implemented")

def execute_load_store(instruction: int, regs: list, memory: Memory):
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

def execute_branch(instruction: int, regs: list):
    """
    Decode and execute branch (B)
    """
    offset24 = instruction & 0xFFFFFF

    if offset24 & (1 << 23):
        offset24 |= ~0xFFFFFF
    
    offset_bytes = offset24 << 2
    regs[15] = (regs[15] + 8 + offset_bytes) & 0xFFFFFFFF
