from assembler import read_source, clean_and_encode_lines, assemble_to_machine_code
from write_binary import write_machine_code_as_bits, write_machine_code_to_file
from cpu import CPU
from memory import Memory

def main():
    # 1. read source file
    source_lines = read_source("program.s")

    # 2. clean code and encode
    clean_lines = clean_and_encode_lines(source_lines)

    # 3. assemble
    machine_codes = assemble_to_machine_code(clean_lines)

    # 4. write in files
    write_machine_code_to_file(machine_codes, "program.bin")
    write_machine_code_as_bits(machine_codes, "program_bits.txt")

    # 5. simulate
    mem_size = 1024  # 1KB memory
    memory = Memory(mem_size)

    cpu = CPU(memory)
    cpu.load_program(machine_codes)

    print("[SIMULATION START]")
    steps = cpu.run(max_steps = 20)
    print(f"[SIMULATION END] Executed {steps - 1} instructions")
    
    for i, val in enumerate(cpu.regs):
        print(f"R{i}: 0x{val:08X}")

    print("\nMemory[0:64]:")
    for addr in range(0, 64, 4):
        word = memory.read_word(addr)
        print(f"{addr:04X}: 0x{word:08X}")


if __name__ == "__main__":
    main()
