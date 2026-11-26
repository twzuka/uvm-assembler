"""Command line interface for the stage 1 assembler."""

import argparse
from pathlib import Path
import sys

from .assembler import parse_source
from .spec import UvmError

ERROR_STATUS = 1


def make_parser():
    """Define the assembler inputs required by stage 1."""
    parser = argparse.ArgumentParser(description="УВМ, вариант 13")
    commands = parser.add_subparsers(dest="command", required=True)
    assembler = commands.add_parser("assemble", help="Разобрать ассемблер")
    assembler.add_argument("source", type=Path, help="Исходный файл .asm")
    assembler.add_argument("output", type=Path, help="Бинарный файл результата")
    assembler.add_argument("--test", action="store_true", help="Вывести поля")
    return parser


def assemble(args):
    """Parse assembly and display fields without creating stage 2 output."""
    program = parse_source(args.source.read_text(encoding="utf-8-sig"))
    if args.test:
        for instruction in program:
            print(instruction.describe())
    print("Этап 1: программа разобрана; машинный код появится на этапе 2.")


def main(argv=None):
    """Run the CLI and report expected failures without a Python traceback."""
    args = make_parser().parse_args(argv)
    try:
        assemble(args)
    except (OSError, UnicodeError, UvmError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return ERROR_STATUS
    return 0
