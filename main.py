from assembler import read_source, clean_and_encode_lines, assemble_to_machine_code, write_machine_code_to_file, write_machine_code_as_bits

def main():
    # 1. read source file
    source_lines = read_source("program.s")

    # 2. clean code and encode
    clean_lines = clean_and_encode_lines(source_lines)

    # 3. assemble
    machine_codes = assemble_to_machine_code(clean_lines)

    # 4. write in file
    write_machine_code_to_file(machine_codes, "program.bin")
    write_machine_code_as_bits(machine_codes, "program_bits.txt")


if __name__ == "__main__":
    main()
