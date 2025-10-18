"""
Data processing (ADD, SUB, MOV): cond|00|I|opcode|S|Rn|Rd|operand2
"""

from .helpers import register_to_number, encode_immediate_value, COND_ALWAYS, OPCODES

def encode_data_processing_instruction (instruction: str, parts: list) -> int:
    """
      MOV Rd, #imm
      ADD Rd, Rn, Rm
      ADD Rd, Rn, #imm
      SUB Rd, Rn, Rm
      SUB Rd, Rn, #imm
    """
    opcode = OPCODES[instruction]

    if instruction == "CMP": S = 1 
    else: S = 0

    if instruction == "ADD" or instruction == "SUB":
        rd = register_to_number(parts[0].rstrip(","))
        rn = register_to_number(parts[1].rstrip(","))
        op2 = parts[2]

        if op2.startswith("#"):
            immediate_value = int(op2[1:], 0)
            I = 1
            operand2 = encode_immediate_value(immediate_value)
        else:
            I = 0
            rm = register_to_number(op2)
            operand2 = rm

        machine_instruction = COND_ALWAYS | (0 << 26) | (I << 25) | opcode | (S << 20) | (rn << 16) | (rd << 12) | operand2
        return machine_instruction

    if instruction == "MOV":
        rd = register_to_number(parts[0].rstrip(","))
        immediate_value = parts[1]

        if not immediate_value.startswith("#"):
            raise ValueError("Only MOV Rd, #imm supported in this subset")
        
        imm = int(immediate_value[1:], 0) #auto-detects base of immediate value
        I = 1
        rn = 0
        operand2 = encode_immediate_value(imm)
        
        machine_instruction = COND_ALWAYS | (0 << 26) | (I << 25) | opcode | (S << 20) | (rn << 16) | (rd << 12) | operand2
        return machine_instruction
    
    if instruction == "CMP":
        rn = register_to_number(parts[0].rstrip(","))
        I = 1 if parts[1].startswith("#") else 0

        if I:
            operand2 = encode_immediate_value(int(parts[1][1:], 0))
        else:
            operand2 = register_to_number(parts[1])
        
        machine_instruction = COND_ALWAYS | (0 << 26) | (I << 25) | opcode | (S << 20) | (rn << 16) | operand2
        return machine_instruction