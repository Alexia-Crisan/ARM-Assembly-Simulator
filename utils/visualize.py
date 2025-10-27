import tkinter as tk
from tkinter import ttk

def visualize_cpu(registers, flags, instruction_memory, data_memory, mem_rows=16, mem_cols=16):
    root = tk.Tk()
    root.title("CPU Simulation")
    root.configure(bg="#f0f0f0")

    # ------------------- Fonts -------------------
    font_normal = ("Segoe UI", 10)
    font_bold = ("Segoe UI", 10, "bold")

    # ------------------- Helper for colored frames -------------------
    def colored_labelframe(parent, title, color):
        outer = tk.Frame(parent, bg=color, bd=3, relief="groove")
        inner = tk.LabelFrame(
            outer,
            text=title,
            fg=color,
            font=font_bold,
            bg="#f8f8f8",
            labelanchor="n",
            bd=0,
        )
        inner.pack(fill="both", expand=True, padx=2, pady=2)
        return outer, inner

    # ------------------- LEFT PANEL -------------------
    left_frame = tk.Frame(root, bg="#f0f0f0")
    left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    # Registers (Dark Red)
    reg_outer, reg_frame = colored_labelframe(left_frame, "Registers", "darkred")
    reg_outer.pack(fill="x", pady=5)
    for i, (name, value) in enumerate(registers.items()):
        tk.Label(reg_frame, text=name, font=font_bold, bg="#f8f8f8").grid(row=i, column=0, sticky="w", padx=4)
        tk.Label(reg_frame, text=f"0x{value:08X}", font=font_normal, bg="#f8f8f8").grid(row=i, column=1, sticky="w", padx=4)

    # Flags (Dark Green)
    flag_outer, flag_frame = colored_labelframe(left_frame, "Flags", "darkgreen")
    flag_outer.pack(fill="x", pady=5)
    for i, (name, value) in enumerate(flags.items()):
        label_font = font_bold if name.upper() in ["N", "Z", "C", "V"] else font_normal
        tk.Label(flag_frame, text=name, font=label_font, bg="#f8f8f8").grid(row=i, column=0, sticky="w", padx=4)
        tk.Label(flag_frame, text=str(value), font=font_normal, bg="#f8f8f8").grid(row=i, column=1, sticky="w", padx=4)

    # ------------------- RIGHT PANEL -------------------
    right_frame = tk.Frame(root, bg="#f0f0f0")
    right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

    # Instruction Memory (Dark Blue)
    instr_outer, instr_frame = colored_labelframe(right_frame, "Instruction Memory", "darkblue")
    instr_outer.pack(pady=5)
    for r in range(mem_rows):
        for c in range(mem_cols):
            addr = r * mem_cols + c
            if addr < len(instruction_memory) and instruction_memory[addr] != 0:
                val = instruction_memory[addr]
                bg_color = "#cce6ff"  # light blue for used cells
            else:
                val = 0
                bg_color = "white"
            cell = tk.Label(
                instr_frame,
                text=f"{val:08X}",
                width=8,
                relief="solid",
                borderwidth=1,
                bg=bg_color,
                font=font_normal
            )
            cell.grid(row=r, column=c, padx=1, pady=1)

    # Data Memory (Dark Blue)
    data_outer, data_frame = colored_labelframe(right_frame, "Data Memory", "darkblue")
    data_outer.pack(pady=5)
    for r in range(mem_rows):
        for c in range(mem_cols):
            addr = r * mem_cols + c
            if addr < len(data_memory) and data_memory[addr] != 0:
                val = data_memory[addr]
                bg_color = "#cce6ff"
            else:
                val = 0
                bg_color = "white"
            cell = tk.Label(
                data_frame,
                text=f"{val:08X}",
                width=8,
                relief="solid",
                borderwidth=1,
                bg=bg_color,
                font=font_normal
            )
            cell.grid(row=r, column=c, padx=1, pady=1)

    root.mainloop()
