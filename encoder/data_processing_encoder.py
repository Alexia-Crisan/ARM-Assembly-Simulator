"""
Data processing (ADD, SUB, MOV, CMP, AND, ORR, EOR): cond|00|I|opcode|S|Rn|Rd|operand2
"""

from .helpers import register_to_number, encode_immediate_value, COND_ALWAYS, OPCODES

def encode_data_processing_instruction (instruction: str, parts: list) -> int:
    """
      MOV Rd, #imm
      MOV Rd, Rn
      ADD Rd, Rn, Rm
      ADD Rd, Rn, #imm
      ADD Rd, Rm/#imm       
      SUB Rd, Rn, Rm
      SUB Rd, Rn, #imm
      SUB Rd, Rm/#imm   
      CMP Rn, Rm
      CMP Rn, #imm
      AND Rd, Rn, Rm
      AND Rd, Rn, #imm
      AND Rd, Rm/#imm 
      ORR Rd, Rn, Rm
      ORR Rd, Rn, #imm
      ORR Rd, Rm/#imm  
      EOR Rd, Rn, Rm
      EOR Rd, Rn, #imm
      EOR Rd, Rm/#imm  
    """
    opcode = OPCODES[instruction]

    if instruction in ["CMP"] : S = 1 
    else: S = 0

    if instruction in ["ADD", "SUB", "AND", "ORR", "EOR", "MVN"]:
        if len(parts) == 2: # ADD R0, R1 -> R0 += R1
            rd = register_to_number(parts[0].rstrip(","))
            rn = rd
            op2 = parts[1]
        elif len(parts) == 3 and instruction != "MVN": # ADD R0, R1, R2 -> R0 = R1 + R2
            rd = register_to_number(parts[0].rstrip(","))
            rn = register_to_number(parts[1].rstrip(","))
            op2 = parts[2]
        else:
            raise ValueError(f"Invalid number of operands for {instruction}")

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
        operand = parts[1]

        if operand.startswith("#"):
            imm = int(operand[1:], 0)
            I = 1
            rn = 0
            operand2 = encode_immediate_value(imm)
        else:
            I = 0
            rn = 0
            rm = register_to_number(operand)
            operand2 = rm

        machine_instruction = COND_ALWAYS | (0 << 26) | (I << 25) | OPCODES[instruction] | (S << 20) | (rn << 16) | (rd << 12) | operand2
    
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