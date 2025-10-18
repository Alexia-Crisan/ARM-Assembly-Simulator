from typing import List
from memory import Memory
from decoder.decoder import execute_data_processing, execute_load_store, execute_branch

class CPU:
    def __init__(self, instruction_memory: Memory, data_memory: Memory):
        self.regs: List[int] = [0] * 16  # r0 to r15 (r15 = program_counter)
        self.instruction_memory = instruction_memory
        self.data_memory = data_memory
        self.running = False

    def get_instruction(self):
        pc = self.regs[15]

        try:
            instruction = self.instruction_memory.read_word(pc)
        except MemoryError:
            self.running = False
            return
        
        if instruction == 0:
            self.running = False
            return

        top2 = (instruction >> 26) & 0b11      # bits [27:26]
        top3 = (instruction >> 25) & 0b111     # bits [27:25]

        if top3 == 0b101:  # Branch
            execute_branch(instruction, self.regs)
            return
        elif top2 == 0b00:  # Data processing
            execute_data_processing(instruction, self.regs)
            self.regs[15] += 4
        elif top2 == 0b01:  # Load/store
            execute_load_store(instruction, self.regs, self.data_memory)
            self.regs[15] += 4
        else:
            raise NotImplementedError(f"Unsupported instruction format: top2={top2:02b} top3={top3:03b}")

    def run(self, max_steps = 1000):
        self.running = True
        steps = 0
        while self.running and steps < max_steps:
            self.get_instruction()
            steps += 1
        return steps
    
    def dump_registers(self):
        print(f"\nRegisters content:")
        for i, val in enumerate(self.regs):
            print(f"R{i}: 0x{val:08X}")

    def dump_memory(self, memory, start = 0, end = 64, step = 4, name = "Memory"):
        print(f"\n{name} content:")
        print(f"{name}[{start}:{end}]:")
        for addr in range(start, end, step):
            word = memory.read_word(addr)
            print(f"{addr:04X}: 0x{word:08X}")
