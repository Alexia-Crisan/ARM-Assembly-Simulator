class Memory:
    def __init__(self, size: int = 4096):
        self.memory = bytearray(size)

    def read_word(self, addr: int) -> int:
        if addr < 0 or addr + 4 > len(self.memory):
            raise MemoryError("Memory read out of range")
        
        return int.from_bytes(self.memory[addr : addr + 4], "big")

    def write_word(self, addr: int, value: int):
        if addr < 0 or addr + 4 > len(self.memory):
            raise MemoryError("Memory write out of range")
        
        self.memory[addr : addr + 4] = (value & 0xFFFFFFFF).to_bytes(4, "big")

    def dump(self, start = 0, words = 8):
        for i in range(words):
            addr = start + 4 * i

            if addr + 4 <= len(self.memory):
                val = self.read_word(addr)  
            else: val = 0

            print(f"0x{addr:08X}: 0x{val:08X}") 
  