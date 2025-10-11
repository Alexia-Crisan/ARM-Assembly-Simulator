# cpu.py
from typing import List
from memory import Memory
from decoder import execute_data_processing, execute_load_store, execute_branch

class CPU:
    def __init__(self, memory: Memory):
        self.regs: List[int] = [0] * 16  # r0..r15 (r15 = program_counter)
        self.memory = memory
        self.program: List[int] = []
        self.running = False

    def load_program(self, program: List[int]):
        self.program = program
        self.regs[15] = 0  # program_counter starts at 0

    def get_instruction(self):
        program_counter = self.regs[15]
        instruction_index = program_counter // 4

        if instruction_index < 0 or instruction_index >= len(self.program):
            self.running = False
            return
        
        instruction = self.program[instruction_index]

        opcode_type = (instruction >> 26) & 0b11
        if opcode_type == 0b00:
            execute_data_processing(instruction, self.regs)
            self.regs[15] += 4
        elif opcode_type == 0b01:
            execute_load_store(instruction, self.regs, self.memory)
            self.regs[15] += 4
        elif opcode_type == 0b101:
            execute_branch(instruction, self.regs)
        else:
            raise NotImplementedError(f"Instruction type {opcode_type} not implemented")

    def run(self, max_steps = 1000):
        self.running = True
        steps = 0
        while self.running and steps < max_steps:
            self.get_instruction()
            steps += 1
        return steps
