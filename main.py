from assembler import read_source, clean_lines, assemble_to_machine_code
from utils.write_binary import write_machine_code_as_bits, write_machine_code_to_file
from cpu import CPU
from memory import Memory

def main():
    # 1. Read and clean source
    source_lines = read_source("program_in/program_Gauss_CMP_BR.s")
    cleaned_lines = clean_lines(source_lines)

    # 2. Assemble
    machine_codes = assemble_to_machine_code(cleaned_lines)

    # 3. Write outputs
    write_machine_code_to_file(machine_codes, "program_out/program.bin")
    write_machine_code_as_bits(machine_codes, "program_out/program_bits.txt")

    # 4. Create memory
    instruction_memory = Memory(1024 * 4)  # 4 KB instruction memory
    data_memory = Memory(1024 * 4)         # 4 KB data memory

    # 5. Load program into instruction memory
    with open("program_out/program.bin", "rb") as f:
        program_bytes = f.read()
        instruction_memory.load_bytes(program_bytes, start_addr = 0)

    # 6. Create CPU and simulate
    cpu = CPU(instruction_memory, data_memory)
    print("[SIMULATION START]")
    steps = cpu.run(max_steps = 100)
    print(f"[SIMULATION END] Executed {steps - 1} instructions")

    # 7. Dump registers and memory
    cpu.dump_registers()
    cpu.dump_memory(cpu.instruction_memory, start = 0, end = 42, name = "Instruction Memory")
    cpu.dump_memory(cpu.data_memory, start = 0, end = 64, name = "Data Memory")

if __name__ == "__main__":
    main()
