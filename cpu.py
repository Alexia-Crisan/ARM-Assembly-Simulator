from typing import List
from memory import Memory
from decoder.decoder import execute_data_processing, execute_load_store, execute_branch, execute_multiply_set, execute_stack_set, execute_system_instruction
from decoder.multiplication_set_decoder import is_multiply_set_instruction
from decoder.branch_decoder import is_branch_instruction
from decoder.data_processing_decoder import is_data_processing_instruction
from decoder.data_transfer_decoder import is_load_store_instruction
from decoder.stack_set_decoder import is_stack_set_instruction
from decoder.system_instruction_decoder import is_system_instruction

class CPU:
    def __init__(self, instruction_memory: Memory, data_memory: Memory):
        self.regs: List[int] = [0] * 16  # r0 to r15 (r15 = program_counter)
        self.instruction_memory = instruction_memory
        self.data_memory = data_memory
        self.running = False

        self.regs[15] = 0                  # PC starts at 0
        self.regs[13] = data_memory.size   # SP starts at end of data memor

        # Flags
        self.flags = {
            "N": 0,  # Negative: set if the result is negative
            "Z": 0,  # Zero: set if the result is zero
            "C": 0,  # Carry: set if there was a carry out from addition/subtraction
            "V": 0   # Overflow: set if signed overflow occurs
        }

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

        if is_system_instruction(instruction): # HLT, OUT, INP
            result = execute_system_instruction(instruction, self)
            if result == "HALT":
                self.halt_execution()
            return
        elif is_branch_instruction(instruction):  # Branch
            execute_branch(instruction, self)
            return
        elif is_multiply_set_instruction(instruction):  # Multiply/Divide
            execute_multiply_set(instruction, self)
            self.regs[15] += 4
        elif is_data_processing_instruction(instruction):  # Data processing
            execute_data_processing(instruction, self)
            self.regs[15] += 4
        elif is_load_store_instruction(instruction):  # Load/store
            execute_load_store(instruction, self, self.data_memory)
            self.regs[15] += 4
        elif is_stack_set_instruction(instruction): # Push/pop
            execute_stack_set(instruction, self, self.data_memory)
            self.regs[15] += 4
        else:
            raise NotImplementedError(f"Unsupported instruction format!")

    def halt_execution(self):
        print("Execution halted.")
        self.running = False

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

    def dump_memory_as_list(self, memory, size=None):
        """Return memory content as a list of integers for visualization."""

        if size is None:
            size = memory.size
        mem_list = []

        for addr in range(0, size, 4):
            try:
                mem_list.append(memory.read_word(addr))
            except MemoryError:
                mem_list.append(0)
        return mem_list

    def get_registers_dict(self):
        return {f"R{i}": val for i, val in enumerate(self.regs)}
