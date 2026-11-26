"""Exercise the CLI through its public entry point."""

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from src.uvm.cli import main


class CliTests(unittest.TestCase):
    """Check assembler inputs and readable failures."""

    def test_binary_output(self):
        """Test mode prints reference bytes and reports the output size."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.asm"
            output = Path(directory) / "program.bin"
            source.write_text("LOAD_CONST 870, 362", encoding="utf-8")
            stream = io.StringIO()
            with redirect_stdout(stream):
                status = main(["assemble", str(source), str(output), "--test"])
            self.assertEqual(status, 0)
            expected = bytes.fromhex("65 36 00 80 5A 00 00 00")
            self.assertEqual(output.read_bytes(), expected)
            self.assertIn("0x65, 0x36, 0x00, 0x80", stream.getvalue())
            self.assertIn("Размер двоичного файла: 8 байт", stream.getvalue())

    def test_preserve_source(self):
        """Reject the same source and output before overwriting assembly."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.asm"
            text = "LOAD_CONST 1, 1000"
            source.write_text(text, encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                status = main(["assemble", str(source), str(source)])
            self.assertEqual(status, 1)
            self.assertEqual(source.read_text("utf-8"), text)

    def test_invalid_source_does_not_write(self):
        """Syntax errors do not replace an existing binary result."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.asm"
            output = Path(directory) / "program.bin"
            source.write_text("LOAD_CONST -1, 0", encoding="utf-8")
            output.write_bytes(b"existing")
            with redirect_stderr(io.StringIO()):
                status = main(["assemble", str(source), str(output)])
            self.assertEqual(status, 1)
            self.assertEqual(output.read_bytes(), b"existing")

    def test_missing_input(self):
        """A missing source gives a nonzero status and a concise error."""
        with tempfile.TemporaryDirectory() as directory:
            missing = str(Path(directory) / "missing.asm")
            stream = io.StringIO()
            with redirect_stderr(stream):
                status = main(["assemble", missing, missing + ".bin"])
            self.assertEqual(status, 1)
            self.assertIn("Ошибка:", stream.getvalue())
