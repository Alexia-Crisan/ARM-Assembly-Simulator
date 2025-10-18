from memory import Memory
from .data_processing_decoder import decode_data_processing_instruction
from .data_transfer_decoder import decode_load_store
from .branch_decoder import decode_branch


def execute_data_processing(instruction: int, cpu):
    decode_data_processing_instruction(instruction, cpu.regs, cpu.flags)

def execute_load_store(instruction: int, cpu, memory: Memory):
    decode_load_store(instruction, cpu.regs, memory)

def execute_branch(instruction: int, cpu):
    decode_branch(instruction, cpu.regs, cpu.flags)
