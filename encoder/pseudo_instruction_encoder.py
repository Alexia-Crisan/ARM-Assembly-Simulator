from .data_processing_encoder import encode_data_processing_instruction
from .multiplication_set_encoder import encode_multiply_or_div_instruction
from .stack_set_encoder import encode_stack_instruction

def encode__pseudo_instruction(instruction: str, parts: list) -> int:
    """
    Encode pseudo-instructions: INC, DEC, CLR
    """
    instruction = instruction.upper().strip()
   
    if instruction == "INC": # INC Rd  ->  ADD Rd, Rd, #1
        if len(parts) != 1:
            raise ValueError("INC expects 1 operand: INC Rd")
        rd = parts[0].rstrip(",")
        return encode_data_processing_instruction("ADD", [rd, rd, "#1"])

    elif instruction == "DEC": # DEC Rd  ->  SUB Rd, Rd, #1
        if len(parts) != 1:
            raise ValueError("DEC expects 1 operand: DEC Rd")
        rd = parts[0].rstrip(",")
        return encode_data_processing_instruction("SUB", [rd, rd, "#1"])

    elif instruction == "CLR":  # CLR Rd  ->  MOV Rd, #0
        if len(parts) != 1:
            raise ValueError("CLR expects 1 operand: CLR Rd")
        rd = parts[0].rstrip(",")
        return encode_data_processing_instruction("MOV", [rd, "#0"])
    
    elif instruction == "LSL":
        if len(parts) == 3 and parts[2].startswith("#"):
            rd = parts[0].rstrip(",")
            rn = parts[1].rstrip(",")
            shift = int(parts[2].lstrip("#"), 0)
        elif len(parts) == 2 and parts[1].startswith("#"):
            rd = parts[0].rstrip(",")
            rn = rd
            shift = int(parts[1].lstrip("#"), 0)
        else:
            raise ValueError("Syntax: LSL Rd, Rn, #imm or LSL Rd, #imm")

        imm = 1 << shift
        temp = "R12"
        seq = []

        seq.append(encode_stack_instruction("PUSH", [f"{temp}"]))

        seq.append(encode_data_processing_instruction("MOV", [temp, f"#{imm}"]))
        seq.append(encode_multiply_or_div_instruction("MUL", [rd, rn, temp]))

        seq.append(encode_stack_instruction("POP", [f"{temp}"]))
        return seq

    elif instruction == "LSR":
        if len(parts) == 3 and parts[2].startswith("#"):
            rd = parts[0].rstrip(",")
            rn = parts[1].rstrip(",")
            shift = int(parts[2].lstrip("#"), 0)
        elif len(parts) == 2 and parts[1].startswith("#"):
            rd = parts[0].rstrip(",")
            rn = rd
            shift = int(parts[1].lstrip("#"), 0)
        else:
            raise ValueError("Syntax: LSR Rd, Rn, #imm or LSR Rd, #imm")

        imm = 1 << shift
        temp = "R12"
        seq = []

        seq.append(encode_stack_instruction("PUSH", [f"{temp}"]))

        seq.append(encode_data_processing_instruction("MOV", [temp, f"#{imm}"]))
        seq.append(encode_multiply_or_div_instruction("DIV", [rd, rn, temp]))

        seq.append(encode_stack_instruction("POP", [f"{temp}"]))
        return seq

    return None
