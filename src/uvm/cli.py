"""Command line interface for the variant 13 assembler."""

import argparse
import json
from pathlib import Path
import sys

from .assembler import parse_number, parse_source
from .codec import encode_instruction, encode_program
from .machine import Machine
from .memory import check_range
from .spec import UvmError

ERROR_STATUS = 1


def make_parser():
    """Define the assembler input, binary output, and test mode."""
    parser = argparse.ArgumentParser(description="УВМ, вариант 13")
    commands = parser.add_subparsers(dest="command", required=True)
    assembler = commands.add_parser("assemble", help="Собрать программу")
    assembler.add_argument("source", type=Path, help="Исходный файл .asm")
    assembler.add_argument("output", type=Path, help="Бинарный файл результата")
    assembler.add_argument("--test", action="store_true", help="Вывести байты")
    runner = commands.add_parser("run", help="Выполнить машинный код")
    runner.add_argument("binary", type=Path, help="Бинарная программа")
    runner.add_argument("dump", type=Path, help="Файл дампа JSON")
    runner.add_argument("--start", type=parse_number, required=True)
    runner.add_argument("--end", type=parse_number, required=True)
    return parser


def assemble(args):
    """Write machine code, report its byte count, and optionally print bytes."""
    if args.source.resolve() == args.output.resolve():
        raise UvmError("Исходный файл и результат должны различаться")
    program = parse_source(args.source.read_text(encoding="utf-8-sig"))
    binary = encode_program(program)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(binary)
    if args.test:
        for instruction in program:
            encoded = encode_instruction(instruction)
            print(", ".join(f"0x{value:02X}" for value in encoded))
    print(f"Размер двоичного файла: {len(binary)} байт")


def run(args):
    """Run the binary and save an inclusive JSON memory dump."""
    if args.binary.resolve() == args.dump.resolve():
        raise UvmError("Бинарный файл и дамп должны различаться")
    check_range(args.start, args.end)
    machine = Machine(args.binary.read_bytes())
    memory = machine.run()
    document = {
        "start": args.start,
        "end": args.end,
        "memory": memory.dump(args.start, args.end),
    }
    args.dump.parent.mkdir(parents=True, exist_ok=True)
    args.dump.write_text(json.dumps(document, indent=2) + "\n",
                         encoding="utf-8")
    print(f"Дамп памяти [{args.start}, {args.end}]: {args.dump}")


def main(argv=None):
    """Run the CLI and report expected failures without a Python traceback."""
    args = make_parser().parse_args(argv)
    try:
        if args.command == "assemble":
            assemble(args)
        else:
            run(args)
    except (OSError, UnicodeError, UvmError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return ERROR_STATUS
    return 0
