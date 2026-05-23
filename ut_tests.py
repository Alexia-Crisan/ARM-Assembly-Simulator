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
            mem.load_bytes(bytes(300), start_addr=0)


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
        cpu = run("MOV R0, #7\nCMP R0, #7\nHLT")
        assert cpu.flags["C"] == 1

    def test_sub_does_not_update_flags(self):
        cpu = run("MOV R0, #10\nCMP R0, #10\nSUB R0, #3\nHLT")
        assert cpu.flags["Z"] == 1

    def test_add_does_not_update_flags(self):
        cpu = run("MOV R0, #5\nCMP R0, #5\nADD R0, #1\nHLT")
        assert cpu.flags["Z"] == 1

    def test_overflow_wrap_unsigned(self):
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
        cpu = run("""
            MOV R0, #0
            JMS inc_sub
            ADD R0, #100
            HLT
inc_sub:
            ADD R0, #1
            RET
        """)
        assert R(cpu, 0) == 101

    def test_lr_set_correctly_by_jms(self):
        cpu = run("""
            MOV R0, #0
            JMS sub
            HLT
sub:
            RET
        """)
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
        assert R(cpu, 3) == 2
        assert R(cpu, 4) == 1

    def test_push_psh_aliases(self):
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

    def test_inc(self):
        assert R(run("MOV R0, #10\nINC R0\nHLT"), 0) == 11

    def test_dec(self):
        assert R(run("MOV R0, #10\nDEC R0\nHLT"), 0) == 9

    def test_clr(self):
        assert R(run("MOV R0, #99\nCLR R0\nHLT"), 0) == 0

    def test_lsl_three_operand(self):
        assert R(run("MOV R1, #3\nLSL R2, R1, #2\nHLT"), 2) == 12

    def test_lsl_in_place(self):
        assert R(run("MOV R0, #5\nLSL R0, #1\nHLT"), 0) == 10

    def test_lsl_by_zero(self):
        assert R(run("MOV R0, #7\nLSL R0, #0\nHLT"), 0) == 7

    def test_lsl_no_push_pop(self):
        assert self._no_push_pop("MOV R1, #3\nLSL R2, R1, #2\nHLT")

    def test_lsr_three_operand(self):
        assert R(run("MOV R2, #24\nLSR R4, R2, #3\nHLT"), 4) == 3

    def test_lsr_in_place(self):
        assert R(run("MOV R0, #8\nLSR R0, #1\nHLT"), 0) == 4

    def test_lsr_no_push_pop(self):
        assert self._no_push_pop("MOV R2, #8\nLSR R2, #1\nHLT")

    def test_mod(self):
        assert R(run("MOV R5, #17\nMOV R3, #5\nMOD R7, R5, R3\nHLT"), 7) == 2

    def test_mod_exact_divisor(self):
        assert R(run("MOV R5, #20\nMOV R3, #5\nMOD R7, R5, R3\nHLT"), 7) == 0

    def test_mod_no_push_pop(self):
        assert self._no_push_pop("MOV R5, #17\nMOV R3, #5\nMOD R7, R5, R3\nHLT")

    def test_swap(self):
        cpu = run("MOV R8, #15\nMOV R9, #99\nSWAP R8, R9\nHLT")
        assert R(cpu, 8) == 99 and R(cpu, 9) == 15

    def test_swp_alias(self):
        cpu = run("MOV R0, #1\nMOV R1, #2\nSWP R0, R1\nHLT")
        assert R(cpu, 0) == 2 and R(cpu, 1) == 1

    def test_swap_no_push_pop(self):
        assert self._no_push_pop("MOV R0, #1\nMOV R1, #2\nSWAP R0, R1\nHLT")

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
        assert R(cpu, 0) == 6
        assert R(cpu, 2) == 8

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
        """Count numbers 1..9 that are divisible by 3."""
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
        assert R(cpu, 0) == 3


# ═════════════════════════════════════════════════════════════════════
# 10. New instructions — RSB, TST, BIC, LDRB, STRB
# ═════════════════════════════════════════════════════════════════════
class TestRSB:

    def test_rsb_basic(self):
        cpu = run("MOV R0, #3\nRSB R1, R0, #10\nHLT")
        assert R(cpu, 1) == 7

    def test_rsb_zero_gives_negation(self):
        cpu = run("MOV R0, #5\nRSB R1, R0, #0\nHLT")
        assert R(cpu, 1) == 0xFFFFFFFB

    def test_rsb_register_operand(self):
        cpu = run("MOV R0, #3\nMOV R1, #10\nRSB R2, R0, R1\nHLT")
        assert R(cpu, 2) == 7

    def test_rsb_two_operand_form(self):
        cpu = run("MOV R0, #40\nRSB R0, #100\nHLT")
        assert R(cpu, 0) == 60


class TestTST:

    def test_tst_sets_z_when_no_overlap(self):
        cpu = run("MOV R0, #0b1010\nTST R0, #0b0101\nHLT")
        assert cpu.flags["Z"] == 1

    def test_tst_clears_z_when_overlap(self):
        cpu = run("MOV R0, #0xFF\nTST R0, #0x0F\nHLT")
        assert cpu.flags["Z"] == 0

    def test_tst_does_not_write_destination(self):
        cpu = run("MOV R0, #0xAA\nMOV R1, #0\nTST R0, #0xFF\nHLT")
        assert R(cpu, 0) == 0xAA
        assert R(cpu, 1) == 0

    def test_tst_with_register_operand(self):
        cpu = run("MOV R0, #0b1100\nMOV R1, #0b0011\nTST R0, R1\nHLT")
        assert cpu.flags["Z"] == 1

    def test_tst_drives_branch(self):
        cpu = run("""
            MOV R0, #0b1010
            TST R0, #0b0001
            BNE odd
            MOV R1, #0
            B end
odd:        MOV R1, #1
end:        HLT
        """)
        assert R(cpu, 1) == 0


class TestBIC:

    def test_bic_clears_lower_bits(self):
        cpu = run("MOV R0, #0xFF\nBIC R1, R0, #0b111\nHLT")
        assert R(cpu, 1) == 0xF8

    def test_bic_clears_all_gives_zero(self):
        cpu = run("MOV R0, #0xFF\nBIC R1, R0, #0xFF\nHLT")
        assert R(cpu, 1) == 0

    def test_bic_mask_of_zero_no_change(self):
        cpu = run("MOV R0, #0b1111\nBIC R1, R0, #0\nHLT")
        assert R(cpu, 1) == 0b1111

    def test_bic_two_operand_form(self):
        cpu = run("MOV R0, #0xFF\nBIC R0, #0x0F\nHLT")
        assert R(cpu, 0) == 0xF0

    def test_bic_with_register_mask(self):
        cpu = run("MOV R0, #0b1111\nMOV R1, #0b1010\nBIC R2, R0, R1\nHLT")
        assert R(cpu, 2) == 0b0101

    def test_bic_orr_set_clear(self):
        cpu = run("MOV R0, #0\nORR R0, #0b11\nBIC R0, #0b10\nHLT")
        assert R(cpu, 0) == 0b01


class TestLDRBSTRB:

    def test_ldrb_zero_extends(self):
        base = DATA_BASE
        cpu = run(f"""
            MOV R0, #0x{base:X}
            MOV R1, #0xFF
            STRB R1, [R0]
            LDRB R2, [R0]
            HLT
        """)
        assert R(cpu, 2) == 0xFF

    def test_ldrb_result_fits_in_byte(self):
        base = DATA_BASE
        cpu = run(f"""
            MOV R0, #0x{base:X}
            MOV R1, #0xAB
            STRB R1, [R0]
            MOV R2, #0
            MVN R2, R2
            LDRB R2, [R0]
            HLT
        """)
        assert R(cpu, 2) == 0xAB
        assert R(cpu, 2) < 0x100

    def test_strb_ldrb_with_offset(self):
        base = DATA_BASE
        cpu = run(f"""
            MOV R0, #0x{base:X}
            MOV R1, #0x42
            STRB R1, [R0, #2]
            LDRB R2, [R0, #2]
            HLT
        """)
        assert R(cpu, 2) == 0x42

    def test_strb_stores_only_lowest_byte(self):
        base = DATA_BASE
        cpu = run(f"""
            MOV R0, #0x{base:X}
            MOV R1, #0x78
            MOV R3, #0x12
            LSL R3, R3, #8
            ORR R1, R1, R3
            STRB R1, [R0]
            LDR R2, [R0]
            HLT
        """)
        assert R(cpu, 2) == 0x78000000

    def test_ldrb_string_bytes(self):
        base = DATA_BASE
        cpu = run(f"""
            MOV R0, #0x{base:X}
            MOV R1, #65
            MOV R2, #66
            MOV R3, #67
            STRB R1, [R0]
            STRB R2, [R0, #1]
            STRB R3, [R0, #2]
            LDRB R4, [R0]
            LDRB R5, [R0, #1]
            LDRB R6, [R0, #2]
            HLT
        """)
        assert R(cpu, 4) == 65
        assert R(cpu, 5) == 66
        assert R(cpu, 6) == 67


# ═════════════════════════════════════════════════════════════════════
# 11. New pseudo-instructions — NEG, NOT, ABS, ROL, ROR, CALL, HALT
# ═════════════════════════════════════════════════════════════════════
class TestNEG:

    def test_neg_positive(self):
        cpu = run("MOV R0, #5\nNEG R1, R0\nHLT")
        assert R(cpu, 1) == 0xFFFFFFFB

    def test_neg_zero(self):
        cpu = run("MOV R0, #0\nNEG R1, R0\nHLT")
        assert R(cpu, 1) == 0

    def test_neg_twice_is_identity(self):
        cpu = run("MOV R0, #42\nNEG R1, R0\nNEG R2, R1\nHLT")
        assert R(cpu, 2) == 42

    def test_neg_expands_to_one_word(self):
        words = assemble_to_machine_code(clean_lines("MOV R0, #5\nNEG R1, R0\nHLT".splitlines()))
        assert len(words) == 3


class TestNOT:

    def test_not_zero(self):
        cpu = run("MOV R0, #0\nNOT R0\nHLT")
        assert R(cpu, 0) == 0xFFFFFFFF

    def test_not_twice_identity(self):
        cpu = run("MOV R0, #0xAB\nNOT R0\nNOT R0\nHLT")
        assert R(cpu, 0) == 0xAB

    def test_not_expands_to_one_word(self):
        words = assemble_to_machine_code(clean_lines("NOT R0\nHLT".splitlines()))
        assert len(words) == 2


class TestABS:

    def test_abs_positive_unchanged(self):
        cpu = run("MOV R0, #7\nABS R1, R0\nHLT")
        assert R(cpu, 1) == 7

    def test_abs_zero(self):
        cpu = run("MOV R0, #0\nABS R1, R0\nHLT")
        assert R(cpu, 1) == 0

    def test_abs_negative(self):
        cpu = run("MOV R0, #5\nNEG R0, R0\nABS R1, R0\nHLT")
        assert R(cpu, 1) == 5

    def test_abs_large_negative(self):
        cpu = run("MOV R0, #100\nNEG R0, R0\nABS R1, R0\nHLT")
        assert R(cpu, 1) == 100

    def test_abs_expands_to_four_words(self):
        words = assemble_to_machine_code(clean_lines("MOV R0, #1\nABS R1, R0\nHLT".splitlines()))
        assert len(words) == 6

    def test_abs_does_not_clobber_source(self):
        cpu = run("MOV R0, #10\nNEG R2, R0\nABS R1, R2\nHLT")
        assert R(cpu, 0) == 10
        assert R(cpu, 1) == 10


class TestROL:

    def test_rol_by_8(self):
        cpu = run("MOV R0, #1\nROL R1, R0, #8\nHLT")
        assert R(cpu, 1) == 0x100

    def test_rol_by_16(self):
        cpu = run("MOV R0, #1\nROL R1, R0, #16\nHLT")
        assert R(cpu, 1) == 0x10000

    def test_rol_in_place(self):
        cpu = run("MOV R0, #1\nROL R0, #4\nHLT")
        assert R(cpu, 0) == 16

    def test_rol_wraps_high_bit(self):
        cpu = run("MOV R0, #0x80\nLSL R0, R0, #24\nROL R1, R0, #1\nHLT")
        assert R(cpu, 1) == 1

    def test_rol_expands_to_six_words(self):
        words = assemble_to_machine_code(clean_lines("MOV R0, #1\nROL R1, R0, #4\nHLT".splitlines()))
        assert len(words) == 8


class TestROR:

    def test_ror_by_1(self):
        cpu = run("MOV R0, #2\nROR R1, R0, #1\nHLT")
        assert R(cpu, 1) == 1

    def test_ror_high_bit_wraps(self):
        cpu = run("MOV R0, #1\nROR R1, R0, #1\nHLT")
        assert R(cpu, 1) == 0x80000000

    def test_ror_by_8(self):
        cpu = run("MOV R0, #0x100\nROR R1, R0, #8\nHLT")
        assert R(cpu, 1) == 1

    def test_ror_in_place(self):
        cpu = run("MOV R0, #0x100\nROR R0, #8\nHLT")
        assert R(cpu, 0) == 1

    def test_rol_ror_roundtrip(self):
        cpu = run("MOV R0, #0xC0\nROL R1, R0, #5\nROR R2, R1, #5\nHLT")
        assert R(cpu, 2) == 0xC0

    def test_ror_expands_to_six_words(self):
        words = assemble_to_machine_code(clean_lines("MOV R0, #2\nROR R1, R0, #1\nHLT".splitlines()))
        assert len(words) == 8


class TestCALL:

    def test_call_executes_subroutine(self):
        cpu = run("""
            MOV R0, #1
            CALL sub
            HLT
sub:
            ADD R0, #10
            RET
        """)
        assert R(cpu, 0) == 11

    def test_call_returns_to_correct_address(self):
        cpu = run("""
            MOV R0, #0
            CALL sub
            ADD R0, #100
            HLT
sub:
            ADD R0, #1
            RET
        """)
        assert R(cpu, 0) == 101

    def test_call_encodes_same_as_jms(self):
        jms_words  = assemble_to_machine_code(clean_lines("JMS sub\nHLT\nsub:\nRET".splitlines()))
        call_words = assemble_to_machine_code(clean_lines("CALL sub\nHLT\nsub:\nRET".splitlines()))
        assert jms_words == call_words


class TestHALT:

    def test_halt_stops_execution(self):
        cpu = run("MOV R0, #5\nHALT\nMOV R0, #99")
        assert R(cpu, 0) == 5

    def test_halt_encodes_same_as_hlt(self):
        hlt_words  = assemble_to_machine_code(clean_lines("HLT".splitlines()))
        halt_words = assemble_to_machine_code(clean_lines("HALT".splitlines()))
        assert hlt_words == halt_words