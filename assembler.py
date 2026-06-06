import re
from encoder.encoder import encode_instruction
from typing import List, Dict


def read_source(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f]


def clean_lines(lines: List[str]) -> List[str]:
    """
    Strip comments (;  //) and blank lines.
    Labels on their own line (e.g. 'loop:') are kept as-is.
    Labels on the same line as an instruction (e.g. 'ok: MOV R1, #1') are split so both the label token and the instruction are kept.
    """
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # strip inline comments
        for sep in (";", "//"):
            if sep in line:
                line = line.split(sep, 1)[0].strip()
        if not line:
            continue

        # handle "label: instruction" on the same line
        if ":" in line:
            colon_idx = line.index(":")
            potential_label = line[:colon_idx].strip()
            rest = line[colon_idx + 1:].strip()

            if potential_label and " " not in potential_label and "\t" not in potential_label:
                cleaned.append(potential_label + ":")
                if rest:
                    cleaned.append(rest)
                continue

        cleaned.append(line)
    return cleaned


def assemble_to_machine_code(lines: List[str], user_pseudos: dict = {}) -> List[int]:

    # separate labels from instructions
    raw_labels: Dict[str, int] = {}
    instruction_lines: List[str] = []
    pc = 0

    for line in lines:
        if line.endswith(":"):
            label = line[:-1].strip()
            if label in raw_labels:
                raise ValueError(f"Duplicate label: '{label}'")
            raw_labels[label] = pc
        else:
            instruction_lines.append(line)
            pc += 4   # placeholder — corrected in pass 1b below

    # recompute label addresses accounting for pseudo-ops
    labels: Dict[str, int] = {}
    pc = 0

    ordered: List[tuple] = []
    for line in lines:
        if line.endswith(":"):
            ordered.append(("label", line[:-1].strip()))
        else:
            ordered.append(("instr", line))

    for kind, value in ordered:
        if kind == "label":
            if value in labels:
                raise ValueError(f"Duplicate label: '{value}'")
            labels[value] = pc
        else:
            try:
                result = encode_with_user_pseudos(value, pc, raw_labels, user_pseudos)
            except Exception:
                result = 0

            word_count = len(result) if isinstance(result, list) else 1
            pc += word_count * 4

    # real encode with correct labels
    machine_codes: List[int] = []
    pc = 0

    for line in instruction_lines:
        code = encode_with_user_pseudos(line, pc, labels, user_pseudos)
        if isinstance(code, list):
            machine_codes.extend(code)
            pc += len(code) * 4
        else:
            machine_codes.append(code)
            pc += 4

    return machine_codes

def expand_user_pseudo(
    name: str,
    defn: dict,
    actual_args: List[str],
    current_place: int,
    labels: Dict[str, int],
    user_pseudos: dict,
) -> List[int]:
    params = defn.get("params", [])
    body   = defn.get("body",   [])
 
    if len(actual_args) != len(params):
        raise ValueError(
            f"User pseudo '{name}' expects {len(params)} argument(s) "
            f"({', '.join(params)}), got {len(actual_args)}"
        )
 
    words = []
    place = current_place
 
    for body_line in body:
        body_line = body_line.strip()
        if not body_line:
            continue
 
        first_token = body_line.split()[0].upper()
        if first_token == name.upper():
            raise ValueError(
                f"User pseudo '{name}' cannot call itself (recursion not allowed)"
            )
 
        expanded = body_line
        for param, arg in sorted(
            zip(params, actual_args), key=lambda pa: -len(pa[0])
        ):
            expanded = re.sub(r"\b" + re.escape(param) + r"\b", arg, expanded)
 
        result = encode_with_user_pseudos(expanded, place, labels, user_pseudos)
        if isinstance(result, list):
            words.extend(result)
            place += len(result) * 4
        else:
            words.append(result)
            place += 4
 
    return words
 
 
def encode_with_user_pseudos(
    line: str,
    current_place: int,
    labels: Dict[str, int],
    user_pseudos: dict,
) -> object:
    tokens   = line.replace(",", " ").split()
    mnemonic = tokens[0].upper() if tokens else ""
    user_pseudo_map = {k.upper(): k for k in user_pseudos}
    if mnemonic in user_pseudo_map:
        key  = user_pseudo_map[mnemonic]
        defn = user_pseudos[key]
 
        rest     = line[line.upper().index(mnemonic) + len(mnemonic):]
        raw_args = [a.strip() for a in re.split(r"[,\s]+", rest.strip()) if a.strip()]
 
        return expand_user_pseudo(
            key, defn, raw_args, current_place, labels, user_pseudos
        )
 
    return encode_instruction(line, current_place, labels)