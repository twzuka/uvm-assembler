"""Check reference fields, grammar, and unsigned operand boundaries."""

from pathlib import Path
import unittest

from src.uvm.assembler import parse_source
from src.uvm.spec import BY_NAME, Instruction, MIN_UNSIGNED, UvmError

ROOT = Path(__file__).resolve().parents[1]


class AssemblerTests(unittest.TestCase):
    """Validate the stage 1 intermediate representation."""

    def test_reference_fields(self):
        """Reproduce every field sequence printed in the assignment."""
        source = (ROOT / "examples/spec_tests.asm").read_text("utf-8")
        descriptions = [item.describe() for item in parse_source(source)]
        self.assertEqual(descriptions, [
            "A=5, B=870, C=362",
            "A=14, B=805, C=879",
            "A=9, B=594, C=839",
            "A=3, B=318, C=533, D=743, E=571",
        ])

    def test_comments_case_and_hex(self):
        """Accept readable assembly with decimal and hexadecimal operands."""
        source = "\n; comment\n load_const 0x366, 0362 ; value\n"
        self.assertEqual(parse_source(source)[0].operands, (870, 362))

    def test_invalid_source(self):
        """Reject malformed syntax, unknown commands, and invalid ranges."""
        cases = (
            "UNKNOWN 1, 2", "LOAD_CONST", "LOAD_CONST 1",
            "LOAD_CONST 1, 2, 3", "LOAD_CONST 1 2", "LOAD_CONST -1, 2",
            "LOAD_CONST 1.5, 2", "LOAD_CONST 1,", "LOAD_CONST 0x, 2",
            "LOAD_CONST 67108864, 2", "READ_MEM 2147483648, 0",
            "EQ 8192, 0, 0, 0",
        )
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(UvmError, "Строка 1"):
                    parse_source(source)

    def test_all_field_boundaries(self):
        """Accept zero and maxima; reject negative and overflowing fields."""
        for spec in BY_NAME.values():
            for index, width in enumerate(spec.widths):
                for value in (0, (1 << width) - 1, -1, 1 << width, True):
                    operands = [0] * len(spec.widths)
                    operands[index] = value
                    with self.subTest(name=spec.name, index=index, val=value):
                        if (type(value) is int
                                and MIN_UNSIGNED <= value < (1 << width)):
                            Instruction(spec, tuple(operands))
                        else:
                            with self.assertRaises(UvmError):
                                Instruction(spec, tuple(operands))

    def test_empty_source(self):
        """An empty program has an empty intermediate representation."""
        self.assertEqual(parse_source("; only a comment\n"), [])
