"""Tests for SchLib parser (model tests)."""

from altium_parser.models.schlib import SchLibrary, SchSymbol
from altium_parser.models.schematic import SchPin, SchRectangle, SchPolyline
from altium_parser.models.common import Point2D


class TestSchLibModels:
    def test_symbol_to_dict(self):
        symbol = SchSymbol(
            name="RES_0402",
            description="0402 Resistor",
            designator_prefix="R",
            part_count=1,
        )
        symbol.pins = [
            SchPin(name="1", number="1", position=Point2D(x_mm=-5.08, y_mm=0)),
            SchPin(name="2", number="2", position=Point2D(x_mm=5.08, y_mm=0)),
        ]
        symbol.rectangles = [
            SchRectangle(
                corner1=Point2D(x_mm=-2.54, y_mm=-1.27),
                corner2=Point2D(x_mm=2.54, y_mm=1.27),
            ),
        ]

        d = symbol.to_dict()
        assert d["name"] == "RES_0402"
        assert d["description"] == "0402 Resistor"
        assert len(d["pins"]) == 2
        assert d["pins"][0]["name"] == "1"
        assert len(d["rectangles"]) == 1
        assert d["statistics"]["pin_count"] == 2

    def test_library_to_dict(self):
        lib = SchLibrary(filename="test.SchLib")
        lib.symbols = [
            SchSymbol(name="RES"),
            SchSymbol(name="CAP"),
            SchSymbol(name="LED"),
        ]
        d = lib.to_dict()
        assert d["statistics"]["symbol_count"] == 3
        assert len(d["symbols"]) == 3
