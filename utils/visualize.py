import math
import tkinter as tk

# Cell background colors
COLOR_INSTR_USED   = "#cce6ff"   # light blue - instruction word present
COLOR_DATA_USED    = "#e8d5f5"   # light purple - data / stack word present
COLOR_EMPTY        = "#ffffff"   # white - instruction slot empty
COLOR_BG           = "#f0f0f0"


def visualize_cpu(registers, flags, memory, mem_cols=8):

    root = tk.Tk()
    root.title("CPU Simulation - Unified Memory")
    root.configure(bg=COLOR_BG)

    font_normal = ("Segoe UI", 10)
    font_bold   = ("Segoe UI", 10, "bold")
    font_mono   = ("Consolas",  9)

    # ----------------------------------------------------------------
    # helper: labeled colored frame
    # ----------------------------------------------------------------
    def colored_labelframe(parent, title, accent):
        outer = tk.Frame(parent, bg=accent, bd=3, relief="groove")
        inner = tk.LabelFrame(
            outer,
            text=title,
            fg=accent,
            font=font_bold,
            bg="#f8f8f8",
            labelanchor="n",
            bd=0,
        )
        inner.pack(fill="both", expand=True, padx=2, pady=2)
        return outer, inner

    # ----------------------------------------------------------------
    # helper: draw a memory grid
    # ----------------------------------------------------------------
    def draw_memory_grid(parent, words, cols, used_color, empty_color, base_addr=0):
        """
        Draw a grid of hex cells.
        words      : list[int]   - one word per cell
        base_addr  : int         - byte address of words[0]
        used_color : str         - bg when word != 0
        empty_color: str         - bg when word == 0
        """
        rows = math.ceil(len(words) / cols) if words else 1

        # Column address headers
        for c in range(cols):
            tk.Label(
                parent,
                text=f"+{c*4:02X}",
                font=("Segoe UI", 8),
                bg="#f8f8f8",
                fg="#888888",
                width=9,
            ).grid(row=0, column=c + 1, padx=1)

        for r in range(rows):
            row_addr = base_addr + r * cols * 4
            # Row address label
            tk.Label(
                parent,
                text=f"{row_addr:04X}",
                font=("Segoe UI", 8),
                bg="#f8f8f8",
                fg="#888888",
                width=5,
                anchor="e",
            ).grid(row=r + 1, column=0, padx=(4, 2))

            for c in range(cols):
                idx = r * cols + c
                if idx < len(words):
                    val = words[idx]
                    bg  = used_color if val != 0 else empty_color
                    txt = f"{val:08X}"
                else:
                    bg  = "#e0e0e0"
                    txt = "--------"

                tk.Label(
                    parent,
                    text=txt,
                    font=font_mono,
                    bg=bg,
                    width=9,
                    relief="solid",
                    borderwidth=1,
                    anchor="center",
                ).grid(row=r + 1, column=c + 1, padx=1, pady=1)

    # ================================================================
    # LEFT PANEL - registers + flags
    # ================================================================
    left = tk.Frame(root, bg=COLOR_BG)
    left.grid(row=0, column=0, padx=10, pady=10, sticky="n")

    # Registers
    reg_outer, reg_frame = colored_labelframe(left, "Registers", "darkred")
    reg_outer.pack(fill="x", pady=5)

    # Show PC / SP / LR with a small annotation
    aliases = {15: "PC", 14: "LR", 13: "SP"}
    for i, (name, value) in enumerate(registers.items()):
        reg_num = int(name[1:]) if name[1:].isdigit() else -1
        alias   = aliases.get(reg_num, "")
        display = f"{name}" + (f" ({alias})" if alias else "")
        tk.Label(reg_frame, text=display,         font=font_bold,   bg="#f8f8f8", anchor="w", width=10).grid(row=i, column=0, sticky="w", padx=4)
        tk.Label(reg_frame, text=f"0x{value:08X}", font=font_mono,   bg="#f8f8f8", anchor="w").grid(row=i, column=1, sticky="w", padx=4)
        tk.Label(reg_frame, text=f"({value})",    font=font_normal, bg="#f8f8f8", fg="#888888", anchor="w").grid(row=i, column=2, sticky="w", padx=4)

    # Flags
    flag_outer, flag_frame = colored_labelframe(left, "Flags", "darkgreen")
    flag_outer.pack(fill="x", pady=5)

    for i, (fname, fval) in enumerate(flags.items()):
        color = "#cc0000" if fval == 1 else "#444444"
        tk.Label(flag_frame, text=fname,     font=font_bold,   bg="#f8f8f8", fg=color, width=4).grid(row=i, column=0, sticky="w", padx=4)
        tk.Label(flag_frame, text=str(fval), font=font_normal, bg="#f8f8f8", fg=color).grid(row=i, column=1, sticky="w", padx=4)

    # ================================================================
    # RIGHT PANEL - unified memory
    # ================================================================
    right = tk.Frame(root, bg=COLOR_BG)
    right.grid(row=0, column=1, padx=10, pady=10, sticky="n")

    instr_words = memory.dump_instruction_region()
    data_words  = memory.dump_data_region()

    # Instruction region
    instr_outer, instr_frame = colored_labelframe(
        right,
        f"Instruction region  (0x{memory.instr_base:04X} – 0x{memory.instr_base + memory.instr_size - 1:04X}  |  {memory.instr_words} words)",
        "darkblue",
    )
    instr_outer.pack(pady=5, fill="x")
    draw_memory_grid(
        instr_frame, instr_words, mem_cols,
        used_color=COLOR_INSTR_USED,
        empty_color=COLOR_EMPTY,
        base_addr=memory.instr_base,
    )

    # Data region
    data_outer, data_frame = colored_labelframe(
        right,
        f"Data / stack region  (0x{memory.data_base:04X} – 0x{memory.data_base + memory.data_size - 1:04X}  |  {memory.data_words} words)",
        "#6a0dad",
    )
    data_outer.pack(pady=5, fill="x")
    draw_memory_grid(
        data_frame, data_words, mem_cols,
        used_color=COLOR_DATA_USED,
        empty_color=COLOR_EMPTY,
        base_addr=memory.data_base,
    )

    root.mainloop()