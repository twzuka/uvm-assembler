"""Exercise the CLI through its public entry point."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from src.uvm.cli import main


class CliTests(unittest.TestCase):
    """Check assembler inputs and readable failures."""

    def test_stage_one_fields(self):
        """Stage 1 prints fields and does not produce a binary file."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.asm"
            output = Path(directory) / "program.bin"
            source.write_text("LOAD_CONST 870, 362", encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream):
                status = main(["assemble", str(source), str(output), "--test"])
            self.assertEqual(status, 0)
            self.assertIn("A=5, B=870, C=362", stream.getvalue())
            self.assertFalse(output.exists())

    def test_missing_input(self):
        """A missing source gives a nonzero status and a concise error."""
        with tempfile.TemporaryDirectory() as directory:
            missing = str(Path(directory) / "missing.asm")
            stream = io.StringIO()
            with redirect_stderr(stream):
                status = main(["assemble", missing, missing + ".bin"])
            self.assertEqual(status, 1)
            self.assertIn("Ошибка:", stream.getvalue())
