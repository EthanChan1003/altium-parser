"""Enums and constants for Altium Designer file formats."""

from enum import IntEnum


class SchRecordType(IntEnum):
    """Schematic record types identified by |RECORD=N in SchDoc/SchLib."""
    HEADER = 0
    COMPONENT = 1
    PIN = 2
    IEEE_SYMBOL = 3
    LABEL = 4
    BEZIER = 5
    POLYLINE = 6
    POLYGON = 7
    ELLIPSE = 8
    PIE = 9
    ROUND_RECTANGLE = 10
    ELLIPTICAL_ARC = 11
    ARC = 12
    LINE = 13
    RECTANGLE = 14
    SHEET_SYMBOL = 15
    SHEET_ENTRY = 16
    POWER_PORT = 17
    PORT = 18
    NO_ERC = 22
    NET_LABEL = 25
    BUS = 26
    WIRE = 27
    TEXT_FRAME = 28
    JUNCTION = 29
    IMAGE = 30
    SHEET = 31
    SHEET_NAME = 32
    SHEET_FILE_NAME = 33
    DESIGNATOR = 34
    BUS_ENTRY = 37
    TEMPLATE = 39
    PARAMETER = 41
    WARNING_SIGN = 43
    IMPLEMENTATION_LIST = 44
    IMPLEMENTATION = 45
    RECORD_46 = 46
    RECORD_47 = 47
    RECORD_48 = 48


class PinElectricalType(IntEnum):
    """Pin electrical types for schematic pins."""
    INPUT = 0
    IO = 1
    OUTPUT = 2
    OPEN_COLLECTOR = 3
    PASSIVE = 4
    HI_Z = 5
    OPEN_EMITTER = 6
    POWER = 7


PIN_ELECTRICAL_NAMES = {
    PinElectricalType.INPUT: "input",
    PinElectricalType.IO: "bidirectional",
    PinElectricalType.OUTPUT: "output",
    PinElectricalType.OPEN_COLLECTOR: "open_collector",
    PinElectricalType.PASSIVE: "passive",
    PinElectricalType.HI_Z: "hi_z",
    PinElectricalType.OPEN_EMITTER: "open_emitter",
    PinElectricalType.POWER: "power",
}


class PinOrientation(IntEnum):
    """Pin orientation encoded in PINCONGLOMERATE field."""
    RIGHT = 0
    UP = 1
    LEFT = 2
    DOWN = 3


class PowerPortStyle(IntEnum):
    """Power port symbol styles."""
    ARROW = 0
    BAR = 1
    GROUND = 2
    SIGNAL_GROUND = 3
    EARTH = 4
    GROUND_POWER = 5
    SIGNAL_POWER = 6
    CIRCLE = 7


POWER_PORT_STYLE_NAMES = {
    PowerPortStyle.ARROW: "arrow",
    PowerPortStyle.BAR: "bar",
    PowerPortStyle.GROUND: "power_ground",
    PowerPortStyle.SIGNAL_GROUND: "signal_ground",
    PowerPortStyle.EARTH: "earth",
    PowerPortStyle.GROUND_POWER: "ground_power",
    PowerPortStyle.SIGNAL_POWER: "signal_power",
    PowerPortStyle.CIRCLE: "circle",
}


class SheetStyle(IntEnum):
    """Sheet paper sizes."""
    A4 = 0
    A3 = 1
    A2 = 2
    A1 = 3
    A0 = 4
    A = 5
    B = 6
    C = 7
    D = 8
    E = 9
    LETTER = 10
    LEGAL = 11
    TABLOID = 12
    ORCAD_A = 13
    ORCAD_B = 14
    ORCAD_C = 15
    ORCAD_D = 16
    ORCAD_E = 17


SHEET_SIZE_MM = {
    SheetStyle.A4: (297, 210),
    SheetStyle.A3: (420, 297),
    SheetStyle.A2: (594, 420),
    SheetStyle.A1: (841, 594),
    SheetStyle.A0: (1189, 841),
    SheetStyle.A: (279.4, 215.9),
    SheetStyle.B: (431.8, 279.4),
    SheetStyle.C: (558.8, 431.8),
    SheetStyle.D: (863.6, 558.8),
    SheetStyle.E: (1117.6, 863.6),
    SheetStyle.LETTER: (279.4, 215.9),
    SheetStyle.LEGAL: (355.6, 215.9),
    SheetStyle.TABLOID: (431.8, 279.4),
}

SHEET_STYLE_NAMES = {
    SheetStyle.A4: "A4",
    SheetStyle.A3: "A3",
    SheetStyle.A2: "A2",
    SheetStyle.A1: "A1",
    SheetStyle.A0: "A0",
    SheetStyle.A: "A",
    SheetStyle.B: "B",
    SheetStyle.C: "C",
    SheetStyle.D: "D",
    SheetStyle.E: "E",
    SheetStyle.LETTER: "Letter",
    SheetStyle.LEGAL: "Legal",
    SheetStyle.TABLOID: "Tabloid",
}


class AltiumLayer(IntEnum):
    """PCB layer IDs used in PcbDoc."""
    TOP_LAYER = 1
    MID_LAYER_1 = 2
    MID_LAYER_2 = 3
    MID_LAYER_3 = 4
    MID_LAYER_4 = 5
    MID_LAYER_5 = 6
    MID_LAYER_6 = 7
    MID_LAYER_7 = 8
    MID_LAYER_8 = 9
    MID_LAYER_9 = 10
    MID_LAYER_10 = 11
    MID_LAYER_11 = 12
    MID_LAYER_12 = 13
    MID_LAYER_13 = 14
    MID_LAYER_14 = 15
    MID_LAYER_15 = 16
    MID_LAYER_16 = 17
    MID_LAYER_17 = 18
    MID_LAYER_18 = 19
    MID_LAYER_19 = 20
    MID_LAYER_20 = 21
    MID_LAYER_21 = 22
    MID_LAYER_22 = 23
    MID_LAYER_23 = 24
    MID_LAYER_24 = 25
    MID_LAYER_25 = 26
    MID_LAYER_26 = 27
    MID_LAYER_27 = 28
    MID_LAYER_28 = 29
    MID_LAYER_29 = 30
    MID_LAYER_30 = 31
    BOTTOM_LAYER = 32
    TOP_OVERLAY = 33
    BOTTOM_OVERLAY = 34
    TOP_PASTE = 35
    BOTTOM_PASTE = 36
    TOP_SOLDER = 37
    BOTTOM_SOLDER = 38
    INTERNAL_PLANE_1 = 39
    INTERNAL_PLANE_2 = 40
    INTERNAL_PLANE_3 = 41
    INTERNAL_PLANE_4 = 42
    INTERNAL_PLANE_5 = 43
    INTERNAL_PLANE_6 = 44
    INTERNAL_PLANE_7 = 45
    INTERNAL_PLANE_8 = 46
    INTERNAL_PLANE_9 = 47
    INTERNAL_PLANE_10 = 48
    INTERNAL_PLANE_11 = 49
    INTERNAL_PLANE_12 = 50
    INTERNAL_PLANE_13 = 51
    INTERNAL_PLANE_14 = 52
    INTERNAL_PLANE_15 = 53
    INTERNAL_PLANE_16 = 54
    DRILL_GUIDE = 55
    KEEP_OUT_LAYER = 56
    MECHANICAL_1 = 57
    MECHANICAL_2 = 58
    MECHANICAL_3 = 59
    MECHANICAL_4 = 60
    MECHANICAL_5 = 61
    MECHANICAL_6 = 62
    MECHANICAL_7 = 63
    MECHANICAL_8 = 64
    MECHANICAL_9 = 65
    MECHANICAL_10 = 66
    MECHANICAL_11 = 67
    MECHANICAL_12 = 68
    MECHANICAL_13 = 69
    MECHANICAL_14 = 70
    MECHANICAL_15 = 71
    MECHANICAL_16 = 72
    DRILL_DRAWING = 73
    MULTI_LAYER = 74
    CONNECTIONS = 75
    BACKGROUND = 76
    DRC_ERROR = 77
    SELECTIONS = 78
    VISIBLE_GRID_1 = 79
    VISIBLE_GRID_2 = 80
    PAD_HOLES = 81
    VIA_HOLES = 82


def layer_id_to_name(layer_id: int) -> str:
    """Convert a layer ID to its human-readable name."""
    _LAYER_NAMES = {
        1: "Top Layer",
        32: "Bottom Layer",
        33: "Top Overlay",
        34: "Bottom Overlay",
        35: "Top Paste",
        36: "Bottom Paste",
        37: "Top Solder",
        38: "Bottom Solder",
        55: "Drill Guide",
        56: "Keep-Out Layer",
        73: "Drill Drawing",
        74: "Multi-Layer",
        75: "Connections",
        76: "Background",
        77: "DRC Error Markers",
        78: "Selections",
        79: "Visible Grid 1",
        80: "Visible Grid 2",
        81: "Pad Holes",
        82: "Via Holes",
    }
    if layer_id in _LAYER_NAMES:
        return _LAYER_NAMES[layer_id]
    if 2 <= layer_id <= 31:
        return f"Mid Layer {layer_id - 1}"
    if 39 <= layer_id <= 54:
        return f"Internal Plane {layer_id - 38}"
    if 57 <= layer_id <= 72:
        return f"Mechanical {layer_id - 56}"
    return f"Unknown Layer {layer_id}"


class PadShape(IntEnum):
    """Pad shape types in PcbDoc."""
    ROUND = 1
    RECTANGULAR = 2
    OCTAGONAL = 3
    ROUNDED_RECT = 9


PAD_SHAPE_NAMES = {
    PadShape.ROUND: "round",
    PadShape.RECTANGULAR: "rectangular",
    PadShape.OCTAGONAL: "octagonal",
    PadShape.ROUNDED_RECT: "rounded_rectangular",
}


class HoleShape(IntEnum):
    """Hole shape types."""
    ROUND = 0
    SQUARE = 1
    SLOT = 2


class TextJustification(IntEnum):
    """Text justification (1-9 grid)."""
    BOTTOM_LEFT = 1
    BOTTOM_CENTER = 2
    BOTTOM_RIGHT = 3
    MIDDLE_LEFT = 4
    MIDDLE_CENTER = 5
    MIDDLE_RIGHT = 6
    TOP_LEFT = 7
    TOP_CENTER = 8
    TOP_RIGHT = 9


class LineWidth(IntEnum):
    """Schematic line width presets."""
    SMALLEST = 0  # 1 pixel (hairline)
    SMALL = 1     # 4 mil (default when omitted)
    MEDIUM = 2    # 10 mil
    LARGE = 3     # 20 mil
    LARGEST = 4   # 40 mil


LINE_WIDTH_MIL = {
    LineWidth.SMALLEST: 1,
    LineWidth.SMALL: 4,
    LineWidth.MEDIUM: 10,
    LineWidth.LARGE: 20,
    LineWidth.LARGEST: 40,
}
