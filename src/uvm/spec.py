"""Instruction fields from variant 13, pages 56-57 of the assignment."""

from dataclasses import dataclass

OPCODE_BITS = 4
MIN_UNSIGNED = 0
ADDRESS_BITS = 31
MAX_ADDRESS = (1 << ADDRESS_BITS) - 1
FIELD_NAMES = ("A", "B", "C", "D", "E")


class UvmError(ValueError):
    """Report invalid assembly, machine code, or virtual machine state."""


@dataclass(frozen=True)
class CommandSpec:
    """Describe the opcode, operand widths, and encoded instruction size."""

    name: str
    opcode: int
    widths: tuple[int, ...]
    size: int


SPECS = (
    CommandSpec("LOAD_CONST", 5, (26, 31), 8),
    CommandSpec("READ_MEM", 14, (31, 31), 9),
    CommandSpec("WRITE_MEM", 9, (31, 31), 9),
    CommandSpec("EQ", 3, (13, 31, 31, 31), 14),
)
BY_NAME = {spec.name: spec for spec in SPECS}
BY_OPCODE = {spec.opcode: spec for spec in SPECS}


@dataclass(frozen=True)
class Instruction:
    """Store a validated instruction in its intermediate representation."""

    spec: CommandSpec
    operands: tuple[int, ...]

    def __post_init__(self):
        """Reject missing operands and numbers outside their unsigned fields."""
        if len(self.operands) != len(self.spec.widths):
            raise UvmError(f"{self.spec.name}: неверное число аргументов")
        fields = zip(FIELD_NAMES[1:], self.operands, self.spec.widths)
        for name, value, width in fields:
            if (type(value) is not int
                    or not MIN_UNSIGNED <= value < (1 << width)):
                raise UvmError(
                    f"Поле {name}: требуется целое от 0 до {(1 << width) - 1}"
                )

    def fields(self):
        """Return the field names and values in the specification's order."""
        values = (self.spec.opcode,) + self.operands
        return dict(zip(FIELD_NAMES, values))

    def describe(self):
        """Format the intermediate representation like the reference tests."""
        return ", ".join(f"{key}={val}" for key, val in self.fields().items())
