def decode_system_instruction(instruction: int, regs: list):
    """
    Decode and execute HLT, INP, OUT
    """
    
    opcode = (instruction >> 25) & 0b111     # bits [27:25]
    operand = instruction & 0x1FFFFFF        # bits [24:0]
    
    if opcode == 0b000: # HLT
        print("[HLT] Halting execution.")
        return "HALT"
    
    elif opcode == 0b001: # INP Rd
        rd = operand & 0xF

        try:
            val = int(input(f"[INP] Enter value for R{rd}: "))
        except ValueError:
            val = 0

        regs[rd] = val & 0xFFFFFFFF
        regs[15] = (regs[15] + 4) & 0xFFFFFFFF

    elif opcode == 0b010: # OUT {Reg list}
        reg_mask = operand & 0x1FFFFFF

        print("[OUT]", end=" ")

        for r in range(16):
            if reg_mask & (1 << r):
                print(f"R{r} = {regs[r]};", end = " ")
    
        print()

        regs[15] = (regs[15] + 4) & 0xFFFFFFFF

    else:
        print(f"[SYSTEM] Unknown opcode {opcode:03b}. Ignored.")
        regs[15] = (regs[15] + 4) & 0xFFFFFFFF

def is_system_instruction(instruction: int) -> bool:
    return (instruction >> 28) == 0b1111
