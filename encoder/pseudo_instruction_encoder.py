from .data_processing_encoder import encode_data_processing_instruction

def encode_simple_pseudo(instruction: str, parts: list) -> int:
    """
    Encode pseudo-instructions: INC, DEC, CLR
    """
    inst = instruction.upper().strip()
   
    if inst == "INC": # INC Rd  ->  ADD Rd, Rd, #1
        if len(parts) != 1:
            raise ValueError("INC expects 1 operand: INC Rd")
        rd = parts[0].rstrip(",")
        return encode_data_processing_instruction("ADD", [rd, rd, "#1"])

    elif inst == "DEC": # DEC Rd  ->  SUB Rd, Rd, #1
        if len(parts) != 1:
            raise ValueError("DEC expects 1 operand: DEC Rd")
        rd = parts[0].rstrip(",")
        return encode_data_processing_instruction("SUB", [rd, rd, "#1"])

    elif inst == "CLR":  # CLR Rd  ->  MOV Rd, #0
        if len(parts) != 1:
            raise ValueError("CLR expects 1 operand: CLR Rd")
        rd = parts[0].rstrip(",")
        return encode_data_processing_instruction("MOV", [rd, "#0"])

    return None
