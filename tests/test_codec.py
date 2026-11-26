"""Compare machine code with independent byte sequences from the PDF."""

from pathlib import Path
import random
import unittest

from src.uvm.assembler import parse_source
from src.uvm.codec import (
    decode_instruction, encode_instruction, encode_program,
)
from src.uvm.spec import BY_NAME, Instruction, UvmError

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_HEX = (
    "65 36 00 80 5A 00 00 00",
    "5E 32 00 00 78 1B 00 00 00",
    "29 25 00 00 38 1A 00 00 00",
    "E3 13 2A 04 00 00 E7 02 00 80 1D 01 00 00",
)


class CodecTests(unittest.TestCase):
    """Check bit layout, endianness, padding, and variable command sizes."""

    def test_reference_bytes(self):
        """Match all four reference commands byte for byte (40 bytes total)."""
        source = (ROOT / "examples/spec_tests.asm").read_text("utf-8")
        program = parse_source(source)
        expected = [bytes.fromhex(item) for item in REFERENCE_HEX]
        self.assertEqual([encode_instruction(item) for item in program],
                         expected)
        self.assertEqual(encode_program(program), b"".join(expected))
        self.assertEqual(len(encode_program(program)), 40)
        for data, instruction in zip(expected, program):
            self.assertEqual(decode_instruction(data), instruction)

    def test_field_round_trips(self):
        """Recover unsigned fields including every maximum and random value."""
        generator = random.Random(13)
        for spec in BY_NAME.values():
            samples = [tuple(0 for _ in spec.widths)]
            samples.append(tuple((1 << bits) - 1 for bits in spec.widths))
            samples.extend(
                tuple(generator.randrange(1 << bits) for bits in spec.widths)
                for _ in range(100)
            )
            for operands in samples:
                instruction = Instruction(spec, operands)
                self.assertEqual(decode_instruction(
                    encode_instruction(instruction)), instruction)

    def test_truncated_and_extra_bytes(self):
        """Require the exact size for each decoded instruction."""
        for reference in REFERENCE_HEX:
            data = bytes.fromhex(reference)
            for length in range(len(data)):
                with self.assertRaises(UvmError):
                    decode_instruction(data[:length])
            with self.assertRaises(UvmError):
                decode_instruction(data + b"\x00")

    def test_nonzero_reserved_bits(self):
        """Reject malformed instructions rather than ignoring high bits."""
        for reference in REFERENCE_HEX:
            data = bytearray.fromhex(reference)
            data[-1] |= 0x80
            with self.assertRaisesRegex(UvmError, "старшие биты"):
                decode_instruction(data)

    def test_unknown_opcode(self):
        """An unassigned operation code is an explicit error."""
        with self.assertRaisesRegex(UvmError, "A=0"):
            decode_instruction(b"\x00")

    def test_empty_program(self):
        """An empty source encodes to an empty binary."""
        self.assertEqual(encode_program([]), b"")
