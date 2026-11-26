"""Verify all three final tasks using real command line subprocesses."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "mixed": ([116, 0, 115, 116, 117, 42, 116], [1, 0, 0, 1, 0, 0, 1]),
    "all_equal": ([116] * 7, [1] * 7),
    "no_equal": ([0, 1, 115, 117, 255, 65536, 67108863], [0] * 7),
}


def execute_example(name, directory):
    """Assemble and execute via independent CLI processes, then load JSON."""
    binary = Path(directory) / f"{name}.bin"
    dump = Path(directory) / f"{name}.json"
    base = [sys.executable, "-X", "utf8", "-B", "-m", "src.uvm"]
    subprocess.run(
        base + ["assemble", f"examples/vector_{name}.asm", str(binary)],
        cwd=ROOT, check=True, capture_output=True,
    )
    subprocess.run(
        base + ["run", str(binary), str(dump),
                "--start", "1000", "--end", "1206"],
        cwd=ROOT, check=True, capture_output=True,
    )
    return binary.read_bytes(), json.loads(dump.read_text("utf-8"))


class ExampleTests(unittest.TestCase):
    """Check observable files, preserved inputs, and all vector results."""

    def test_three_vector_programs(self):
        """Three 170-byte programs produce correct independent JSON dumps."""
        with tempfile.TemporaryDirectory() as directory:
            for name, (vector, expected) in CASES.items():
                with self.subTest(example=name):
                    binary, dump = execute_example(name, directory)
                    memory = dump["memory"]
                    original = [memory[str(1000 + i)] for i in range(7)]
                    result = [memory[str(1200 + i)] for i in range(7)]
                    self.assertEqual(len(binary), 170)
                    self.assertEqual((dump["start"], dump["end"]),
                                     (1000, 1206))
                    self.assertEqual(original, vector)
                    self.assertEqual(result, expected)
                    self.assertEqual(memory["1100"], 116)
                    self.assertEqual(memory["1101"], 1000)

    def test_launcher_outside_repository(self):
        """The launcher finds source modules from another working directory."""
        with tempfile.TemporaryDirectory(prefix="uvm test ") as directory:
            binary = Path(directory) / "program.bin"
            launcher = [str(ROOT / "run.bat")] if os.name == "nt" else [
                "sh", str(ROOT / "run.sh"),
            ]
            environment = dict(os.environ, PYTHON=sys.executable,
                               PYTHONUTF8="1")
            subprocess.run(
                launcher + ["assemble",
                            str(ROOT / "examples/spec_tests.asm"),
                            str(binary)],
                cwd=directory, env=environment, check=True,
                capture_output=True,
            )
            self.assertEqual(len(binary.read_bytes()), 40)
