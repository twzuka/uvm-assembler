"""Execution semantics of variant 13 memory instructions."""


def load_constant(memory, operands):
    """Store the B constant at the C address."""
    value, destination = operands
    memory.write(destination, value)


def copy_memory(memory, operands):
    """Copy M[C] to M[B], as specified for both read and write."""
    destination, source = operands
    memory.write(destination, memory.read(source))


def compare_equal(memory, operands):
    """Store 1 iff M[C] equals M[M[D] + B], otherwise store 0 at E."""
    offset, first_address, pointer_address, destination = operands
    first = memory.read(first_address)
    second_address = memory.read(pointer_address) + offset
    second = memory.read(second_address)
    memory.write(destination, int(first == second))


HANDLERS = {
    "LOAD_CONST": load_constant,
    "READ_MEM": copy_memory,
    "WRITE_MEM": copy_memory,
    "EQ": compare_equal,
}
