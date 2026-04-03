"""Tests for SchDoc parser (using synthetic data)."""

import struct
from altium_parser.core.kv_parser import parse_kv_record
from altium_parser.models.schematic import SchDocument, SchComponent, SchWire, SchNetLabel
from altium_parser.models.common import Point2D


class TestSchDocModels:
    """Test SchDoc models and their serialization."""

    def test_component_to_dict(self):
        comp = SchComponent(
            refdes="U1",
            lib_reference="STM32F103",
            position=Point2D(x_mm=25.4, y_mm=50.8),
            rotation=90,
            part_count=1,
            description="ARM MCU",
        )
        d = comp.to_dict()
        assert d["refdes"] == "U1"
        assert d["lib_reference"] == "STM32F103"
        assert d["position"]["x_mm"] == 25.4
        assert d["rotation"] == 90

    def test_wire_to_dict(self):
        wire = SchWire(points=[
            Point2D(x_mm=10.0, y_mm=20.0),
            Point2D(x_mm=30.0, y_mm=20.0),
        ])
        d = wire.to_dict()
        assert len(d["points"]) == 2
        assert d["points"][0]["x_mm"] == 10.0

    def test_net_label_to_dict(self):
        label = SchNetLabel(
            name="VCC",
            position=Point2D(x_mm=50.8, y_mm=25.4),
            orientation=0,
        )
        d = label.to_dict()
        assert d["name"] == "VCC"
        assert d["position"]["x_mm"] == 50.8

    def test_document_to_dict(self):
        doc = SchDocument(filename="test.SchDoc")
        doc.components.append(SchComponent(refdes="U1"))
        doc.wires.append(SchWire(points=[Point2D(0, 0), Point2D(10, 10)]))

        d = doc.to_dict()
        assert "components" in d
        assert "wires" in d
        assert "statistics" in d
        assert d["statistics"]["component_count"] == 1
        assert d["statistics"]["wire_count"] == 1

    def test_document_statistics(self):
        doc = SchDocument(filename="test.SchDoc")
        for i in range(5):
            doc.components.append(SchComponent(refdes=f"U{i+1}"))
        for i in range(10):
            doc.net_labels.append(SchNetLabel(name=f"NET{i}"))

        d = doc.to_dict()
        assert d["statistics"]["component_count"] == 5
        assert d["statistics"]["net_label_count"] == 10


class TestSchDocRecordParsing:
    """Test parsing of individual record types from KV data."""

    def test_parse_component_record(self, sample_kv_bytes):
        kv = parse_kv_record(sample_kv_bytes)
        assert kv["RECORD"] == "1"
        assert kv["LIBREFERENCE"] == "RES_0402"
        assert kv["COMPONENTDESCRIPTION"] == "Resistor 10K"
        assert kv["LOCATION.X"] == "500"
        assert kv["LOCATION.Y"] == "300"

    def test_parse_wire_record(self, sample_wire_kv):
        kv = parse_kv_record(sample_wire_kv)
        assert kv["RECORD"] == "27"
        count = int(kv["LOCATIONCOUNT"])
        assert count == 3
        points = []
        for i in range(1, count + 1):
            x = int(kv[f"X{i}"])
            y = int(kv[f"Y{i}"])
            points.append((x, y))
        assert points == [(100, 200), (300, 200), (300, 400)]

    def test_parse_parameter_with_equals(self, sample_kv_with_special):
        kv = parse_kv_record(sample_kv_with_special)
        assert kv["TEXT"] == "10K=5%"
        assert kv["OWNERINDEX"] == "3"
        assert kv["ISHIDDEN"] == "T"
