from typing import Dict, List, Union, Optional
from .data_processing_encoder import encode_data_processing_instruction
from .multiplication_set_encoder import encode_multiply_or_div_instruction
from .branch_encoder import encode_branch

def encode_pseudo_instruction(instruction: str, parts: list, current_place: int, labels: Dict[str, int]) -> int:
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

        seq.append(encode_data_processing_instruction("MOV", [temp, f"#{imm}"]))
        seq.append(encode_multiply_or_div_instruction("MUL", [rd, rn, temp]))

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

        seq.append(encode_data_processing_instruction("MOV", [temp, f"#{imm}"]))
        seq.append(encode_multiply_or_div_instruction("DIV", [rd, rn, temp]))

        return seq
    
    elif instruction == "MOD":
        if len(parts) != 3:
            raise ValueError("Syntax: MOD Rd, Rn, Rm")
        
        rd = parts[0].rstrip(",")
        rn = parts[1].rstrip(",")
        rm = parts[2]

        temp = "R12"
        seq = []

        seq.append(encode_multiply_or_div_instruction("DIV", [temp, rn, rm]))
        seq.append(encode_multiply_or_div_instruction("MUL", [temp, temp, rm]))
        seq.append(encode_data_processing_instruction("SUB", [rd, rn, temp]))
        
        return seq

    elif instruction == "SWAP" or instruction == "SWP":
        if len(parts) != 2:
            raise ValueError("Syntax: SWAP Rn, Rm")

        rn = parts[0].rstrip(",")
        rm = parts[1].rstrip(",")

        temp = "R12"
        seq = []

        seq.append(encode_data_processing_instruction("MOV", [temp, rn]))
        seq.append(encode_data_processing_instruction("MOV", [rn, rm]))
        seq.append(encode_data_processing_instruction("MOV", [rm, temp]))

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

    elif instruction == "NOT":  # NOT Rd  ->  MVN Rd, Rd
        if len(parts) != 1:
            raise ValueError("NOT expects 1 operand: NOT Rd")
        rd = parts[0].rstrip(",")
        return encode_data_processing_instruction("MVN", [rd, rd])

    elif instruction == "NEG":  # NEG Rd, Rn  ->  RSB Rd, Rn, #0  (Rd = 0 - Rn)
        if len(parts) != 2:
            raise ValueError("NEG expects 2 operands: NEG Rd, Rn")
        rd = parts[0].rstrip(",")
        rn = parts[1].rstrip(",")
        return encode_data_processing_instruction("RSB", [rd, rn, "#0"])

    elif instruction == "ABS":  # ABS Rd, Rn  ->  |Rn|
        # Expansion (4 words):
        #   CMP  Rn, #0            ; set N if negative
        #   MOV  Rd, Rn            ; assume positive
        #   BGE  skip              ; if N=0 (non-negative), skip the negate
        #   RSB  Rd, Rn, #0        ; Rd = -Rn
        # BGE is at current_place+8; its target is current_place+16 (one word past RSB).
        # offset = (target - (bge_pc + 8)) >> 2 = (current_place+16 - current_place-8-8) >> 2 = 0
        
        if len(parts) != 2:
            raise ValueError("ABS expects 2 operands: ABS Rd, Rn")
        rd  = parts[0].rstrip(",")
        rn  = parts[1].rstrip(",")
        bge_place = current_place + 8           # byte address of the BGE instruction
        skip_addr = current_place + 16          # byte address after RSB (skip target)
        bge_word  = encode_branch("BGE", "__abs_skip__", bge_place,
                                  {"__abs_skip__": skip_addr}, "GE")
        return [
            encode_data_processing_instruction("CMP", [rn, "#0"]),
            encode_data_processing_instruction("MOV", [rd, rn]),
            bge_word,
            encode_data_processing_instruction("RSB", [rd, rn, "#0"]),
        ]

    elif instruction == "ROL":  # ROL Rd, Rn, #n  ->  (Rn<<n) | (Rn>>(32-n))
        # Saves Rn to R11 first so in-place (Rd==Rn) is safe.
        # Clobbers R11 and R12.
        if len(parts) == 3 and parts[2].startswith("#"):
            rd    = parts[0].rstrip(",")
            rn    = parts[1].rstrip(",")
            n     = int(parts[2].lstrip("#"), 0)
        elif len(parts) == 2 and parts[1].startswith("#"):
            rd    = parts[0].rstrip(",")
            rn    = rd
            n     = int(parts[1].lstrip("#"), 0)
        else:
            raise ValueError("Syntax: ROL Rd, Rn, #n  or  ROL Rd, #n")
        if not (1 <= n <= 31):
            raise ValueError("ROL shift amount must be 1..31")
        right_shift = 32 - n
        return [
            encode_data_processing_instruction("MOV",  ["R11", rn]),
            encode_data_processing_instruction("MOV",  ["R12", f"#{1 << n}"]),
            encode_multiply_or_div_instruction("MUL",  [rd,   "R11", "R12"]),
            encode_data_processing_instruction("MOV",  ["R12", f"#{1 << right_shift}"]),
            encode_multiply_or_div_instruction("DIV",  ["R12", "R11", "R12"]),
            encode_data_processing_instruction("ORR",  [rd,   rd,   "R12"]),
        ]

    elif instruction == "ROR":  # ROR Rd, Rn, #n  ->  (Rn>>n) | (Rn<<(32-n))
        # Saves Rn to R11 first so in-place (Rd==Rn) is safe.
        # Clobbers R11 and R12.
        if len(parts) == 3 and parts[2].startswith("#"):
            rd    = parts[0].rstrip(",")
            rn    = parts[1].rstrip(",")
            n     = int(parts[2].lstrip("#"), 0)
        elif len(parts) == 2 and parts[1].startswith("#"):
            rd    = parts[0].rstrip(",")
            rn    = rd
            n     = int(parts[1].lstrip("#"), 0)
        else:
            raise ValueError("Syntax: ROR Rd, Rn, #n  or  ROR Rd, #n")
        if not (1 <= n <= 31):
            raise ValueError("ROR shift amount must be 1..31")
        left_shift = 32 - n
        return [
            encode_data_processing_instruction("MOV",  ["R11", rn]),
            encode_data_processing_instruction("MOV",  ["R12", f"#{1 << n}"]),
            encode_multiply_or_div_instruction("DIV",  [rd,   "R11", "R12"]),
            encode_data_processing_instruction("MOV",  ["R12", f"#{1 << left_shift}"]),
            encode_multiply_or_div_instruction("MUL",  ["R12", "R11", "R12"]),
            encode_data_processing_instruction("ORR",  [rd,   rd,   "R12"]),
        ]

    elif instruction == "CALL":  # CALL label  ->  JMS label  (alias)
        if len(parts) != 1:
            raise ValueError("CALL expects 1 operand: CALL label")
        return encode_branch("JMS", parts[0], current_place, labels, "AL")

    elif instruction == "HALT":  # HALT  ->  HLT  (alias)
        from .system_instruction_encoder import encode_system_instruction
        return encode_system_instruction("HLT", [])

    return None