def decode_data_processing_instruction(instruction: int, regs: list, flags: dict):
    """
    Decode and execute data-processing instructions (ADD, SUB, MOV, CMP)
    flags: dict with keys 'N', 'Z', 'C', 'V'
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
    elif opcode == 0b0000:  # AND
        regs[rd_idx] = (regs[rn_idx] & val2) & 0xFFFFFFFF
    elif opcode == 0b1100:  # ORR
        regs[rd_idx] = (regs[rn_idx] | val2) & 0xFFFFFFFF
    elif opcode == 0b0001:  # EOR
        regs[rd_idx] = (regs[rn_idx] ^ val2) & 0xFFFFFFFF
    elif opcode == 0b1111:  # MVN
        regs[rd_idx] = (~val2) & 0xFFFFFFFF
    elif opcode == 0b1101:  # MOV
        regs[rd_idx] = val2
    elif opcode == 0b1010:  # CMP
        result = (regs[rn_idx] - val2) & 0xFFFFFFFF
        flags['Z'] = int(result == 0)
        flags['N'] = int((result >> 31) & 1)
        flags['V'] = int(((regs[rn_idx] ^ val2) & (regs[rn_idx] ^ result)) >> 31)
        #flags['C'] = int(regs[rn_idx] >= val2)
    else:
        raise NotImplementedError(f"Opcode {opcode} not implemented")
    
def is_data_processing_instruction(instruction: int) -> bool:
    top2 = (instruction >> 26) & 0b11  # bits [27:26]
    return top2 == 0b00