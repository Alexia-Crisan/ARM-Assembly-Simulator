"""
Single data transfer (LDR, STR): cond|01|I|P|U|B|W|L|Rn|Rd|offset12
"""

from .helpers import register_to_number, encode_immediate_value, COND_ALWAYS

# single data transfer base (bits 27-26 = 01)
# P = 1 (pre-indexed), U = 1 (add offset), B = 0 (word), W = 0, L = 1 for LDR, L = 0 for STR
   
def encode_load_store(instruction: str, parts: list) -> int:
    """
    - LDR Rd, [Rn]          -> offset = 0
    - LDR Rd, [Rn, #imm]    -> offset = imm
    - STR Rd, [Rn] / STR Rd, [Rn, #imm]

    I     = 0 (immediate offset, not register)
    P     = 1 (pre-indexed)
    U     = 1 if offset >= 0, 0 if negative (add/subtract)
    B     = 0 (word transfer)
    W     = 0 (no write-back)
    L     = 1 for LDR (load), 0 for STR (store)
    """

    rd = register_to_number(parts[0].rstrip(","))
    rn = parts[1]
    if not (rn.startswith("[") and rn.endswith("]")):
        raise ValueError("Memory operand must be [Rn] or [Rn, #imm]")

    inner_rn = rn[1:-1] # remove brackets 

    if "," in inner_rn:
        rn_token, immediate_value = [t.strip() for t in inner_rn.split(",", 1)]
        rn = register_to_number(rn_token)     
        immediate_value = int(immediate_value.lstrip("#"), 0)               
    else:
        rn = register_to_number(inner_rn)
        immediate_value = 0

    P = 1                      
    B = 0                       
    W = 0                    
    I = 0                       

    if immediate_value >= 0: U = 1 
    else: U = 0 

    if instruction.upper() == "LDR": L = 1 
    else: L = 0 

    offset12 = immediate_value & 0xFFF 

    machine_instruction = COND_ALWAYS | (0b01 << 26) | (I << 25) | (P << 24) | (U << 23) | (B << 22) | (W << 21) | (L << 20) | (rn << 16) | (rd << 12) | offset12 
    
    return machine_instruction
