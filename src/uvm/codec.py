"""Encode and decode packed little-endian variant 13 instructions."""

from .spec import BY_OPCODE, Instruction, OPCODE_BITS, UvmError

OPCODE_MASK = (1 << OPCODE_BITS) - 1


def encode_instruction(instruction):
    """Pack unsigned fields from the least significant bit upward."""
    packed = instruction.spec.opcode
    shift = OPCODE_BITS
    for value, width in zip(instruction.operands, instruction.spec.widths):
        packed |= value << shift
        shift += width
    return packed.to_bytes(instruction.spec.size, byteorder="little")


def encode_program(program):
    """Concatenate variable-length instructions without headers or gaps."""
    return b"".join(encode_instruction(item) for item in program)


def spec_for_byte(first_byte):
    """Look up an instruction by the low four bits of its first byte."""
    opcode = first_byte & OPCODE_MASK
    if opcode not in BY_OPCODE:
        raise UvmError(f"Неизвестный код операции A={opcode}")
    return BY_OPCODE[opcode]


def decode_instruction(data):
    """Unpack one complete instruction and reject nonzero reserved bits."""
    if not data:
        raise UvmError("Отсутствует команда")
    spec = spec_for_byte(data[0])
    if len(data) != spec.size:
        raise UvmError(f"{spec.name}: требуется {spec.size} байт")
    packed = int.from_bytes(data, byteorder="little") >> OPCODE_BITS
    operands = []
    for width in spec.widths:
        operands.append(packed & ((1 << width) - 1))
        packed >>= width
    if packed:
        raise UvmError("Неиспользуемые старшие биты команды не равны нулю")
    return Instruction(spec, tuple(operands))
