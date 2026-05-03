import sys, os
from flask import Flask, request, jsonify, send_from_directory
from assembler import clean_lines, assemble_to_machine_code
from memory import Memory
from cpu import CPU


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "decoder"))
sys.path.insert(0, os.path.join(BASE_DIR, "encoder"))
sys.path.insert(0, os.path.join(BASE_DIR, "utils"))

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder='web', static_url_path='')

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/run", methods=["POST"])
def run_program():
    data = request.get_json()
    source_code = data.get("code", "")
    cleaned = clean_lines(source_code.splitlines())

    if not cleaned:
        return jsonify({"error": "No assembly code provided"}), 400

    try:
        machine_code = assemble_to_machine_code(cleaned)
    except Exception as e:
        return jsonify({"error": f"Assembler error: {e}"}), 400

    memory = Memory(size=512)

    try:
        program_bytes = b''.join(int(x).to_bytes(4, "big", signed=False) for x in machine_code)
        memory.load_bytes(program_bytes, start_addr=0)
    except Exception as e:
        return jsonify({"error": f"Memory load error: {e}"}), 400

    cpu = CPU(memory)
    try:
        steps = cpu.run(max_steps=200)
    except Exception as e:
        return jsonify({"error": f"Execution error: {e}"}), 400

    registers = cpu.get_registers_dict()
    flags = cpu.flags

    return jsonify({
        "steps": steps - 1,
        "registers": registers,
        "flags": flags,
        "instruction_memory": cpu.memory.dump_instruction_region(),
        "data_memory": cpu.memory.dump_data_region()
    })


@app.route("/reset", methods=["POST"])
def reset():
    return jsonify({"message": "Simulator reset"})

@app.route("/docs.html")
def serve_docs():
    return send_from_directory(app.static_folder, "docs.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
