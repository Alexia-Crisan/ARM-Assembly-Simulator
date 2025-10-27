class Memory:
    def __init__(self, size: int = 4096):
        self.size = size   
        self.memory = bytearray(size)

    def read_word(self, addr: int) -> int:
        if addr < 0 or addr + 4 > len(self.memory):
            raise MemoryError("Memory read out of range")
        
        return int.from_bytes(self.memory[addr : addr + 4], "big")

    def write_word(self, addr: int, value: int):
        if addr < 0 or addr + 4 > len(self.memory):
            raise MemoryError("Memory write out of range")
        
        self.memory[addr : addr + 4] = (value & 0xFFFFFFFF).to_bytes(4, "big")

    def load_bytes(self, data: bytes, start_addr: int = 0):
        self.memory[start_addr : start_addr + len(data)] = data