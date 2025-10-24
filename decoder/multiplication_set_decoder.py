def decode_multiply_set(instruction: int, regs: list):
    """
    Decode and execute MUL / DVI
    """

    A  = (instruction >> 21) & 1   # 0 -> MUL, 1 -> DIV
    Rd = (instruction >> 16) & 0xF
    Rn = (instruction >> 12) & 0xF  # 0
    Rs = (instruction >> 8) & 0xF
    Rm = instruction & 0xF

    if A == 0:  # MUL
        regs[Rd] = (regs[Rm] * regs[Rs]) & 0xFFFFFFFF
    else:       # DIV
        if regs[Rs] == 0:
            raise ZeroDivisionError(f"Divide by zero: R{Rs}={regs[Rs]}")
        regs[Rd] = (regs[Rm] // regs[Rs]) & 0xFFFFFFFF

def is_multiply_set_instruction(instruction: int) -> bool:
        bits_27_22 = (instruction >> 22) & 0b111111
        bits_7_4 = (instruction >> 4) & 0b1111

        return bits_27_22 == 0b000000 and bits_7_4 == 0b1001