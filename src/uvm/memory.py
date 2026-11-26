"""Unified sparse memory for instructions and nonnegative integer data."""

from .spec import MAX_ADDRESS, MIN_UNSIGNED, UvmError

BYTE_LIMIT = 1 << 8


def check_address(address):
    """Reject addresses outside the 31-bit unsigned address space."""
    if (type(address) is not int
            or not MIN_UNSIGNED <= address <= MAX_ADDRESS):
        raise UvmError(f"Адрес вне диапазона 0..{MAX_ADDRESS}: {address}")


def check_range(start, end):
    """Validate an inclusive memory dump range."""
    check_address(start)
    check_address(end)
    if start > end:
        raise UvmError("Начало диапазона должно быть не больше конца")


class Memory:
    """Store code and data in the same address space; unset cells are zero."""

    def __init__(self):
        """Create an empty address space without allocating 2**31 cells."""
        self._cells = {}

    def read(self, address):
        """Return an integer cell, defaulting to zero."""
        check_address(address)
        return self._cells.get(address, 0)

    def write(self, address, value):
        """Write a nonnegative integer to a shared code or data cell."""
        check_address(address)
        if type(value) is not int or value < MIN_UNSIGNED:
            raise UvmError("Ячейка памяти должна содержать целое число >= 0")
        self._cells[address] = value

    def load(self, binary):
        """Load each program byte into one cell starting at address zero."""
        if binary:
            check_address(len(binary) - 1)
        for address, value in enumerate(binary):
            self.write(address, value)

    def read_bytes(self, start, size):
        """Fetch instruction bytes from the current shared memory contents."""
        values = [self.read(start + offset) for offset in range(size)]
        if any(value >= BYTE_LIMIT for value in values):
            raise UvmError("Команда содержит значение, не являющееся байтом")
        return bytes(values)

    def dump(self, start, end):
        """Return an inclusive range with JSON-compatible string keys."""
        check_range(start, end)
        return {str(address): self.read(address)
                for address in range(start, end + 1)}
