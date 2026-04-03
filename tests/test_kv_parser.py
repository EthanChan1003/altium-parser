"""Tests for the KV parser."""

from altium_parser.core.kv_parser import parse_kv_record, parse_pcb_kv_record


class TestParseKvRecord:
    def test_basic_record(self):
        data = b"|RECORD=1|NAME=TestComponent|VALUE=100K|"
        result = parse_kv_record(data)
        assert result["RECORD"] == "1"
        assert result["NAME"] == "TestComponent"
        assert result["VALUE"] == "100K"

    def test_empty_input(self):
        result = parse_kv_record(b"")
        assert result == {}

    def test_null_terminated(self):
        data = b"|RECORD=5|TEXT=Hello\x00\x00"
        result = parse_kv_record(data)
        assert result["RECORD"] == "5"
        assert result["TEXT"] == "Hello"

    def test_value_with_equals(self):
        data = b"|RECORD=41|NAME=Value|TEXT=R=10K|"
        result = parse_kv_record(data)
        assert result["TEXT"] == "R=10K"

    def test_empty_value(self):
        data = b"|RECORD=1|NAME=|VALUE=test|"
        result = parse_kv_record(data)
        assert result["NAME"] == ""
        assert result["VALUE"] == "test"

    def test_keys_uppercased(self):
        data = b"|Record=1|location.x=100|Location.Y=200|"
        result = parse_kv_record(data)
        assert "RECORD" in result
        assert "LOCATION.X" in result
        assert "LOCATION.Y" in result

    def test_no_leading_pipe(self):
        data = b"RECORD=1|NAME=Test|"
        result = parse_kv_record(data)
        assert result["RECORD"] == "1"
        assert result["NAME"] == "Test"

    def test_coordinate_record(self, sample_wire_kv):
        result = parse_kv_record(sample_wire_kv)
        assert result["RECORD"] == "27"
        assert result["LOCATIONCOUNT"] == "3"
        assert result["X1"] == "100"
        assert result["Y1"] == "200"
        assert result["X3"] == "300"
        assert result["Y3"] == "400"

    def test_boolean_values(self):
        data = b"|RECORD=1|ISMIRRORED=T|ISHIDDEN=F|ISSOLID=T|"
        result = parse_kv_record(data)
        assert result["ISMIRRORED"] == "T"
        assert result["ISHIDDEN"] == "F"
        assert result["ISSOLID"] == "T"


class TestParsePcbKvRecord:
    def test_basic_pcb_record(self):
        data = b"|NAME=GND|NET=1|"
        result = parse_pcb_kv_record(data)
        assert result["NAME"] == "GND"
        assert result["NET"] == "1"

    def test_prefix_before_pipe(self):
        data = b"SomePrefix|NAME=VCC|NET=2|"
        result = parse_pcb_kv_record(data)
        assert result["NAME"] == "VCC"
        assert result["NET"] == "2"
