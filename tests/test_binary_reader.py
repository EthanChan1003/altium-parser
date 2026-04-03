"""Tests for the BinaryReader."""

import struct
import pytest

from altium_parser.core.binary_reader import BinaryReader
from altium_parser.core.exceptions import CorruptedDataError


class TestBinaryReader:
    def test_read_uint8(self):
        reader = BinaryReader(b"\x42\xFF")
        assert reader.read_uint8() == 0x42
        assert reader.read_uint8() == 0xFF

    def test_read_int8(self):
        reader = BinaryReader(b"\x80\x7F")
        assert reader.read_int8() == -128
        assert reader.read_int8() == 127

    def test_read_uint16(self):
        data = struct.pack("<H", 1234)
        reader = BinaryReader(data)
        assert reader.read_uint16() == 1234

    def test_read_int16(self):
        data = struct.pack("<h", -1234)
        reader = BinaryReader(data)
        assert reader.read_int16() == -1234

    def test_read_uint32(self):
        data = struct.pack("<I", 123456789)
        reader = BinaryReader(data)
        assert reader.read_uint32() == 123456789

    def test_read_int32(self):
        data = struct.pack("<i", -123456789)
        reader = BinaryReader(data)
        assert reader.read_int32() == -123456789

    def test_read_float32(self):
        data = struct.pack("<f", 3.14)
        reader = BinaryReader(data)
        assert abs(reader.read_float32() - 3.14) < 0.001

    def test_read_float64(self):
        data = struct.pack("<d", 3.141592653589793)
        reader = BinaryReader(data)
        assert abs(reader.read_float64() - 3.141592653589793) < 1e-10

    def test_read_bool(self):
        reader = BinaryReader(b"\x01\x00")
        assert reader.read_bool() is True
        assert reader.read_bool() is False

    def test_read_fixed_string(self):
        reader = BinaryReader(b"Hello\x00\x00\x00")
        result = reader.read_fixed_string(8)
        assert result == "Hello"

    def test_read_pascal_string(self):
        data = b"\x05Hello"
        reader = BinaryReader(data)
        assert reader.read_pascal_string() == "Hello"

    def test_read_pascal_string_empty(self):
        reader = BinaryReader(b"\x00")
        assert reader.read_pascal_string() == ""

    def test_read_pascal_string16(self):
        text = b"Test"
        data = struct.pack("<H", len(text)) + text
        reader = BinaryReader(data)
        assert reader.read_pascal_string16() == "Test"

    def test_read_pascal_string32(self):
        text = b"TestString"
        data = struct.pack("<I", len(text)) + text
        reader = BinaryReader(data)
        assert reader.read_pascal_string32() == "TestString"

    def test_read_widestring(self):
        text = "AB"
        data = text.encode("utf-16-le")
        reader = BinaryReader(data)
        assert reader.read_widestring(2) == "AB"

    def test_read_widestring_pascal32(self):
        text = "Hello"
        encoded = text.encode("utf-16-le")
        data = struct.pack("<I", len(text)) + encoded
        reader = BinaryReader(data)
        assert reader.read_widestring_pascal32() == "Hello"

    def test_skip(self):
        reader = BinaryReader(b"\x01\x02\x03\x04\x05")
        reader.skip(3)
        assert reader.read_uint8() == 0x04

    def test_peek(self):
        reader = BinaryReader(b"\x01\x02\x03")
        peeked = reader.peek(2)
        assert peeked == b"\x01\x02"
        assert reader.tell() == 0  # Offset unchanged

    def test_read_bytes(self):
        reader = BinaryReader(b"\x01\x02\x03\x04")
        assert reader.read_bytes(3) == b"\x01\x02\x03"
        assert reader.tell() == 3

    def test_remaining(self):
        reader = BinaryReader(b"\x01\x02\x03")
        assert reader.remaining() == 3
        reader.skip(2)
        assert reader.remaining() == 1

    def test_is_eof(self):
        reader = BinaryReader(b"\x01")
        assert not reader.is_eof()
        reader.skip(1)
        assert reader.is_eof()

    def test_seek(self):
        reader = BinaryReader(b"\x01\x02\x03\x04")
        reader.seek(2)
        assert reader.read_uint8() == 0x03

    def test_read_beyond_eof_raises(self):
        reader = BinaryReader(b"\x01")
        with pytest.raises(CorruptedDataError):
            reader.read_uint16()

    def test_skip_beyond_eof_raises(self):
        reader = BinaryReader(b"\x01")
        with pytest.raises(CorruptedDataError):
            reader.skip(5)

    def test_seek_out_of_range_raises(self):
        reader = BinaryReader(b"\x01\x02")
        with pytest.raises(CorruptedDataError):
            reader.seek(10)

    def test_read_remaining(self):
        reader = BinaryReader(b"\x01\x02\x03")
        reader.skip(1)
        assert reader.read_remaining() == b"\x02\x03"
        assert reader.is_eof()
