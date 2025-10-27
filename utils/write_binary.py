from typing import List

def write_machine_code_to_file(machine_codes: List[int], output_file: str) -> None:
    with open(output_file, "wb") as f:
        for code in machine_codes:
            f.write(code.to_bytes(4, byteorder = "big"))
    print(f"[OK] Wrote {len(machine_codes)} instructions to {output_file}")

def write_machine_code_as_bits(machine_codes: list[int], output_file: str) -> None:
    with open(output_file, "w", encoding = "utf-8") as f:
        for code in machine_codes:
            bits = format(code, "032b")
            grouped = " ".join(bits[i:i+4] for i in range(0, 32, 4)) # insert space every 4 bits
            f.write(grouped + "\n")
    
    print(f"[OK] Wrote {len(machine_codes)} binary instructions to {output_file}")