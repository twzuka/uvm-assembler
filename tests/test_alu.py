"""Check equality, indirect addressing, and result storage."""

from pathlib import Path
import unittest

from src.uvm.assembler import parse_source
from src.uvm.codec import encode_program
from src.uvm.machine import Machine
from src.uvm.spec import MAX_ADDRESS, UvmError
from tests.test_machine import run_source

ROOT = Path(__file__).resolve().parents[1]


class AluTests(unittest.TestCase):
    """Exercise the exact EQ addressing rule from variant 13."""

    def test_eq_example(self):
        """The demonstration writes both true and false results to memory."""
        source = (ROOT / "examples/eq_demo.asm").read_text("utf-8")
        memory = run_source(source).memory
        self.assertEqual(memory.dump(1200, 1201), {"1200": 1, "1201": 0})

    def test_equal_unequal_zero_and_large_values(self):
        """Store integer 0/1 for equal and unequal whole-cell values."""
        for first, second in ((0, 0), (0, 1), (116, 116), (116, 115),
                              (67108863, 67108863), (65536, 0)):
            with self.subTest(first=first, second=second):
                memory = run_source(
                    f"LOAD_CONST {first}, 1000\n"
                    "LOAD_CONST 1100, 1001\n"
                    f"LOAD_CONST {second}, 1100\n"
                    "EQ 0, 1000, 1001, 1200"
                ).memory
                result = memory.read(1200)
                self.assertEqual(result, int(first == second))
                self.assertIs(type(result), int)

    def test_indirect_address_with_offset(self):
        """Use M[D]+B, rather than D+B, D, or M[D+B]."""
        memory = run_source(
            "LOAD_CONST 116, 1000\n"
            "LOAD_CONST 1100, 1001\n"
            "LOAD_CONST 116, 1103\n"
            "LOAD_CONST 115, 1100\n"
            "LOAD_CONST 117, 1004\n"
            "EQ 3, 1000, 1001, 1200"
        ).memory
        self.assertEqual(memory.read(1200), 1)

    def test_maximum_offset(self):
        """The largest 13-bit offset is added to the stored base address."""
        memory = run_source(
            "LOAD_CONST 116, 1000\n"
            "LOAD_CONST 2000, 1001\n"
            "LOAD_CONST 116, 10191\n"
            "EQ 8191, 1000, 1001, 1200"
        ).memory
        self.assertEqual(memory.read(1200), 1)

    def test_result_may_alias_an_operand(self):
        """Read both operands before writing a possibly overlapping result."""
        for destination in (1000, 1001, 1100):
            memory = run_source(
                "LOAD_CONST 116, 1000\n"
                "LOAD_CONST 1100, 1001\n"
                "LOAD_CONST 116, 1100\n"
                f"EQ 0, 1000, 1001, {destination}"
            ).memory
            self.assertEqual(memory.read(destination), 1)

    def test_effective_address_overflow(self):
        """Reject M[D]+B outside 31-bit memory, without wrapping around."""
        binary = encode_program(parse_source("EQ 1, 1000, 1001, 1200"))
        machine = Machine(binary)
        machine.memory.write(1001, MAX_ADDRESS)
        with self.assertRaisesRegex(UvmError, "Адрес вне диапазона"):
            machine.run()

    def test_maximum_effective_address(self):
        """Read a valid second operand at the highest memory address."""
        binary = encode_program(parse_source("EQ 1, 1000, 1001, 1200"))
        machine = Machine(binary)
        machine.memory.write(1000, 116)
        machine.memory.write(1001, MAX_ADDRESS - 1)
        machine.memory.write(MAX_ADDRESS, 116)
        machine.run()
        self.assertEqual(machine.memory.read(1200), 1)

    def test_comparison_is_not_byte_truncated(self):
        """Compare 26-bit values exactly rather than just their low byte."""
        memory = run_source(
            "LOAD_CONST 116, 1000\n"
            "LOAD_CONST 1100, 1001\n"
            "LOAD_CONST 372, 1100\n"
            "EQ 0, 1000, 1001, 1200"
        ).memory
        self.assertEqual(memory.read(1200), 0)
