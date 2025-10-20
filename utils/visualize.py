import tkinter as tk
from tkinter import ttk

def visualize_cpu(registers, flags, instruction_memory, data_memory, mem_rows = 16, mem_cols = 16):
    """
    registers: dict of register name -> value
    flags: dict of flags -> value
    instruction_memory: list of integers
    data_memory: list of integers
    mem_rows: number of rows for memory grids
    mem_cols: number of columns for memory grids
    """
    root = tk.Tk()
    root.title("CPU Simulation")

    # ------------------- LEFT PANEL: Registers + Flags -------------------
    left_frame = ttk.Frame(root)
    left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    # Registers
    reg_frame = ttk.LabelFrame(left_frame, text="Registers")
    reg_frame.pack(fill="x", pady=5)
    for i, (name, value) in enumerate(registers.items()):
        tk.Label(reg_frame, text=name).grid(row=i, column=0, sticky="w")
        tk.Label(reg_frame, text=f"0x{value:08X}").grid(row=i, column=1, sticky="w")

    # Flags
    flag_frame = ttk.LabelFrame(left_frame, text="Flags")
    flag_frame.pack(fill="x", pady=5)
    for i, (name, value) in enumerate(flags.items()):
        tk.Label(flag_frame, text=name).grid(row=i, column=0, sticky="w")
        tk.Label(flag_frame, text=str(value)).grid(row=i, column=1, sticky="w")

    # ------------------- RIGHT PANEL: Memories -------------------
    right_frame = ttk.Frame(root)
    right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

    # Instruction Memory
    instr_frame = ttk.LabelFrame(right_frame, text="Instruction Memory")
    instr_frame.pack(pady=5)
    for r in range(mem_rows):
        for c in range(mem_cols):
            addr = r * mem_cols + c
            val = instruction_memory[addr] if addr < len(instruction_memory) else 0
            cell = tk.Label(instr_frame, text=f"{val:08X}", width=8, relief="solid", borderwidth=1)
            cell.grid(row=r, column=c, padx=1, pady=1)

    # Data Memory
    data_frame = ttk.LabelFrame(right_frame, text="Data Memory")
    data_frame.pack(pady=5)
    for r in range(mem_rows):
        for c in range(mem_cols):
            addr = r * mem_cols + c
            val = data_memory[addr] if addr < len(data_memory) else 0
            cell = tk.Label(data_frame, text=f"{val:08X}", width=8, relief="solid", borderwidth=1)
            cell.grid(row=r, column=c, padx=1, pady=1)

    root.mainloop()
