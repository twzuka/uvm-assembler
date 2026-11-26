"""Parse mnemonic-based assembly into validated instructions."""

import re

from .spec import BY_NAME, Instruction, UvmError

MNEMONIC_WITH_OPERANDS = 2
NUMBER = re.compile(r"(?:[0-9]+|0[xX][0-9a-fA-F]+)\Z")


def parse_number(token):
    """Read an unsigned decimal or hexadecimal integer without truncation."""
    token = token.strip()
    if not NUMBER.fullmatch(token):
        raise UvmError(f"Некорректное целое число: {token!r}")
    base = 16 if token.lower().startswith("0x") else 10
    return int(token, base)


def parse_line(line):
    """Parse one nonempty instruction, preserving the operand field order."""
    parts = line.split(maxsplit=1)
    name = parts[0].upper()
    if name not in BY_NAME:
        raise UvmError(f"Неизвестная команда: {parts[0]}")
    tokens = (parts[1].split(",")
              if len(parts) == MNEMONIC_WITH_OPERANDS else [])
    operands = tuple(parse_number(token) for token in tokens)
    return Instruction(BY_NAME[name], operands)


def parse_source(source):
    """Parse a whole program, allowing blank lines and semicolon comments."""
    program = []
    for line_number, original in enumerate(source.splitlines(), start=1):
        line = original.partition(";")[0].strip()
        if not line:
            continue
        try:
            program.append(parse_line(line))
        except (UvmError, ValueError) as error:
            raise UvmError(f"Строка {line_number}: {error}") from error
    return program
