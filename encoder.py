# encoder.py

"""
- Data processing (ADD, SUB, MOV): cond|00|I|opcode|S|Rn|Rd|operand2
- Single data transfer (LDR, STR): cond|01|I|P|U|B|W|L|Rn|Rd|offset12
- Branch (B): cond|101|offset24
"""

COND_ALWAYS = 0b1110 << 28 # always flag: 0b1110

# data processing opcodes (bits 24-21)
OPCODES = {
    "ADD": 0b0100 << 21, # ADD (addition), Example: ADD R0, R1, R2 -> R0 = R1 + R2
    "SUB": 0b0010 << 21, # SUB (subtract), Example: SUB R2, R0, R1 -> R2 = R0 - R1
    "MOV": 0b1101 << 21, # MOV (move / immediate load), Example: MOV R0, #5 -> R0 = 5
}

# Single data transfer base (bits 27-26 = 01)
# P = 1 (pre-indexed), U = 1 (add offset), B = 0 (word), W = 0, L = 1 for LDR, L = 0 for STR

def register_to_number(reg: str) -> int: #R2 -> 2
    if not reg.upper().startswith("R"):
        raise ValueError(f"Expected register like Rnum, got: {reg}")
    return int(reg[1:])

# immediate values are stored in 12 bits instead of 32: |rot|immediate_value(8 bits)| -> |11..8|7..0|
# immediate_value_32_bits = ROR(immediate_value_8_bits, 2 * rotate), ROR = right rotate
def encode_immediate_value(immediate_value: int) -> int:
    if immediate_value < 0:
        immediate_value &= 0xFFFFFFFF

    if 0 <= immediate_value <= 0xFF: # fits in 8 bits
        return immediate_value  # rotate = 0, immediate_value_8_bits = immediate_value

    # try rotate right to make immediate_value fit in 8 bits
    for rot in range(1, 16):
        rotate = rot * 2
        val = ((immediate_value >> rotate) | ((immediate_value << (32 - rotate)) & 0xFFFFFFFF)) & 0xFFFFFFFF # rotate right by rotate
        if val <= 0xFF:
            return (rotate << 8) | (val & 0xFF)

    raise ValueError(f"Immediate 0x{immediate_value:X} cannot be encoded in ARM rotate form")

def encode_data_processing_instruction (instruction: str, parts: list) -> int:
    """
    Encode data-processing instruction. parts is the token list after mnemonic.
    Supports:
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
            operand2 = encode_immediate_value(imm)
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
   