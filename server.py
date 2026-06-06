import sys, os, uuid, time
from flask import Flask, request, jsonify, send_from_directory
from assembler import clean_lines, assemble_to_machine_code
from memory import Memory
from cpu import CPU

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for sub in ("", "decoder", "encoder", "utils"):
    sys.path.insert(0, os.path.join(BASE_DIR, sub))

app = Flask(__name__, static_folder="web", static_url_path="")

# ── session store ─────────────────────────────────────────────────────
# Each entry: { regs, flags, memory_bytes, steps, addr_to_line, halted, last_access }
_sessions = {}
_SESSION_TTL = 1800  # 30 minutes


def _expire_sessions():
    now = time.time()
    dead = [k for k, v in _sessions.items() if now - v["last_access"] > _SESSION_TTL]
    for k in dead:
        del _sessions[k]


def _cpu_from_session(s: dict) -> CPU:
    mem = Memory(size=len(s["memory_bytes"]))
    mem.memory = bytearray(s["memory_bytes"])
    cpu = CPU(mem)
    cpu.regs  = list(s["regs"])
    cpu.flags = dict(s["flags"])
    cpu.running = not s["halted"]
    return cpu


def _session_from_cpu(cpu: CPU) -> dict:
    return {
        "regs":         list(cpu.regs),
        "flags":        dict(cpu.flags),
        "memory_bytes": bytes(cpu.memory.memory),
    }


def _state_response(s: dict, prev_regs=None) -> dict:
    changed = []
    if prev_regs:
        changed = [i for i in range(16) if s["regs"][i] != prev_regs[i]]
    return {
        "registers":          {f"R{i}": v for i, v in enumerate(s["regs"])},
        "flags":              s["flags"],
        "steps":              s["steps"],
        "halted":             s["halted"],
        "pc":                 s["regs"][15],
        "changed_registers":  changed,
        "instruction_memory": _dump_region(s["memory_bytes"], 0, len(s["memory_bytes"]) // 2),
        "data_memory":        _dump_region(s["memory_bytes"], len(s["memory_bytes"]) // 2, len(s["memory_bytes"])),
    }


def _dump_region(raw: bytes, start: int, end: int) -> list:
    return [
        int.from_bytes(raw[a:a+4], "big")
        for a in range(start, end, 4)
    ]


# ── static routes ─────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/docs.html")
def serve_docs():
    return send_from_directory(app.static_folder, "docs.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


# ── normal run ────────────────────────────────────────────────────────

@app.route("/run", methods=["POST"])
def run_program():
    data        = request.get_json()
    source_code = data.get("code", "")
    user_pseudos = data.get("user_pseudos", {})
    cleaned     = clean_lines(source_code.splitlines())

    if not cleaned:
        return jsonify({"error": "No assembly code provided"}), 400

    try:
        machine_code = assemble_to_machine_code(cleaned, user_pseudos)
    except Exception as e:
        return jsonify({"error": f"Assembler error: {e}"}), 400

    memory = Memory(size=512)
    try:
        program_bytes = b"".join(int(x).to_bytes(4, "big") for x in machine_code)
        memory.load_bytes(program_bytes, start_addr=0)
    except Exception as e:
        return jsonify({"error": f"Memory load error: {e}"}), 400

    cpu = CPU(memory)
    try:
        steps = cpu.run(max_steps=200)
    except Exception as e:
        return jsonify({"error": f"Execution error: {e}"}), 400

    return jsonify({
        "steps":              steps - 1,
        "registers":          cpu.get_registers_dict(),
        "flags":              cpu.flags,
        "instruction_memory": cpu.memory.dump_instruction_region(),
        "data_memory":        cpu.memory.dump_data_region(),
    })


# ── debugger ──────────────────────────────────────────────────────────

@app.route("/debug/start", methods=["POST"])
def debug_start():
    """Assemble the program and create a debug session."""
    _expire_sessions()

    data        = request.get_json()
    source_code = data.get("code", "")
    user_pseudos = data.get("user_pseudos", {})
    cleaned     = clean_lines(source_code.splitlines())

    if not cleaned:
        return jsonify({"error": "No assembly code provided"}), 400

    try:
        machine_code, addr_to_line = assemble_with_map(cleaned, user_pseudos)
    except Exception as e:
        return jsonify({"error": f"Assembler error: {e}"}), 400

    memory = Memory(size=512)
    try:
        program_bytes = b"".join(int(x).to_bytes(4, "big") for x in machine_code)
        memory.load_bytes(program_bytes, start_addr=0)
    except Exception as e:
        return jsonify({"error": f"Memory load error: {e}"}), 400

    cpu = CPU(memory)

    session_id = str(uuid.uuid4())
    s = _session_from_cpu(cpu)
    s.update({
        "steps":       0,
        "halted":      False,
        "addr_to_line": addr_to_line,
        "last_access": time.time(),
    })
    _sessions[session_id] = s

    resp = _state_response(s)
    resp["session_id"]  = session_id
    resp["addr_to_line"] = addr_to_line
    return jsonify(resp)


@app.route("/debug/step", methods=["POST"])
def debug_step():
    """Execute one instruction and return the new state."""
    data       = request.get_json()
    session_id = data.get("session_id", "")

    if session_id not in _sessions:
        return jsonify({"error": "Session not found or expired"}), 404

    s = _sessions[session_id]
    s["last_access"] = time.time()

    if s["halted"]:
        return jsonify({**_state_response(s), "session_id": session_id})

    prev_regs = list(s["regs"])

    cpu = _cpu_from_session(s)
    try:
        cpu.get_instruction()
    except Exception as e:
        return jsonify({"error": f"Execution error: {e}"}), 400

    s.update(_session_from_cpu(cpu))
    s["steps"]  += 1
    s["halted"]  = not cpu.running

    resp = _state_response(s, prev_regs)
    resp["session_id"] = session_id
    return jsonify(resp)


@app.route("/debug/reset", methods=["POST"])
def debug_reset():
    """Delete the session."""
    data       = request.get_json()
    session_id = data.get("session_id", "")
    _sessions.pop(session_id, None)
    return jsonify({"ok": True})


@app.route("/reset", methods=["POST"])
def reset():
    return jsonify({"message": "Simulator reset"})


# ── assembler helper ──────────────────────────────────────────────────

def assemble_with_map(cleaned: list, user_pseudos = None):
    """
    Assemble and return (machine_codes, addr_to_line).
    addr_to_line maps byte address -> index into the cleaned source line list
    (labels excluded, so it maps to instruction lines only).
    """
    from encoder.encoder import encode_instruction
    from assembler import encode_with_user_pseudos

    if user_pseudos is None:
        user_pseudos = {}

    labels      = {}
    instr_lines = []
    pc          = 0

    # pass 1a — rough label pass
    for line in cleaned:
        if line.endswith(":"):
            labels[line[:-1].strip()] = pc
        else:
            instr_lines.append(line)
            pc += 4

    # pass 1b — accurate label pass with pseudo-op sizing
    labels_final = {}
    pc = 0
    for line in cleaned:
        if line.endswith(":"):
            labels_final[line[:-1].strip()] = pc
        else:
            try:
                result = encode_with_user_pseudos(line, pc, labels, user_pseudos)
            except Exception:
                result = 0
            pc += (len(result) if isinstance(result, list) else 1) * 4

    # pass 2 — encode + build addr_to_line
    machine_codes = []
    addr_to_line  = {}
    pc            = 0
    line_idx      = 0   # index into instr_lines (non-label lines in source)

    for line in cleaned:
        if line.endswith(":"):
            continue
        code = encode_with_user_pseudos(line, pc, labels_final, user_pseudos)
        if isinstance(code, list):
            for word in code:
                addr_to_line[pc] = line_idx
                machine_codes.append(word)
                pc += 4
        else:
            addr_to_line[pc] = line_idx
            machine_codes.append(code)
            pc += 4
        line_idx += 1

    return machine_codes, {str(k): v for k, v in addr_to_line.items()}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)