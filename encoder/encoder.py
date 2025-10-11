"""
- Data processing (ADD, SUB, MOV): cond|00|I|opcode|S|Rn|Rd|operand2
- Single data transfer (LDR, STR): cond|01|I|P|U|B|W|L|Rn|Rd|offset12
- Branch (B): cond|101|offset24
"""

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