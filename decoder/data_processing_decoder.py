def decode_data_processing_instruction(instruction: int, regs: list, flags: dict):
    """
    Decode and execute data-processing instructions (ADD, SUB, MOV, CMP)
    flags: dict with keys 'N', 'Z', 'C', 'V'
    """
    opcode = (instruction >> 21) & 0xF
    I = (instruction >> 25) & 1
    S = (instruction >> 20) & 1
    rn_idx = (instruction >> 16) & 0xF
    rd_idx = (instruction >> 12) & 0xF
    operand2 = instruction & 0xFFF

    if I:
        rotate = ((operand2 >> 8) & 0xF) * 2
        imm8 = operand2 & 0xFF
        val2 = ((imm8 >> rotate) | ((imm8 << (32 - rotate)) & 0xFFFFFFFF)) & 0xFFFFFFFF
    else:
        val2 = regs[operand2 & 0xF]

    rn_val = regs[rn_idx] & 0xFFFFFFFF
    
    if opcode == 0b0100:  # ADD
        result = (rn_val + val2) & 0xFFFFFFFF
        regs[rd_idx] = result
        if S: update_flags(flags, result, rn_val, val2, "add")

    elif opcode == 0b0010:  # SUB
        result = (rn_val - val2) & 0xFFFFFFFF
        regs[rd_idx] = result
        if S: update_flags(flags, result, rn_val, val2, "sub")

    elif opcode == 0b0000:  # AND
        result = (rn_val & val2) & 0xFFFFFFFF
        regs[rd_idx] = result
        if S: update_flags(flags, result, rn_val, val2, "logic")

    elif opcode == 0b1100:  # ORR
        result = (rn_val | val2) & 0xFFFFFFFF
        regs[rd_idx] = result
        if S: update_flags(flags, result, rn_val, val2, "logic")

    elif opcode == 0b0001:  # EOR
        result = (rn_val ^ val2) & 0xFFFFFFFF
        regs[rd_idx] = result
        if S: update_flags(flags, result, rn_val, val2, "logic")

    elif opcode == 0b1111:  # MVN
        result = (~val2) & 0xFFFFFFFF
        regs[rd_idx] = result
        if S: update_flags(flags, result, rn_val, val2, "logic")

    elif opcode == 0b1101:  # MOV
        result = val2 & 0xFFFFFFFF
        regs[rd_idx] = result
        if S: update_flags(flags, result, rn_val, val2, "logic")

    elif opcode == 0b1010:  # CMP
        result = (regs[rn_idx] - val2) & 0xFFFFFFFF
        if S: update_flags(flags, result, rn_val, val2, "sub")
        
    else:
        raise NotImplementedError(f"Opcode {opcode} not implemented")

def update_flags(flags: dict, result32: int, rn_val: int, val2: int, op: str):
    """
    Update N, Z, C, V flags from a 32-bit arithmetic or logical result.
    op must be one of: 'add', 'sub', 'logic'
    """
    flags["N"] = (result32 >> 31) & 1
    flags["Z"] = int(result32 == 0)
 
    if op == "add":
        # Carry: unsigned overflow
        flags["C"] = int((rn_val + val2) > 0xFFFFFFFF)
        # Signed overflow: both operands same sign, result different sign
        flags["V"] = int(((~(rn_val ^ val2)) & (rn_val ^ result32)) >> 31 & 1)

    elif op == "sub":
        # Carry (borrow): unsigned borrow did NOT occur
        flags["C"] = int(rn_val >= val2)
        # Signed overflow: operands have different signs, result sign differs from rn
        flags["V"] = int(((rn_val ^ val2) & (rn_val ^ result32)) >> 31 & 1)

    else:  # logical operations - C and V are not changed by convention
        flags["C"] = 0
        flags["V"] = 0

def is_data_processing_instruction(instruction: int) -> bool:
    top2 = (instruction >> 26) & 0b11  # bits [27:26]
    return top2 == 0b00