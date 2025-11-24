from typing import Dict, List, Union, Optional
from .data_processing_encoder import encode_data_processing_instruction
from .multiplication_set_encoder import encode_multiply_or_div_instruction
from .stack_set_encoder import encode_stack_instruction
from .branch_encoder import encode_branch

def encode__pseudo_instruction(instruction: str, parts: list, current_place: int, labels: Dict[str, int]) -> int:
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
    
    elif instruction == "MOD":
        if len(parts) != 3:
            raise ValueError("Syntax: MOD Rd, Rn, Rm")
        
        rd = parts[0].rstrip(",")
        rn = parts[1].rstrip(",")
        rm = parts[2]

        temp = "R12"
        seq = []
        seq.append(encode_stack_instruction("PUSH", [f"{{{temp}}}"]))

        seq.append(encode_multiply_or_div_instruction("DIV", [temp, rn, rm]))
        seq.append(encode_multiply_or_div_instruction("MUL", [temp, temp, rm]))
        seq.append(encode_data_processing_instruction("SUB", [rd, rn, temp]))
        
        seq.append(encode_stack_instruction("POP", [f"{{{temp}}}"]))
        return seq

    elif instruction == "SWAP" or instruction == "SWP":
        if len(parts) != 2:
            raise ValueError("Syntax: SWAP Rn, Rm")

        rn = parts[0].rstrip(",")
        rm = parts[1].rstrip(",")

        temp = "R12"
        seq = []

        seq.append(encode_stack_instruction("PUSH", [f"{{{temp}}}"]))

        seq.append(encode_data_processing_instruction("MOV", [temp, rn]))
        seq.append(encode_data_processing_instruction("MOV", [rn, rm]))
        seq.append(encode_data_processing_instruction("MOV", [rm, temp]))

        seq.append(encode_stack_instruction("POP", [f"{{{temp}}}"]))
        return seq
    
    elif instruction == "LOOP":
        if len(parts) != 1:
            raise ValueError("Syntax: LOOP label")
        
        if current_place is None or labels is None:
            raise ValueError("LOOP requires current_place and labels")

        label = parts[0]
        cx = "R12"
        seq = []

        seq.append(encode_data_processing_instruction("SUB", [cx, "#1"]))
        seq.append(encode_data_processing_instruction("CMP", [cx, "#0"]))
        seq.append(encode_branch("B", label, current_place + 8, labels, "NE"))
    
        return seq

    return None
