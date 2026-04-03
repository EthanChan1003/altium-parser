"""Data models for Altium SchLib (schematic library) files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schematic import SchPin, SchPolyline, SchPolygon, SchRectangle, SchLine, SchArc
from .schematic import SchEllipse, SchRoundRectangle, SchBezier, SchText, SchParameter


@dataclass
class SchSymbol:
    """A schematic symbol definition in a library."""
    name: str = ""
    description: str = ""
    designator_prefix: str = ""
    part_count: int = 1
    pins: list[SchPin] = field(default_factory=list)
    parameters: list[SchParameter] = field(default_factory=list)
    polylines: list[SchPolyline] = field(default_factory=list)
    polygons: list[SchPolygon] = field(default_factory=list)
    rectangles: list[SchRectangle] = field(default_factory=list)
    lines: list[SchLine] = field(default_factory=list)
    arcs: list[SchArc] = field(default_factory=list)
    ellipses: list[SchEllipse] = field(default_factory=list)
    round_rectangles: list[SchRoundRectangle] = field(default_factory=list)
    beziers: list[SchBezier] = field(default_factory=list)
    texts: list[SchText] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "designator_prefix": self.designator_prefix,
            "part_count": self.part_count,
            "pins": [p.to_dict() for p in self.pins],
            "parameters": [p.to_dict() for p in self.parameters],
            "polylines": [p.to_dict() for p in self.polylines],
            "polygons": [p.to_dict() for p in self.polygons],
            "rectangles": [r.to_dict() for r in self.rectangles],
            "lines": [l.to_dict() for l in self.lines],
            "arcs": [a.to_dict() for a in self.arcs],
            "ellipses": [e.to_dict() for e in self.ellipses],
            "round_rectangles": [r.to_dict() for r in self.round_rectangles],
            "beziers": [b.to_dict() for b in self.beziers],
            "texts": [t.to_dict() for t in self.texts],
            "statistics": {
                "pin_count": len(self.pins),
                "primitive_count": (
                    len(self.polylines) + len(self.polygons) + len(self.rectangles)
                    + len(self.lines) + len(self.arcs) + len(self.ellipses)
                    + len(self.round_rectangles) + len(self.beziers) + len(self.texts)
                ),
            },
        }


@dataclass
class SchLibrary:
    """Parsed schematic library (.SchLib) file."""
    filename: str = ""
    symbols: list[SchSymbol] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbols": [s.to_dict() for s in self.symbols],
            "statistics": {
                "symbol_count": len(self.symbols),
            },
        }
