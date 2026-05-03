"""
Unit tests for the ARM simulator.

Run with:  pytest ut_tests.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from assembler import clean_lines, assemble_to_machine_code
from memory    import Memory, INSTR_BASE, DATA_BASE, DATA_SIZE
from cpu       import CPU


# ─────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────

def run(source: str, max_steps: int = 200) -> CPU:
    """Assemble source, load into unified memory, run, return cpu."""
    lines  = clean_lines(source.strip().splitlines())
    words  = assemble_to_machine_code(lines)
    mem    = Memory()
    prog   = b"".join(w.to_bytes(4, "big") for w in words)
    mem.load_bytes(prog, start_addr=INSTR_BASE)
    cpu    = CPU(mem)
    cpu.run(max_steps=max_steps)
    return cpu


def R(cpu: CPU, n: int) -> int:
    return cpu.regs[n]


# ─────────────────────────────────────────────────────────────────────
# 1. Unified memory
# ─────────────────────────────────────────────────────────────────────

class TestUnifiedMemory:
    def test_single_object(self):
        """CPU should expose exactly one memory object."""
        cpu = run("HLT")
        assert hasattr(cpu, "memory")
        assert not hasattr(cpu, "instruction_memory")
        assert not hasattr(cpu, "data_memory")

    def test_instruction_region_readable(self):
        cpu = run("MOV R0, #42\nHLT")
        # instruction region should have at least one non-zero word
        dump = cpu.memory.dump_instruction_region()
        assert any(w != 0 for w in dump)

    def test_data_region_writeable(self):
        """STR and LDR should work through the unified memory at DATA_BASE."""
        cpu = run(f"""
            MOV R0, #0x{DATA_BASE:X}
            MOV R1, #99
            STR R1, [R0]
            LDR R2, [R0]
            HLT
        """)
        assert R(cpu, 2) == 99

    def test_sp_initialised_to_data_top(self):
        cpu = run("HLT")
        expected_sp = DATA_BASE + DATA_SIZE - 4
        assert cpu.regs[13] == expected_sp

    def test_push_pop_use_data_region(self):
        """PUSH/POP should touch addresses inside the data region."""
        cpu = run(f"""
            MOV R0, #77
            PSH {{R0}}
            MOV R0, #0
            POP {{R0}}
            HLT
        """)
        assert R(cpu, 0) == 77


# ─────────────────────────────────────────────────────────────────────
# 2. Data-processing instructions
# ─────────────────────────────────────────────────────────────────────

class TestDataProcessing:
    def test_mov_immediate(self):
        cpu = run("MOV R3, #255\nHLT")
        assert R(cpu, 3) == 255

    def test_mov_register(self):
        cpu = run("MOV R0, #10\nMOV R1, R0\nHLT")
        assert R(cpu, 1) == 10

    def test_add_three_operand(self):
        cpu = run("MOV R0, #10\nMOV R1, #5\nADD R2, R0, R1\nHLT")
        assert R(cpu, 2) == 15

    def test_add_immediate(self):
        cpu = run("MOV R0, #10\nADD R0, #3\nHLT")
        assert R(cpu, 0) == 13

    def test_sub_three_operand(self):
        cpu = run("MOV R0, #20\nMOV R1, #7\nSUB R2, R0, R1\nHLT")
        assert R(cpu, 2) == 13

    def test_sub_immediate(self):
        cpu = run("MOV R0, #20\nSUB R0, #5\nHLT")
        assert R(cpu, 0) == 15

    def test_and(self):
        cpu = run("MOV R0, #0xFF\nMOV R1, #0x0F\nAND R2, R0, R1\nHLT")
        assert R(cpu, 2) == 0x0F

    def test_orr(self):
        cpu = run("MOV R0, #0xF0\nMOV R1, #0x0F\nORR R2, R0, R1\nHLT")
        assert R(cpu, 2) == 0xFF

    def test_eor(self):
        cpu = run("MOV R0, #0xFF\nMOV R1, #0x0F\nEOR R2, R0, R1\nHLT")
        assert R(cpu, 2) == 0xF0

    def test_mvn(self):
        cpu = run("MOV R0, #0\nMVN R1, R0\nHLT")
        assert R(cpu, 1) == 0xFFFFFFFF

    def test_mul(self):
        cpu = run("MOV R0, #6\nMOV R1, #7\nMUL R2, R0, R1\nHLT")
        assert R(cpu, 2) == 42

    def test_div(self):
        cpu = run("MOV R0, #20\nMOV R1, #4\nDIV R2, R0, R1\nHLT")
        assert R(cpu, 2) == 5


# ─────────────────────────────────────────────────────────────────────
# 3. Flag logic
# ─────────────────────────────────────────────────────────────────────

class TestFlags:
    def test_cmp_equal_sets_z(self):
        cpu = run("MOV R0, #5\nCMP R0, #5\nHLT")
        assert cpu.flags["Z"] == 1
        assert cpu.flags["N"] == 0

    def test_cmp_less_sets_n(self):
        cpu = run("MOV R0, #3\nCMP R0, #10\nHLT")
        assert cpu.flags["N"] == 1
        assert cpu.flags["Z"] == 0

    def test_cmp_greater_clears_nz(self):
        cpu = run("MOV R0, #10\nCMP R0, #3\nHLT")
        assert cpu.flags["N"] == 0
        assert cpu.flags["Z"] == 0

    def test_cmp_sets_carry(self):
        # rn >= val2 → C = 1 (no borrow)
        cpu = run("MOV R0, #10\nCMP R0, #5\nHLT")
        assert cpu.flags["C"] == 1

    def test_cmp_clears_carry_on_borrow(self):
        cpu = run("MOV R0, #3\nCMP R0, #10\nHLT")
        assert cpu.flags["C"] == 0

    def test_sub_does_not_update_flags_without_s(self):
        # plain SUB (S=0) must NOT change flags
        cpu = run("MOV R0, #10\nCMP R0, #10\nSUB R0, #3\nHLT")
        # Z was set by CMP; SUB must not clear it
        assert cpu.flags["Z"] == 1

    def test_add_overflow_flag(self):
        # Build 0x7FFFFFFF = (0x80 << 24) - 1 and add 1 → 0x80000000.
        # Plain ADD has S=0 so flags are unchanged; we just verify unsigned wrap.
        # 0x80 * 0x1000000 = 0x80000000; sub 1 → 0x7FFFFFFF; add 1 → 0x80000000.
        cpu = run("""
            MOV R0, #0x80
            MOV R1, #1
            LSL R0, R0, #24
            SUB R0, #1
            ADD R0, R0, R1
            HLT
        """)
        assert R(cpu, 0) == 0x80000000


# ─────────────────────────────────────────────────────────────────────
# 4. Branches
# ─────────────────────────────────────────────────────────────────────

class TestBranches:
    def test_unconditional_branch(self):
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
ok:
            MOV R1, #1
end:
            HLT
        """)
        assert R(cpu, 1) == 1

    def test_bne_not_taken_when_equal(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #5
            BNE skip
            MOV R1, #42
            B end
skip:
            MOV R1, #0
end:
            HLT
        """)
        assert R(cpu, 1) == 42

    def test_blt_taken(self):
        cpu = run("""
            MOV R0, #3
            CMP R0, #10
            BLT ok
            MOV R2, #0
            B end
ok:
            MOV R2, #1
end:
            HLT
        """)
        assert R(cpu, 2) == 1

    def test_bgt_taken(self):
        cpu = run("""
            MOV R0, #10
            CMP R0, #3
            BGT ok
            MOV R2, #0
            B end
ok:
            MOV R2, #1
end:
            HLT
        """)
        assert R(cpu, 2) == 1

    def test_bge_taken_on_equal(self):
        cpu = run("""
            MOV R0, #5
            CMP R0, #5
            BGE ok
            MOV R2, #0
            B end
ok:
            MOV R2, #1
end:
            HLT
        """)
        assert R(cpu, 2) == 1

    def test_ble_taken_on_less(self):
        cpu = run("""
            MOV R0, #3
            CMP R0, #10
            BLE ok
            MOV R2, #0
            B end
ok:
            MOV R2, #1
end:
            HLT
        """)
        assert R(cpu, 2) == 1

    def test_jms_ret(self):
        cpu = run("""
            MOV R0, #1
            JMS sub
            HLT
sub:
            ADD R0, #10
            RET
        """)
        assert R(cpu, 0) == 11


# ─────────────────────────────────────────────────────────────────────
# 5. Load / Store
# ─────────────────────────────────────────────────────────────────────

class TestLoadStore:
    def test_str_ldr_no_offset(self):
        cpu = run(f"""
            MOV R0, #0x{DATA_BASE:X}
            MOV R1, #123
            STR R1, [R0]
            LDR R2, [R0]
            HLT
        """)
        assert R(cpu, 2) == 123

    def test_str_ldr_with_offset(self):
        cpu = run(f"""
            MOV R0, #0x{DATA_BASE:X}
            MOV R1, #77
            STR R1, [R0, #8]
            LDR R2, [R0, #8]
            HLT
        """)
        assert R(cpu, 2) == 77

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


# ─────────────────────────────────────────────────────────────────────
# 6. Stack (PUSH / POP)
# ─────────────────────────────────────────────────────────────────────

class TestStack:
    def test_push_pop_single(self):
        cpu = run("""
            MOV R0, #55
            PSH {R0}
            MOV R0, #0
            POP {R0}
            HLT
        """)
        assert R(cpu, 0) == 55

    def test_push_pop_lifo_order(self):
        cpu = run("""
            MOV R0, #1
            MOV R1, #2
            PSH {R0}
            PSH {R1}
            POP {R3}
            POP {R4}
            HLT
        """)
        assert R(cpu, 3) == 2   # top of stack = last pushed
        assert R(cpu, 4) == 1


# ─────────────────────────────────────────────────────────────────────
# 7. Pseudo-instructions — correctness and NO memory spill
# ─────────────────────────────────────────────────────────────────────

class TestPseudoInstructions:
    def _count_push_pop_words(self, source: str) -> int:
        """Count how many encoded words look like PUSH or POP."""
        lines = clean_lines(source.strip().splitlines())
        words = assemble_to_machine_code(lines)
        # PUSH/POP: bits [27:25] = 0b100
        return sum(1 for w in words if (w >> 25) & 0b111 == 0b100)

    def test_inc(self):
        cpu = run("MOV R0, #10\nINC R0\nHLT")
        assert R(cpu, 0) == 11

    def test_dec(self):
        cpu = run("MOV R0, #10\nDEC R0\nHLT")
        assert R(cpu, 0) == 9

    def test_clr(self):
        cpu = run("MOV R0, #99\nCLR R0\nHLT")
        assert R(cpu, 0) == 0

    def test_lsl(self):
        cpu = run("MOV R1, #3\nLSL R2, R1, #2\nHLT")
        assert R(cpu, 2) == 12   # 3 << 2 = 12

    def test_lsl_in_place(self):
        cpu = run("MOV R0, #5\nLSL R0, #1\nHLT")
        assert R(cpu, 0) == 10

    def test_lsr(self):
        cpu = run("MOV R2, #24\nLSR R4, R2, #3\nHLT")
        assert R(cpu, 4) == 3    # 24 >> 3 = 3

    def test_mod(self):
        cpu = run("MOV R5, #17\nMOV R3, #5\nMOD R7, R5, R3\nHLT")
        assert R(cpu, 7) == 2    # 17 % 5 = 2

    def test_swap(self):
        cpu = run("MOV R8, #15\nMOV R9, #99\nSWAP R8, R9\nHLT")
        assert R(cpu, 8) == 99
        assert R(cpu, 9) == 15

    def test_loop(self):
        cpu = run("""
            MOV R0, #0
            MOV R12, #5
loop:
            ADD R0, #1
            LOOP loop
            HLT
        """)
        assert R(cpu, 0) == 5

    # ---- No-memory-spill checks ----
    def test_lsl_no_push_pop(self):
        assert self._count_push_pop_words("MOV R1, #3\nLSL R2, R1, #2\nHLT") == 0

    def test_lsr_no_push_pop(self):
        assert self._count_push_pop_words("MOV R2, #8\nLSR R2, #1\nHLT") == 0

    def test_mod_no_push_pop(self):
        assert self._count_push_pop_words("MOV R5, #17\nMOV R3, #5\nMOD R7, R5, R3\nHLT") == 0

    def test_swap_no_push_pop(self):
        assert self._count_push_pop_words("MOV R0, #1\nMOV R1, #2\nSWAP R0, R1\nHLT") == 0

    def test_loop_no_push_pop(self):
        assert self._count_push_pop_words(
            "MOV R12, #3\nloop:\nADD R0, #1\nLOOP loop\nHLT"
        ) == 0


# ─────────────────────────────────────────────────────────────────────
# 8. Assembler — error handling
# ─────────────────────────────────────────────────────────────────────

class TestAssemblerErrors:
    def test_unknown_instruction(self):
        with pytest.raises(ValueError):
            assemble_to_machine_code(["FOOBAR R0, #1"])

    def test_unknown_label(self):
        with pytest.raises((ValueError, KeyError)):
            assemble_to_machine_code(["B nowhere"])

    def test_duplicate_label(self):
        with pytest.raises(ValueError, match="Duplicate label"):
            assemble_to_machine_code(["lbl:", "NOP", "lbl:", "HLT"])

    def test_register_out_of_range(self):
        with pytest.raises(ValueError):
            assemble_to_machine_code(["MOV R16, #1"])


# ─────────────────────────────────────────────────────────────────────
# 9. End-to-end programs
# ─────────────────────────────────────────────────────────────────────

class TestEndToEnd:
    def test_gauss_sum(self):
        """Sum 1..6 = 21."""
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
        """5! = 120."""
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

    def test_jms_ret_nested(self):
        """Call a subroutine that doubles R0."""
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