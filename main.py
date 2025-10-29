from assembler import read_source, clean_lines, assemble_to_machine_code
from utils.write_binary import write_machine_code_as_bits, write_machine_code_to_file
from cpu import CPU
from memory import Memory
from utils.visualize import visualize_cpu 

def main():
    # 1. Read and clean source
    source_lines = read_source("program_in/program_JMS_RET_verification.s")
    cleaned_lines = clean_lines(source_lines)

    # 2. Assemble
    machine_codes = assemble_to_machine_code(cleaned_lines)

    # 3. Write outputs
    write_machine_code_to_file(machine_codes, "program_out/program.bin")
    write_machine_code_as_bits(machine_codes, "program_out/program_bits.txt")

    # 4. Create memory
    instruction_memory = Memory(1024 * 4)  # 4 KB instruction memory
    data_memory = Memory(64 * 4)         # 4 KB data memory

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
    # cpu.dump_registers()
    # cpu.dump_memory(cpu.instruction_memory, start = 0, end = 42, name = "Instruction Memory")
    # cpu.dump_memory(cpu.data_memory, start = 0, end = 64, name = "Data Memory")

    # 8. Visualize CPU state in a GUI
    registers_dict = cpu.get_registers_dict()            
    flags_dict = cpu.flags                                 
    instr_mem_list = cpu.dump_memory_as_list(cpu.instruction_memory, size = 512)
    data_mem_list = cpu.dump_memory_as_list(cpu.data_memory, size = 256)
    visualize_cpu(registers_dict, flags_dict, instr_mem_list, data_mem_list, mem_rows = 12, mem_cols = 12)

if __name__ == "__main__":
    main()
