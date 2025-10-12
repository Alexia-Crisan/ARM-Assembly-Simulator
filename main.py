from assembler import read_source, clean_lines, assemble_to_machine_code
from utils.write_binary import write_machine_code_as_bits, write_machine_code_to_file
from cpu import CPU
from memory import Memory

def main():
    # 1. read source file
    source_lines = read_source("program_in/program_ADD_MOV_STR_B.s")

    # 2. clean code
    cleaned_lines = clean_lines(source_lines)

    # 3. assemble
    machine_codes = assemble_to_machine_code(cleaned_lines)

    # 4. write in files
    write_machine_code_to_file(machine_codes, "program_out/program.bin")
    write_machine_code_as_bits(machine_codes, "program_out/program_bits.txt")

    # 5. simulate
    mem_size = 1024  # 1KB memory
    memory = Memory(mem_size)

    cpu = CPU(memory)
    cpu.load_program(machine_codes)

    print("[SIMULATION START]")
    steps = cpu.run(max_steps = 20)
    print(f"[SIMULATION END] Executed {steps - 1} instructions")
    
    #6. dump regisers and memory content after simulation
    cpu.dump_registers()
    cpu.dump_memory()



if __name__ == "__main__":
    main()
