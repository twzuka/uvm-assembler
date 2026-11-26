"""Exercise actual programs through the fetch/decode/execute cycle."""

from pathlib import Path
import unittest

from src.uvm.assembler import parse_source
from src.uvm.codec import encode_program
from src.uvm.machine import Machine
from src.uvm.spec import MAX_ADDRESS, UvmError

ROOT = Path(__file__).resolve().parents[1]


def run_source(source):
    """Assemble text and execute its encoded form."""
    machine = Machine(encode_program(parse_source(source)))
    machine.run()
    return machine


class MachineTests(unittest.TestCase):
    """Check baseline memory operations and malformed machine code."""

    def test_load_and_both_copy_operations(self):
        """Both READ_MEM and WRITE_MEM implement M[B] = M[C]."""
        machine = run_source(
            "LOAD_CONST 870, 1000\n"
            "READ_MEM 1001, 1000\n"
            "WRITE_MEM 1002, 1001"
        )
        self.assertEqual([machine.memory.read(i) for i in range(1000, 1003)],
                         [870, 870, 870])
        self.assertEqual(machine.pc, 26)

    def test_array_copy_example(self):
        """The stage 3 program preserves and copies every source element."""
        source = (ROOT / "examples/copy_array.asm").read_text("utf-8")
        machine = run_source(source)
        expected = [0, 17, 116, 67108863, 42]
        for base in (1000, 1100):
            self.assertEqual([machine.memory.read(base + i) for i in range(5)],
                             expected)

    def test_zero_uninitialized_and_self_copy(self):
        """Unset cells read as zero; copying a cell onto itself is valid."""
        machine = run_source(
            "LOAD_CONST 42, 1000\n"
            "WRITE_MEM 1000, 1000\n"
            "READ_MEM 1001, 2000"
        )
        self.assertEqual(machine.memory.read(1000), 42)
        self.assertEqual(machine.memory.read(1001), 0)

    def test_maximum_address(self):
        """The largest encodable address is executable."""
        machine = run_source(f"LOAD_CONST 7, {MAX_ADDRESS}")
        self.assertEqual(machine.memory.read(MAX_ADDRESS), 7)

    def test_empty_binary(self):
        """An empty program terminates with zero-initialized memory."""
        machine = Machine(b"")
        machine.run()
        self.assertEqual(machine.pc, 0)
        self.assertEqual(machine.memory.read(1000), 0)

    def test_bad_machine_code(self):
        """Invalid opcodes and truncated instructions report their address."""
        for binary in (b"\x00", b"\x05"):
            with self.assertRaisesRegex(UvmError, "Адрес команды 0"):
                Machine(binary).run()

    def test_future_instruction_can_be_modified(self):
        """A write changes a future operand in the same memory used to fetch."""
        machine = run_source("LOAD_CONST 117, 8\nLOAD_CONST 0, 1000")
        self.assertEqual(machine.memory.read(1000), 7)

    def test_nonbyte_instruction_cell(self):
        """A data value larger than a byte is not a valid fetched opcode."""
        with self.assertRaisesRegex(UvmError, "не являющееся байтом"):
            run_source("LOAD_CONST 256, 8\nLOAD_CONST 0, 1000")

    def test_eq_not_implemented_at_stage_three(self):
        """The stage 3 VM explicitly rejects the stage 4 operation."""
        with self.assertRaisesRegex(UvmError, "ещё не поддерживается"):
            run_source("EQ 0, 1000, 1100, 1200")
