"""Cursor-based binary stream reader for parsing Altium binary data."""

from __future__ import annotations

import struct
from io import BytesIO

from .exceptions import CorruptedDataError


class BinaryReader:
    """A cursor-based binary reader wrapping a bytes buffer.

    Provides typed read methods that advance an internal offset cursor.
    All multi-byte values are read as little-endian (Altium's native byte order).
    """

    def __init__(self, data: bytes | BytesIO):
        if isinstance(data, BytesIO):
            data = data.read()
        self._data = data
        self._offset = 0
        self._length = len(data)

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def length(self) -> int:
        return self._length

    def remaining(self) -> int:
        """Return number of bytes remaining from current offset."""
        return self._length - self._offset

    def is_eof(self) -> bool:
        return self._offset >= self._length

    def tell(self) -> int:
        return self._offset

    def seek(self, offset: int) -> None:
        if offset < 0 or offset > self._length:
            raise CorruptedDataError(f"Seek offset {offset} out of range [0, {self._length}]")
        self._offset = offset

    def skip(self, n: int) -> None:
        """Skip n bytes forward."""
        self._check_available(n)
        self._offset += n

    def peek(self, n: int) -> bytes:
        """Peek at n bytes without advancing cursor."""
        self._check_available(n)
        return self._data[self._offset:self._offset + n]

    def read_bytes(self, n: int) -> bytes:
        """Read exactly n raw bytes."""
        self._check_available(n)
        result = self._data[self._offset:self._offset + n]
        self._offset += n
        return result

    def read_remaining(self) -> bytes:
        """Read all remaining bytes."""
        result = self._data[self._offset:]
        self._offset = self._length
        return result

    def read_uint8(self) -> int:
        self._check_available(1)
        val = self._data[self._offset]
        self._offset += 1
        return val

    def read_int8(self) -> int:
        self._check_available(1)
        val = struct.unpack_from("<b", self._data, self._offset)[0]
        self._offset += 1
        return val

    def read_uint16(self) -> int:
        self._check_available(2)
        val = struct.unpack_from("<H", self._data, self._offset)[0]
        self._offset += 2
        return val

    def read_int16(self) -> int:
        self._check_available(2)
        val = struct.unpack_from("<h", self._data, self._offset)[0]
        self._offset += 2
        return val

    def read_uint32(self) -> int:
        self._check_available(4)
        val = struct.unpack_from("<I", self._data, self._offset)[0]
        self._offset += 4
        return val

    def read_int32(self) -> int:
        self._check_available(4)
        val = struct.unpack_from("<i", self._data, self._offset)[0]
        self._offset += 4
        return val

    def read_float32(self) -> float:
        self._check_available(4)
        val = struct.unpack_from("<f", self._data, self._offset)[0]
        self._offset += 4
        return val

    def read_float64(self) -> float:
        self._check_available(8)
        val = struct.unpack_from("<d", self._data, self._offset)[0]
        self._offset += 8
        return val

    def read_bool(self) -> bool:
        return self.read_uint8() != 0

    def read_fixed_string(self, length: int, encoding: str = "latin-1") -> str:
        """Read a fixed-length string, stripping null terminators."""
        raw = self.read_bytes(length)
        return raw.split(b"\x00", 1)[0].decode(encoding, errors="replace")

    def read_pascal_string(self, encoding: str = "latin-1") -> str:
        """Read a Pascal-style string: 1-byte length prefix + data."""
        length = self.read_uint8()
        if length == 0:
            return ""
        return self.read_bytes(length).decode(encoding, errors="replace")

    def read_pascal_string16(self, encoding: str = "latin-1") -> str:
        """Read a string with 2-byte (uint16) length prefix + data."""
        length = self.read_uint16()
        if length == 0:
            return ""
        return self.read_bytes(length).decode(encoding, errors="replace")

    def read_pascal_string32(self, encoding: str = "latin-1") -> str:
        """Read a string with 4-byte (uint32) length prefix + data."""
        length = self.read_uint32()
        if length == 0:
            return ""
        return self.read_bytes(length).decode(encoding, errors="replace")

    def read_widestring(self, char_count: int) -> str:
        """Read a UTF-16LE encoded string of given character count."""
        byte_count = char_count * 2
        raw = self.read_bytes(byte_count)
        return raw.decode("utf-16-le", errors="replace")

    def read_widestring_pascal32(self) -> str:
        """Read a wide string: 4-byte character count prefix + UTF-16LE data."""
        char_count = self.read_uint32()
        if char_count == 0:
            return ""
        return self.read_widestring(char_count)

    def _check_available(self, n: int) -> None:
        if self._offset + n > self._length:
            raise CorruptedDataError(
                f"Attempted to read {n} bytes at offset {self._offset}, "
                f"but only {self._length - self._offset} bytes remain",
                offset=self._offset,
            )
