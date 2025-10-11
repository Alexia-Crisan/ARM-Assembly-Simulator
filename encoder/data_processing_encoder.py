"""
Data processing (ADD, SUB, MOV): cond|00|I|opcode|S|Rn|Rd|operand2
"""

from encoder import register_to_number, encode_immediate_value

COND_ALWAYS = 0b1110 << 28 # always flag: 0b1110

# data processing opcodes (bits 24 - 21)
OPCODES = {
    "ADD": 0b0100 << 21, # ADD (addition), Example: ADD R0, R1, R2 -> R0 = R1 + R2
    "SUB": 0b0010 << 21, # SUB (subtract), Example: SUB R2, R0, R1 -> R2 = R0 - R1
    "MOV": 0b1101 << 21, # MOV (move / immediate load), Example: MOV R0, #5 -> R0 = 5
}

def encode_data_processing_instruction (instruction: str, parts: list) -> int:
    """
      MOV Rd, #imm
      ADD Rd, Rn, Rm
      ADD Rd, Rn, #imm
      SUB Rd, Rn, Rm
      SUB Rd, Rn, #imm
    """
    opcode = OPCODES[instruction]

    S = 0

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