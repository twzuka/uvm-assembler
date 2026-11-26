"""Validate shared memory cells, byte fetches, and dump boundaries."""

import unittest

from src.uvm.memory import Memory, check_range
from src.uvm.spec import MAX_ADDRESS, UvmError


class MemoryTests(unittest.TestCase):
    """Cover address validation and sparse unified storage."""

    def test_uninitialized_and_high_addresses(self):
        """Access the maximum address without a huge backing allocation."""
        memory = Memory()
        self.assertEqual(memory.read(MAX_ADDRESS), 0)
        memory.write(MAX_ADDRESS, 67108863)
        self.assertEqual(memory.read(MAX_ADDRESS), 67108863)

    def test_invalid_addresses(self):
        """Reject negative, overflowing, fractional, and boolean addresses."""
        memory = Memory()
        for address in (-1, MAX_ADDRESS + 1, 1.5, True):
            with self.subTest(address=address):
                with self.assertRaises(UvmError):
                    memory.read(address)
                with self.assertRaises(UvmError):
                    memory.write(address, 0)

    def test_invalid_values(self):
        """A memory cell must hold a nonnegative integer."""
        memory = Memory()
        for value in (-1, 1.5, True):
            with self.assertRaises(UvmError):
                memory.write(1000, value)

    def test_dump_is_inclusive(self):
        """Include both endpoints and zero-valued cells in JSON mapping."""
        memory = Memory()
        memory.write(11, 116)
        self.assertEqual(memory.dump(10, 12),
                         {"10": 0, "11": 116, "12": 0})
        self.assertEqual(memory.dump(MAX_ADDRESS, MAX_ADDRESS),
                         {str(MAX_ADDRESS): 0})

    def test_invalid_ranges(self):
        """Validate each endpoint and their order."""
        for start, end in ((2, 1), (-1, 0), (0, MAX_ADDRESS + 1)):
            with self.assertRaises(UvmError):
                check_range(start, end)

    def test_code_and_data_share_storage(self):
        """Data writes are immediately visible to instruction byte fetch."""
        memory = Memory()
        memory.load(b"\x05\x00")
        memory.write(1, 14)
        self.assertEqual(memory.read_bytes(0, 2), b"\x05\x0e")
        memory.write(1, 256)
        with self.assertRaisesRegex(UvmError, "не являющееся байтом"):
            memory.read_bytes(0, 2)
