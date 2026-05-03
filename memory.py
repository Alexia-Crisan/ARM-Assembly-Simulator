"""
Unified memory
  0x00000000 .. (size//2 - 1)   instruction region
  (size//2)  .. (size - 1)      data / stack region
"""

class Memory:
    def __init__(self, size: int = 512):
        if size % 8 != 0:
            raise ValueError("Size must be a multiple of 8")

        self.total_size = size
        self.instr_base = 0
        self.instr_size = size // 2 # bytes
        self.data_base  = size // 2
        self.data_size  = size // 2 # bytes

        self.memory = bytearray(size)

        self.instr_words = self.instr_size // 4 # words
        self.data_words  = self.data_size  // 4 # words

    def read_word(self, addr: int) -> int:
        addr = addr & 0xFFFFFFFF
        if addr + 4 > self.total_size:
            raise MemoryError(f"Memory read out of range: 0x{addr:08X}")
        
        return int.from_bytes(self.memory[addr: addr + 4], "big")

    def write_word(self, addr: int, value: int):
        addr = addr & 0xFFFFFFFF
        if addr + 4 > self.total_size:
            raise MemoryError(f"Memory write out of range: 0x{addr:08X}")
        
        self.memory[addr: addr + 4] = (value & 0xFFFFFFFF).to_bytes(4, "big")

    def load_bytes(self, data: bytes, start_addr: int = 0):
        end = start_addr + len(data)
        if end > self.instr_size:
            raise MemoryError(
                f"Program ({len(data)} bytes) exceeds instruction region "
                f"({self.instr_size} bytes)"
            )
        
        self.memory[start_addr: end] = data

    def dump_instruction_region(self) -> list[int]:
        return [
            int.from_bytes(self.memory[a: a + 4], "big")
            for a in range(self.instr_base, self.instr_base + self.instr_size, 4)
        ]

    def dump_data_region(self) -> list[int]:
        return [
            int.from_bytes(self.memory[a: a + 4], "big")
            for a in range(self.data_base, self.data_base + self.data_size, 4)
        ]