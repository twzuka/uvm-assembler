"""Fetch, decode, and execute instructions from unified memory."""

from .codec import decode_instruction, spec_for_byte
from .memory import Memory
from .operations import HANDLERS
from .spec import UvmError


class Machine:
    """Run a binary until its program counter reaches the input file size."""

    def __init__(self, binary):
        """Load code at address zero and remember only its original length."""
        self.memory = Memory()
        self.memory.load(binary)
        self.code_size = len(binary)
        self.pc = 0

    def step(self):
        """Fetch current bytes, decode their fields, and execute one command."""
        try:
            first = self.memory.read_bytes(self.pc, 1)[0]
            spec = spec_for_byte(first)
            if self.pc + spec.size > self.code_size:
                raise UvmError("Неполная команда в конце программы")
            data = self.memory.read_bytes(self.pc, spec.size)
            instruction = decode_instruction(data)
            handler = HANDLERS.get(instruction.spec.name)
            if handler is None:
                raise UvmError(f"Команда {spec.name} ещё не поддерживается")
            handler(self.memory, instruction.operands)
        except UvmError as error:
            raise UvmError(f"Адрес команды {self.pc}: {error}") from error
        self.pc += spec.size

    def run(self):
        """Execute sequentially; the ISA has no jumps or HALT instruction."""
        while self.pc < self.code_size:
            self.step()
        return self.memory
