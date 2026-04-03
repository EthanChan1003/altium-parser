"""Tests for unit conversion utilities."""

from altium_parser.core.units import (
    sch_to_mm, sch_to_mil, pcb_to_mm, pcb_to_mil,
    mil_to_mm, mm_to_mil, delphi_color_to_rgb,
)


class TestSchUnits:
    def test_sch_to_mm_basic(self):
        # 1 unit = 10 mil = 0.254 mm
        assert sch_to_mm(1) == 0.254
        assert sch_to_mm(100) == 25.4
        assert sch_to_mm(0) == 0.0

    def test_sch_to_mm_typical_value(self):
        # A4 sheet width = 1170 units = 297.18 mm
        result = sch_to_mm(1170)
        assert abs(result - 297.18) < 0.01

    def test_sch_to_mm_negative(self):
        assert sch_to_mm(-100) == -25.4

    def test_sch_to_mil(self):
        assert sch_to_mil(1) == 10.0
        assert sch_to_mil(100) == 1000.0


class TestPcbUnits:
    def test_pcb_to_mm_basic(self):
        # 1 unit = 0.0001 mil = 0.00000254 mm
        result = pcb_to_mm(10000000)  # = 1 inch = 25.4 mm
        assert abs(result - 25.4) < 0.001

    def test_pcb_to_mm_common_track_width(self):
        # 10 mil track = 100000 units
        result = pcb_to_mm(100000)
        assert abs(result - 0.254) < 0.001

    def test_pcb_to_mm_zero(self):
        assert pcb_to_mm(0) == 0.0

    def test_pcb_to_mm_negative(self):
        result = pcb_to_mm(-10000000)
        assert abs(result - (-25.4)) < 0.001

    def test_pcb_to_mil(self):
        assert pcb_to_mil(10000) == 1.0
        assert pcb_to_mil(100000) == 10.0


class TestGeneralUnits:
    def test_mil_to_mm(self):
        assert mil_to_mm(1000) == 25.4
        assert mil_to_mm(10) == 0.254

    def test_mm_to_mil(self):
        assert mm_to_mil(25.4) == 1000.0
        assert mm_to_mil(0.254) == 10.0

    def test_roundtrip_mil_mm(self):
        original = 123.456
        result = mm_to_mil(mil_to_mm(original))
        assert abs(result - original) < 0.01


class TestDelphiColor:
    def test_pure_red(self):
        assert delphi_color_to_rgb(0x0000FF) == (255, 0, 0)

    def test_pure_green(self):
        assert delphi_color_to_rgb(0x00FF00) == (0, 255, 0)

    def test_pure_blue(self):
        assert delphi_color_to_rgb(0xFF0000) == (0, 0, 255)

    def test_white(self):
        assert delphi_color_to_rgb(0xFFFFFF) == (255, 255, 255)

    def test_black(self):
        assert delphi_color_to_rgb(0x000000) == (0, 0, 0)

    def test_mixed_color(self):
        # BGR: B=0x12, G=0x34, R=0x56
        assert delphi_color_to_rgb(0x123456) == (0x56, 0x34, 0x12)
