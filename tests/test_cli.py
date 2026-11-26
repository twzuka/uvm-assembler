"""Exercise the CLI through its public entry point."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
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

    def test_interpreter_json_dump(self):
        """Run an assembled program and read its actual JSON output."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.asm"
            binary = Path(directory) / "program.bin"
            dump = Path(directory) / "dump.json"
            source.write_text("LOAD_CONST 116, 1000", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main([
                    "assemble", str(source), str(binary),
                ]), 0)
                self.assertEqual(main([
                    "run", str(binary), str(dump),
                    "--start", "999", "--end", "1001",
                ]), 0)
            self.assertEqual(json.loads(dump.read_text("utf-8")), {
                "start": 999, "end": 1001,
                "memory": {"999": 0, "1000": 116, "1001": 0},
            })

    def test_interpreter_errors_preserve_dump(self):
        """Failed execution or a reversed range does not replace a dump."""
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "bad.bin"
            dump = Path(directory) / "dump.json"
            binary.write_bytes(b"\x00")
            dump.write_text("existing", encoding="utf-8")
            for start, end in (("0", "10"), ("10", "0")):
                with redirect_stderr(io.StringIO()):
                    status = main([
                        "run", str(binary), str(dump),
                        "--start", start, "--end", end,
                    ])
                self.assertEqual(status, 1)
                self.assertEqual(dump.read_text("utf-8"), "existing")

    def test_preserve_binary_when_dump_path_matches(self):
        """A dump cannot overwrite its binary input."""
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "program.bin"
            binary.write_bytes(bytes.fromhex("05 00 00 00 FA 00 00 00"))
            original = binary.read_bytes()
            with redirect_stderr(io.StringIO()):
                status = main([
                    "run", str(binary), str(binary),
                    "--start", "1000", "--end", "1000",
                ])
            self.assertEqual(status, 1)
            self.assertEqual(binary.read_bytes(), original)
