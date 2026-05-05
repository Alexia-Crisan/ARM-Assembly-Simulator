"""
Unit tests for the ARM Assembly Simulator.
Run with:  python -m pytest ut_tests.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from assembler import clean_lines, assemble_to_machine_code
from memory    import Memory
from cpu       import CPU

# ── constants that mirror Memory(512) defaults ────────────────────────
_MEM_SIZE  = 512
INSTR_BASE = 0
DATA_BASE  = _MEM_SIZE // 2
DATA_SIZE  = _MEM_SIZE // 2


# ── helper ────────────────────────────────────────────────────────────
def run(source: str, max_steps: int = 300) -> CPU:
    """Assemble *source*, load into a fresh Memory(512), run, return cpu."""
    lines = clean_lines(source.strip().splitlines())
    words = assemble_to_machine_code(lines)
    mem   = Memory(size=_MEM_SIZE)
    prog  = b"".join(w.to_bytes(4, "big") for w in words)
    mem.load_bytes(prog, start_addr=INSTR_BASE)
    cpu = CPU(mem)
    cpu.run(max_steps=max_steps)
    return cpu


def R(cpu: CPU, n: int) -> int:
    return cpu.regs[n]


# ═════════════════════════════════════════════════════════════════════
# 1. Unified memory
# ═════════════════════════════════════════════════════════════════════
class TestUnifiedMemory:

    def test_single_memory_object(self):
        cpu = run("HLT")
        assert hasattr(cpu, "memory")
        assert not hasattr(cpu, "instruction_memory")
        assert not hasattr(cpu, "data_memory")

    def test_instruction_region_has_nonzero_words(self):
        cpu = run("MOV R0, #42\nHLT")
        assert any(w != 0 for w in cpu.memory.dump_instruction_region())

    def test_data_region_initially_zero(self):
        cpu = run("HLT")
        assert all(w == 0 for w in cpu.memory.dump_data_region())

    def test_sp_points_to_top_of_data_region(self):
        cpu = run("HLT")
        assert cpu.regs[13] == DATA_BASE + DATA_SIZE

    def test_ldr_str_roundtrip_at_data_base(self):
        cpu = run(f"""
            MOV R0, #0x{DATA_BASE:X}
            MOV R1, #99
            STR R1, [R0]
            LDR R2, [R0]
            HLT
        """)
        assert R(cpu, 2) == 99

    def test_push_pop_stays_in_data_region(self):
        cpu = run("""
            MOV R0, #77
            PSH {R0}
            MOV R0, #0
            POP {R0}
            HLT
        """)
        assert R(cpu, 0) == 77

    def test_memory_size_accessible(self):
        mem = Memory(size=512)
        assert mem.total_size == 512
        assert mem.instr_words == 64
        assert mem.data_words  == 64

    def test_program_too_large_raises(self):
        mem = Memory(size=512)
        with pytest.raises(MemoryError):
            mem.load_bytes(bytes(300), start_addr=0)   # 300 > 256 (instr region)


# ═════════════════════════════════════════════════════════════════════
# 2. Data-processing instructions
# ═════════════════════════════════════════════════════════════════════
class TestDataProcessing:

    def test_mov_immediate(self):
        assert R(run("MOV R3, #255\nHLT"), 3) == 255

    def test_mov_register(self):
        assert R(run("MOV R0, #10\nMOV R1, R0\nHLT"), 1) == 10

    def test_mov_zero(self):
        assert R(run("MOV R0, #0\nHLT"), 0) == 0

    def test_add_three_operand(self):
        assert R(run("MOV R0, #10\nMOV R1, #5\nADD R2, R0, R1\nHLT"), 2) == 15

    def test_add_two_operand_immediate(self):
        assert R(run("MOV R0, #10\nADD R0, #3\nHLT"), 0) == 13

    def test_add_two_operand_register(self):
        assert R(run("MOV R0, #4\nMOV R1, #6\nADD R0, R1\nHLT"), 0) == 10

    def test_sub_three_operand(self):
        assert R(run("MOV R0, #20\nMOV R1, #7\nSUB R2, R0, R1\nHLT"), 2) == 13

    def test_sub_two_operand_immediate(self):
        assert R(run("MOV R0, #20\nSUB R0, #5\nHLT"), 0) == 15

    def test_sub_underflow_wraps(self):
        cpu = run("MOV R0, #0\nSUB R0, #1\nHLT")
        assert R(cpu, 0) == 0xFFFFFFFF

    def test_and(self):
        assert R(run("MOV R0, #0xFF\nMOV R1, #0x0F\nAND R2, R0, R1\nHLT"), 2) == 0x0F

    def test_and_zero_result(self):
        assert R(run("MOV R0, #0xF0\nMOV R1, #0x0F\nAND R2, R0, R1\nHLT"), 2) == 0

    def test_orr(self):
        assert R(run("MOV R0, #0xF0\nMOV R1, #0x0F\nORR R2, R0, R1\nHLT"), 2) == 0xFF

    def test_eor(self):
        assert R(run("MOV R0, #0xFF\nMOV R1, #0x0F\nEOR R2, R0, R1\nHLT"), 2) == 0xF0

    def test_eor_self_is_zero(self):
        assert R(run("MOV R0, #42\nEOR R0, R0\nHLT"), 0) == 0

    def test_mvn_zero(self):
        assert R(run("MOV R0, #0\nMVN R1, R0\nHLT"), 1) == 0xFFFFFFFF

    def test_mvn_all_ones(self):
        cpu = run("MOV R0, #0xFF\nMVN R1, R0\nHLT")
        assert R(cpu, 1) == 0xFFFFFF00

    def test_mul(self):
        assert R(run("MOV R0, #6\nMOV R1, #7\nMUL R2, R0, R1\nHLT"), 2) == 42

    def test_mul_by_zero(self):
        assert R(run("MOV R0, #99\nMOV R1, #0\nMUL R2, R0, R1\nHLT"), 2) == 0

    def test_div_exact(self):
        assert R(run("MOV R0, #20\nMOV R1, #4\nDIV R2, R0, R1\nHLT"), 2) == 5

    def test_div_integer_truncation(self):
        assert R(run("MOV R0, #7\nMOV R1, #2\nDIV R2, R0, R1\nHLT"), 2) == 3

    def test_div_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            run("MOV R0, #10\nMOV R1, #0\nDIV R2, R0, R1\nHLT")


# ═════════════════════════════════════════════════════════════════════
# 3. Flag logic
# ═════════════════════════════════════════════════════════════════════
class TestFlags:

    def test_cmp_equal_sets_z(self):
        cpu = run("MOV R0, #5\nCMP R0, #5\nHLT")
        assert cpu.flags["Z"] == 1 and cpu.flags["N"] == 0

    def test_cmp_less_sets_n(self):
        cpu = run("MOV R0, #3\nCMP R0, #10\nHLT")
        assert cpu.flags["N"] == 1 and cpu.flags["Z"] == 0

    def test_cmp_greater_clears_nz(self):
        cpu = run("MOV R0, #10\nCMP R0, #3\nHLT")
        assert cpu.flags["N"] == 0 and cpu.flags["Z"] == 0

    def test_cmp_sets_carry_when_no_borrow(self):
        cpu = run("MOV R0, #10\nCMP R0, #5\nHLT")
        assert cpu.flags["C"] == 1

    def test_cmp_clears_carry_on_borrow(self):
        cpu = run("MOV R0, #3\nCMP R0, #10\nHLT")
        assert cpu.flags["C"] == 0

    def test_cmp_equal_sets_carry(self):
        # equal: rn >= val2 → C = 1
        cpu = run("MOV R0, #7\nCMP R0, #7\nHLT")
        assert cpu.flags["C"] == 1

    def test_sub_does_not_update_flags(self):
        # plain SUB has S=0 — flags must not change
        cpu = run("MOV R0, #10\nCMP R0, #10\nSUB R0, #3\nHLT")
        assert cpu.flags["Z"] == 1    # set by CMP, must survive SUB

    def test_add_does_not_update_flags(self):
        cpu = run("MOV R0, #5\nCMP R0, #5\nADD R0, #1\nHLT")
        assert cpu.flags["Z"] == 1    # set by CMP, must survive ADD

    def test_overflow_wrap_unsigned(self):
        # Build 0x7FFFFFFF via LSL then adjust, add 1 → 0x80000000
        cpu = run("""
            MOV R0, #0x80
            LSL R0, R0, #24
            SUB R0, #1
            MOV R1, #1
            ADD R0, R0, R1
            HLT
        """)
        assert R(cpu, 0) == 0x80000000

    def test_flags_n_zero_after_zero_result(self):
        cpu = run("MOV R0, #5\nCMP R0, #5\nHLT")
        assert cpu.flags["N"] == 0
        assert cpu.flags["Z"] == 1


# ═════════════════════════════════════════════════════════════════════
# 4. Branches
# ═════════════════════════════════════════════════════════════════════
class TestBranches:

    def test_unconditional_branch_skips(self):
        cpu = run("""
            MOV R0, #1
            B done
            MOV R0, #99
done:
            HLT
        """)
        assert R(cpu, 0) == 1

    def test_beq_taken(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #5
            BEQ ok
            MOV R1, #0
            B end
ok:         MOV R1, #1
end:        HLT
        """)
        assert R(cpu, 1) == 1

    def test_beq_not_taken(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #6
            BEQ ok
            MOV R1, #99
            B end
ok:         MOV R1, #0
end:        HLT
        """)
        assert R(cpu, 1) == 99

    def test_bne_taken(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #6
            BNE ok
            MOV R1, #0
            B end
ok:         MOV R1, #1
end:        HLT
        """)
        assert R(cpu, 1) == 1

    def test_bne_not_taken_when_equal(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #5
            BNE skip
            MOV R1, #42
            B end
skip:       MOV R1, #0
end:        HLT
        """)
        assert R(cpu, 1) == 42

    def test_blt_taken(self):
        cpu = run("""
            MOV R0, #3
            CMP R0, #10
            BLT ok
            MOV R2, #0
            B end
ok:         MOV R2, #1
end:        HLT
        """)
        assert R(cpu, 2) == 1

    def test_blt_not_taken_when_greater(self):
        cpu = run("""
            MOV R0, #10
            CMP R0, #3
            BLT fail
            MOV R2, #1
            B end
fail:       MOV R2, #0
end:        HLT
        """)
        assert R(cpu, 2) == 1

    def test_bgt_taken(self):
        cpu = run("""
            MOV R0, #10
            CMP R0, #3
            BGT ok
            MOV R2, #0
            B end
ok:         MOV R2, #1
end:        HLT
        """)
        assert R(cpu, 2) == 1

    def test_bgt_not_taken_when_equal(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #5
            BGT fail
            MOV R2, #1
            B end
fail:       MOV R2, #0
end:        HLT
        """)
        assert R(cpu, 2) == 1

    def test_bge_taken_on_equal(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #5
            BGE ok
            MOV R2, #0
            B end
ok:         MOV R2, #1
end:        HLT
        """)
        assert R(cpu, 2) == 1

    def test_bge_taken_on_greater(self):
        cpu = run("""
            MOV R0, #9
            CMP R0, #5
            BGE ok
            MOV R2, #0
            B end
ok:         MOV R2, #1
end:        HLT
        """)
        assert R(cpu, 2) == 1

    def test_ble_taken_on_less(self):
        cpu = run("""
            MOV R0, #3
            CMP R0, #10
            BLE ok
            MOV R2, #0
            B end
ok:         MOV R2, #1
end:        HLT
        """)
        assert R(cpu, 2) == 1

    def test_ble_taken_on_equal(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #5
            BLE ok
            MOV R2, #0
            B end
ok:         MOV R2, #1
end:        HLT
        """)
        assert R(cpu, 2) == 1

    def test_jms_ret_basic(self):
        cpu = run("""
            MOV R0, #1
            JMS sub
            HLT
sub:
            ADD R0, #10
            RET
        """)
        assert R(cpu, 0) == 11

    def test_jms_ret_returns_to_correct_address(self):
        # After RET the instruction after JMS executes, not JMS again
        cpu = run("""
            MOV R0, #0
            JMS inc_sub
            ADD R0, #100
            HLT
inc_sub:
            ADD R0, #1
            RET
        """)
        assert R(cpu, 0) == 101   # 0+1 (sub) + 100 (after return)

    def test_lr_set_correctly_by_jms(self):
        cpu = run("""
            MOV R0, #0
            JMS sub
            HLT
sub:
            RET
        """)
        # LR = address of instruction after JMS = 8 (JMS is at byte 4)
        assert cpu.regs[14] == 8


# ═════════════════════════════════════════════════════════════════════
# 5. Load / Store
# ═════════════════════════════════════════════════════════════════════
class TestLoadStore:

    def test_str_ldr_no_offset(self):
        cpu = run(f"MOV R0, #0x{DATA_BASE:X}\nMOV R1, #123\nSTR R1, [R0]\nLDR R2, [R0]\nHLT")
        assert R(cpu, 2) == 123

    def test_str_ldr_with_offset(self):
        cpu = run(f"MOV R0, #0x{DATA_BASE:X}\nMOV R1, #77\nSTR R1, [R0, #8]\nLDR R2, [R0, #8]\nHLT")
        assert R(cpu, 2) == 77

    def test_multiple_stores(self):
        cpu = run(f"""
            MOV R0, #0x{DATA_BASE:X}
            MOV R1, #10
            MOV R2, #20
            STR R1, [R0]
            STR R2, [R0, #4]
            LDR R3, [R0]
            LDR R4, [R0, #4]
            HLT
        """)
        assert R(cpu, 3) == 10
        assert R(cpu, 4) == 20

    def test_overwrite(self):
        cpu = run(f"""
            MOV R0, #0x{DATA_BASE:X}
            MOV R1, #10
            STR R1, [R0]
            MOV R1, #20
            STR R1, [R0]
            LDR R2, [R0]
            HLT
        """)
        assert R(cpu, 2) == 20

    def test_out_of_bounds_raises(self):
        # 0x200 = 512 = total_size of Memory(512), writing here is 1 byte past the end
        # 0x200 IS ARM-encodable (rot=12, imm8=2), so this tests runtime MemoryError
        with pytest.raises(MemoryError):
            run("MOV R0, #0x200\nMOV R1, #1\nSTR R1, [R0]\nHLT")


# ═════════════════════════════════════════════════════════════════════
# 6. Stack (PSH / POP)
# ═════════════════════════════════════════════════════════════════════
class TestStack:

    def test_push_pop_single(self):
        cpu = run("MOV R0, #55\nPSH {R0}\nMOV R0, #0\nPOP {R0}\nHLT")
        assert R(cpu, 0) == 55

    def test_push_pop_lifo(self):
        cpu = run("""
            MOV R0, #1
            MOV R1, #2
            PSH {R0}
            PSH {R1}
            POP {R3}
            POP {R4}
            HLT
        """)
        assert R(cpu, 3) == 2   # last pushed → first popped
        assert R(cpu, 4) == 1

    def test_push_psh_aliases(self):
        # PSH and PUSH are aliases
        cpu = run("MOV R0, #33\nPUSH {R0}\nMOV R0, #0\nPOP {R0}\nHLT")
        assert R(cpu, 0) == 33

    def test_sp_decrements_on_push(self):
        cpu = run("HLT")
        sp_before = cpu.regs[13]
        cpu2 = run("MOV R0, #1\nPSH {R0}\nHLT")
        assert cpu2.regs[13] == sp_before - 4

    def test_sp_restores_after_push_pop(self):
        cpu = run("HLT")
        initial_sp = cpu.regs[13]
        cpu2 = run("MOV R0, #1\nPSH {R0}\nPOP {R0}\nHLT")
        assert cpu2.regs[13] == initial_sp

    def test_multi_register_push_pop(self):
        cpu = run("""
            MOV R0, #0x11
            MOV R1, #0x22
            MOV R2, #0x33
            PSH {R0}
            PSH {R1}
            PSH {R2}
            POP {R5}
            POP {R6}
            POP {R7}
            HLT
        """)
        assert R(cpu, 5) == 0x33
        assert R(cpu, 6) == 0x22
        assert R(cpu, 7) == 0x11


# ═════════════════════════════════════════════════════════════════════
# 7. Pseudo-instructions
# ═════════════════════════════════════════════════════════════════════
class TestPseudoInstructions:

    def _no_push_pop(self, source: str) -> bool:
        words = assemble_to_machine_code(clean_lines(source.strip().splitlines()))
        return all((w >> 25) & 0b111 != 0b100 for w in words)

    # ── INC / DEC / CLR ──────────────────────────────────────────────
    def test_inc(self):
        assert R(run("MOV R0, #10\nINC R0\nHLT"), 0) == 11

    def test_dec(self):
        assert R(run("MOV R0, #10\nDEC R0\nHLT"), 0) == 9

    def test_clr(self):
        assert R(run("MOV R0, #99\nCLR R0\nHLT"), 0) == 0

    # ── LSL ──────────────────────────────────────────────────────────
    def test_lsl_three_operand(self):
        assert R(run("MOV R1, #3\nLSL R2, R1, #2\nHLT"), 2) == 12

    def test_lsl_in_place(self):
        assert R(run("MOV R0, #5\nLSL R0, #1\nHLT"), 0) == 10

    def test_lsl_by_zero(self):
        assert R(run("MOV R0, #7\nLSL R0, #0\nHLT"), 0) == 7

    def test_lsl_no_push_pop(self):
        assert self._no_push_pop("MOV R1, #3\nLSL R2, R1, #2\nHLT")

    # ── LSR ──────────────────────────────────────────────────────────
    def test_lsr_three_operand(self):
        assert R(run("MOV R2, #24\nLSR R4, R2, #3\nHLT"), 4) == 3

    def test_lsr_in_place(self):
        assert R(run("MOV R0, #8\nLSR R0, #1\nHLT"), 0) == 4

    def test_lsr_no_push_pop(self):
        assert self._no_push_pop("MOV R2, #8\nLSR R2, #1\nHLT")

    # ── MOD ──────────────────────────────────────────────────────────
    def test_mod(self):
        assert R(run("MOV R5, #17\nMOV R3, #5\nMOD R7, R5, R3\nHLT"), 7) == 2

    def test_mod_exact_divisor(self):
        assert R(run("MOV R5, #20\nMOV R3, #5\nMOD R7, R5, R3\nHLT"), 7) == 0

    def test_mod_no_push_pop(self):
        assert self._no_push_pop("MOV R5, #17\nMOV R3, #5\nMOD R7, R5, R3\nHLT")

    # ── SWAP / SWP ───────────────────────────────────────────────────
    def test_swap(self):
        cpu = run("MOV R8, #15\nMOV R9, #99\nSWAP R8, R9\nHLT")
        assert R(cpu, 8) == 99 and R(cpu, 9) == 15

    def test_swp_alias(self):
        cpu = run("MOV R0, #1\nMOV R1, #2\nSWP R0, R1\nHLT")
        assert R(cpu, 0) == 2 and R(cpu, 1) == 1

    def test_swap_no_push_pop(self):
        assert self._no_push_pop("MOV R0, #1\nMOV R1, #2\nSWAP R0, R1\nHLT")

    # ── LOOP ─────────────────────────────────────────────────────────
    def test_loop_five_iterations(self):
        cpu = run("""
            MOV R0, #0
            MOV R12, #5
loop:
            ADD R0, #1
            LOOP loop
            HLT
        """)
        assert R(cpu, 0) == 5

    def test_loop_three_iterations(self):
        cpu = run("""
            MOV R0, #0
            MOV R12, #3
lp:
            ADD R0, #2
            LOOP lp
            HLT
        """)
        assert R(cpu, 0) == 6

    def test_loop_no_push_pop(self):
        assert self._no_push_pop("MOV R12, #3\nlp:\nADD R0, #1\nLOOP lp\nHLT")


# ═════════════════════════════════════════════════════════════════════
# 8. Assembler — error handling
# ═════════════════════════════════════════════════════════════════════
class TestAssemblerErrors:

    def test_unknown_instruction(self):
        with pytest.raises(ValueError):
            assemble_to_machine_code(["FOOBAR R0, #1"])

    def test_unknown_label_in_branch(self):
        with pytest.raises((ValueError, KeyError)):
            assemble_to_machine_code(["B nowhere"])

    def test_duplicate_label(self):
        with pytest.raises(ValueError, match="Duplicate label"):
            assemble_to_machine_code(["lbl:", "HLT", "lbl:", "HLT"])

    def test_register_out_of_range(self):
        with pytest.raises(ValueError):
            assemble_to_machine_code(["MOV R16, #1"])

    def test_immediate_not_encodable(self):
        # 0x12345678 cannot be represented in ARM rotate form
        with pytest.raises(ValueError):
            assemble_to_machine_code(["MOV R0, #0x12345678"])

    def test_inp_wrong_operand_count(self):
        with pytest.raises((ValueError, TypeError)):
            assemble_to_machine_code(["INP"])

    def test_clean_lines_strips_comments(self):
        lines = clean_lines([
            "; full comment",
            "MOV R0, #1 ; inline comment",
            "// another style",
            "",
            "HLT",
        ])
        assert lines == ["MOV R0, #1", "HLT"]

    def test_clean_lines_strips_blank(self):
        lines = clean_lines(["", "   ", "HLT", "  "])
        assert lines == ["HLT"]


# ═════════════════════════════════════════════════════════════════════
# 9. End-to-end programs
# ═════════════════════════════════════════════════════════════════════
class TestEndToEnd:

    def test_gauss_sum_1_to_6(self):
        """1+2+3+4+5+6 = 21"""
        cpu = run("""
            MOV R0, #6
            MOV R1, #0
            MOV R2, #1
            ADD R0, R0, #1
loop:
            ADD R1, R1, R2
            ADD R2, #1
            CMP R2, R0
            BNE loop
            HLT
        """)
        assert R(cpu, 1) == 21

    def test_factorial_5(self):
        """5! = 120"""
        cpu = run("""
            MOV R0, #5
            MOV R1, #1
            MOV R2, #1
            ADD R0, #1
fact:
            MUL R1, R2
            ADD R2, #1
            CMP R2, R0
            BNE fact
            HLT
        """)
        assert R(cpu, 1) == 120

    def test_factorial_1(self):
        """1! = 1"""
        cpu = run("""
            MOV R0, #1
            MOV R1, #1
            MOV R2, #1
            ADD R0, #1
fact:
            MUL R1, R2
            ADD R2, #1
            CMP R2, R0
            BNE fact
            HLT
        """)
        assert R(cpu, 1) == 1

    def test_jms_ret_doubles_value(self):
        cpu = run("""
            MOV R0, #7
            JMS double
            HLT
double:
            MOV R1, #2
            MUL R0, R0, R1
            RET
        """)
        assert R(cpu, 0) == 14

    def test_jms_ret_execution_continues_after_return(self):
        cpu = run("""
            MOV R0, #1
            MOV R1, #2
            JMS sub
            ADD R2, R0, R1
            HLT
sub:
            ADD R0, #5
            RET
        """)
        assert R(cpu, 0) == 6    # 1 + 5
        assert R(cpu, 2) == 8    # 6 + 2

    def test_ldr_str_store_and_load_multiple(self):
        base = DATA_BASE
        cpu = run(f"""
            MOV R0, #0x{base:X}
            MOV R1, #10
            MOV R2, #20
            MOV R3, #30
            STR R1, [R0]
            STR R2, [R0, #4]
            STR R3, [R0, #8]
            LDR R4, [R0]
            LDR R5, [R0, #4]
            LDR R6, [R0, #8]
            HLT
        """)
        assert R(cpu, 4) == 10
        assert R(cpu, 5) == 20
        assert R(cpu, 6) == 30

    def test_loop_sum_with_pseudo(self):
        """Sum 1..5 using LOOP pseudo-instruction = 15"""
        cpu = run("""
            MOV R0, #0
            MOV R1, #1
            MOV R12, #5
lp:
            ADD R0, R0, R1
            INC R1
            LOOP lp
            HLT
        """)
        assert R(cpu, 0) == 15

    def test_mod_in_loop(self):
        """Count numbers 1..9 that are divisible by 3.
        NOTE: MOD uses R12 as a scratch register internally, so R12 cannot
        be used as the loop counter simultaneously.  Use an explicit counter
        in R10 and a manual BNE loop instead of the LOOP pseudo-instruction.
        """
        cpu = run("""
            MOV R0, #0
            MOV R1, #1
            MOV R2, #3
            MOV R10, #1
top:
            MOD R3, R1, R2
            CMP R3, #0
            BNE skip
            ADD R0, #1
skip:
            INC R1
            INC R10
            CMP R10, #10
            BNE top
            HLT
        """)
        assert R(cpu, 0) == 3   # divisible: 3, 6, 9