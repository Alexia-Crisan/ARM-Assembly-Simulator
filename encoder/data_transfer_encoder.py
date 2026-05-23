"""
Single data transfer: cond|01|I|P|U|B|W|L|Rn|Rd|offset12
 
B=0 -> word (LDR/STR)
B=1 -> byte (LDRB/STRB)
"""

from .helpers import register_to_number, encode_immediate_value, COND_ALWAYS

# single data transfer base (bits 27-26 = 01)
# P = 1 (pre-indexed), U = 1 (add offset), B = 0 (word), W = 0, L = 1 for LDR, L = 0 for STR
   
def encode_load_store(instruction: str, parts: list) -> int:
    """
    LDR  Rd, [Rn]          word load
    LDR  Rd, [Rn, #imm]    word load with offset
    STR  Rd, [Rn]          word store
    STR  Rd, [Rn, #imm]    word store with offset
    LDRB Rd, [Rn]          byte load (zero-extended)
    LDRB Rd, [Rn, #imm]    byte load with offset
    STRB Rd, [Rn]          byte store (lowest byte only)
    STRB Rd, [Rn, #imm]    byte store with offset
    """

    instr_upper = instruction.upper()
    rd = register_to_number(parts[0].rstrip(","))
    rn_str = parts[1]
 
    if not (rn_str.startswith("[") and rn_str.endswith("]")):
        raise ValueError("Memory operand must be [Rn] or [Rn, #imm]")
 
    inner = rn_str[1:-1]
    if "," in inner:
        rn_tok, imm_tok = [t.strip() for t in inner.split(",", 1)]
        rn = register_to_number(rn_tok)
        immediate_value = int(imm_tok.lstrip("#"), 0)
    else:
        rn = register_to_number(inner)
        immediate_value = 0
 
    P = 1; W = 0; I = 0
    U = 1 if immediate_value >= 0 else 0
    B = 1 if instr_upper in ("LDRB", "STRB") else 0
    L = 1 if instr_upper in ("LDR", "LDRB") else 0
    offset12 = immediate_value & 0xFFF
 
    return COND_ALWAYS | (0b01 << 26) | (I << 25) | (P << 24) | (U << 23) | (B << 22) | (W << 21) | (L << 20) | (rn << 16) | (rd << 12) | offset12
 
