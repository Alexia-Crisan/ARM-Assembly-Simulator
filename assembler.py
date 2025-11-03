from encoder.encoder import encode_instruction
from typing import List, Dict

def read_source(path: str) -> List[str]:
    with open(path, "r", encoding = "utf-8") as f:
        return [ln.rstrip("\n") for ln in f]


def clean_lines(lines: List[str]) -> List[str]:
    """
    Removes empty lines and comments
    Keeps labels
    """
    cleaned = []
    for line in lines:
        line = line.strip()

        if not line:
            continue

        for sep in (";", "//"):
            if sep in line:
                line = line.split(sep, 1)[0].strip()

        if not line:
            continue

        cleaned.append(line)

    return cleaned

def assemble_to_machine_code(lines: List[str]) -> List[int]:

    labels: Dict[str, int] = {}
    instructions: List[str] = []
    program_counter = 0

    # collect labels
    for line in lines:
        if line.endswith(":"):            
            label = line[ : -1].strip()
            labels[label] = program_counter # label points to current program_counter address
        else:
            instructions.append(line)
            program_counter += 4 # each instruction is 4 bytes

    # encode each instruction
    machine_codes: List[int] = []
    program_counter = 0
    for line in instructions:
        code = encode_instruction(line, program_counter, labels)
        
        if isinstance(code, list):
            machine_codes.extend(code)
            program_counter += len(code) * 4
        else:
            machine_codes.append(code)
            program_counter += 4

    return machine_codes