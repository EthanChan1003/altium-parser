"""Tests for PcbLib parser (model tests)."""

from altium_parser.models.pcblib import PcbFootprintLibrary, PcbFootprint
from altium_parser.models.pcb import PcbPad, PcbTrack
from altium_parser.models.common import Point2D


class TestPcbLibModels:
    def test_footprint_to_dict(self):
        fp = PcbFootprint(
            name="LQFP-64",
            description="64-pin LQFP package",
            height_mm=1.6,
        )
        fp.pads = [
            PcbPad(designator="1", position=Point2D(x_mm=0, y_mm=0)),
            PcbPad(designator="2", position=Point2D(x_mm=0.5, y_mm=0)),
        ]
        fp.tracks = [
            PcbTrack(start=Point2D(0, 0), end=Point2D(10, 0), width_mm=0.15),
        ]

        d = fp.to_dict()
        assert d["name"] == "LQFP-64"
        assert d["height_mm"] == 1.6
        assert len(d["pads"]) == 2
        assert d["statistics"]["pad_count"] == 2
        assert d["statistics"]["track_count"] == 1

    def test_library_to_dict(self):
        lib = PcbFootprintLibrary(filename="test.PcbLib")
        lib.footprints = [
            PcbFootprint(name="0402"),
            PcbFootprint(name="0603"),
            PcbFootprint(name="SOT-223"),
        ]
        d = lib.to_dict()
        assert d["statistics"]["footprint_count"] == 3
        assert len(d["footprints"]) == 3
