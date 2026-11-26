"""Execution semantics of variant 13 memory instructions."""


def load_constant(memory, operands):
    """Store the B constant at the C address."""
    value, destination = operands
    memory.write(destination, value)


def copy_memory(memory, operands):
    """Copy M[C] to M[B], as specified for both read and write."""
    destination, source = operands
    memory.write(destination, memory.read(source))


HANDLERS = {
    "LOAD_CONST": load_constant,
    "READ_MEM": copy_memory,
    "WRITE_MEM": copy_memory,
}
