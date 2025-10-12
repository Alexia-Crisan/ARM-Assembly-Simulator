from memory import Memory
from .data_processing_decoder import decode_data_processing_instruction
from .data_transfer_decoder import decode_load_store
from .branch_decoder import decode_branch


def execute_data_processing(instruction: int, regs: list):
    decode_data_processing_instruction(instruction, regs)

def execute_load_store(instruction: int, regs: list, memory: Memory):
    decode_load_store(instruction, regs, memory)

def execute_branch(instruction: int, regs: list):
    decode_branch(instruction, regs)
