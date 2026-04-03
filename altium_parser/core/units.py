"""Unit conversion utilities for Altium internal coordinate systems."""


def sch_to_mm(value: int | float) -> float:
    """Convert schematic coordinate unit to millimeters.

    SchDoc uses 1 unit = 10 mil = 0.254 mm.
    """
    return round(value * 0.254, 6)


def sch_to_mil(value: int | float) -> float:
    """Convert schematic coordinate unit to mils."""
    return round(value * 10.0, 4)


def pcb_to_mm(value: int | float) -> float:
    """Convert PcbDoc coordinate unit to millimeters.

    PcbDoc uses 1 unit = 0.0001 mil = 0.00000254 mm.
    Equivalent to: value / 10000 / 39.370078740158
    """
    return round(value * 0.00000254, 6)


def pcb_to_mil(value: int | float) -> float:
    """Convert PcbDoc coordinate unit to mils."""
    return round(value * 0.0001, 4)


def mil_to_mm(value: float) -> float:
    """Convert mils to millimeters."""
    return round(value * 0.0254, 6)


def mm_to_mil(value: float) -> float:
    """Convert millimeters to mils."""
    return round(value / 0.0254, 4)


def delphi_color_to_rgb(color_int: int) -> tuple[int, int, int]:
    """Convert Delphi TColor (0x00BBGGRR) to (R, G, B) tuple."""
    r = color_int & 0xFF
    g = (color_int >> 8) & 0xFF
    b = (color_int >> 16) & 0xFF
    return (r, g, b)
