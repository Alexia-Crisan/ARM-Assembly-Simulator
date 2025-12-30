# data processing opcodes (bits 24 - 21)
OPCODES = {
    "ADD": 0b0100 << 21, # ADD (addition), Example: ADD R0, R1, R2 -> R0 = R1 + R2
    "SUB": 0b0010 << 21, # SUB (subtract), Example: SUB R2, R0, R1 -> R2 = R0 - R1
    "MOV": 0b1101 << 21, # MOV (move / immediate load), Example: MOV R0, #5 -> R0 = 5
    "CMP": 0b1010 << 21, # CMP (compare), Example: CMP Rn, Operand2 -> sets flags
    "AND": 0b0000 << 21, # AND (logic and), Example: AND R0, R1, R2 -> R0 = R1 & R2
    "ORR": 0b1100 << 21, # ORR (logic or), Example: AND R0, R1, R2 -> R0 = R1 | R2
    "EOR": 0b0001 << 21, # XOR (exclusive or), , Example: EOR R0, R1, R2 -> R0 = R1 ^ R2
    "MVN": 0b1111 << 21, # MVN (not), Example: MVN R0, R1 -> R0 = ~R1
}

# Condition codes (bits 31 - 28)
CONDITION_CODES = {
    "EQ": 0b0000 << 28,  # equal
    "NE": 0b0001 << 28,  # not equal
    "GE": 0b1010 << 28,  # signed greater or equal
    "LT": 0b1011 << 28,  # signed less than
    "GT": 0b1100 << 28,  # signed greater than
    "LE": 0b1101 << 28,  # signed less or equal
    "AL": 0b1110 << 28,  # always (default)
}

COND_ALWAYS = CONDITION_CODES["AL"]

BRANCH_COND_MAP = {
    "B": "AL",
    "BEQ": "EQ",
    "BNE": "NE",
    "BLT": "LT",
    "BGT": "GT",
    "BGE": "GE",
    "BLE": "LE",
}

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
            return (rot << 8) | (val & 0xFF)

    raise ValueError(f"Immediate 0x{immediate_value:X} cannot be encoded in ARM rotate form")