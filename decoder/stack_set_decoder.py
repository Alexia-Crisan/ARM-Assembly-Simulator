def decode_stack_instruction(instruction: int, regs: list, memory):
    P = (instruction >> 24) & 1
    U = (instruction >> 23) & 1
    S = (instruction >> 22) & 1
    W = (instruction >> 21) & 1
    L = (instruction >> 20) & 1
    rn = (instruction >> 16) & 0xF
    reg_list = instruction & 0xFFFF

    sp_index = rn
    sp = regs[sp_index]

    if L == 0:
        for reg_num in range(15):
            if reg_list & (1 << reg_num):
                sp -= 4
                memory.write_word(sp, regs[reg_num])
        regs[sp_index] = sp
    else:
        for reg_num in range(16):
            if reg_list & (1 << reg_num):
                regs[reg_num] = memory.read_word(sp)
                sp += 4
        regs[sp_index] = sp

def is_stack_set_instruction(instruction: int) -> bool:
    top3 = (instruction >> 25) & 0b111
    return top3 == 0b100
