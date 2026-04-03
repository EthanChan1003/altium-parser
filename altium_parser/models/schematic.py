"""Data models for Altium SchDoc (schematic document) files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .common import Point2D, Color, model_to_dict


@dataclass
class SchPin:
    """Schematic component pin."""
    name: str = ""
    number: str = ""
    electrical_type: str = "passive"
    position: Point2D = field(default_factory=Point2D)
    orientation: int = 0
    length_mm: float = 0.0
    is_hidden: bool = False
    owner_index: int = -1
    owner_part_id: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "number": self.number,
            "electrical_type": self.electrical_type,
            "position": self.position.to_dict(),
            "orientation": self.orientation,
            "length_mm": self.length_mm,
            "is_hidden": self.is_hidden,
        }


@dataclass
class SchPolyline:
    """Schematic polyline primitive."""
    points: list[Point2D] = field(default_factory=list)
    color: Color = field(default_factory=Color)
    line_width: int = 1
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
            "color": self.color.to_hex(),
            "line_width": self.line_width,
        }


@dataclass
class SchPolygon:
    """Schematic polygon primitive."""
    points: list[Point2D] = field(default_factory=list)
    fill_color: Color = field(default_factory=Color)
    border_color: Color = field(default_factory=Color)
    line_width: int = 1
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
            "fill_color": self.fill_color.to_hex(),
            "border_color": self.border_color.to_hex(),
            "line_width": self.line_width,
        }


@dataclass
class SchRectangle:
    """Schematic rectangle primitive."""
    corner1: Point2D = field(default_factory=Point2D)
    corner2: Point2D = field(default_factory=Point2D)
    fill_color: Color = field(default_factory=Color)
    border_color: Color = field(default_factory=Color)
    line_width: int = 1
    is_solid: bool = False
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "corner1": self.corner1.to_dict(),
            "corner2": self.corner2.to_dict(),
            "fill_color": self.fill_color.to_hex(),
            "border_color": self.border_color.to_hex(),
            "line_width": self.line_width,
            "is_solid": self.is_solid,
        }


@dataclass
class SchLine:
    """Schematic line primitive."""
    start: Point2D = field(default_factory=Point2D)
    end: Point2D = field(default_factory=Point2D)
    color: Color = field(default_factory=Color)
    line_width: int = 1
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "color": self.color.to_hex(),
            "line_width": self.line_width,
        }


@dataclass
class SchArc:
    """Schematic arc primitive."""
    center: Point2D = field(default_factory=Point2D)
    radius_mm: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 360.0
    line_width: int = 1
    color: Color = field(default_factory=Color)
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "center": self.center.to_dict(),
            "radius_mm": self.radius_mm,
            "start_angle": self.start_angle,
            "end_angle": self.end_angle,
            "line_width": self.line_width,
            "color": self.color.to_hex(),
        }


@dataclass
class SchEllipse:
    """Schematic ellipse primitive."""
    center: Point2D = field(default_factory=Point2D)
    radius_x_mm: float = 0.0
    radius_y_mm: float = 0.0
    fill_color: Color = field(default_factory=Color)
    border_color: Color = field(default_factory=Color)
    line_width: int = 1
    is_solid: bool = False
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "center": self.center.to_dict(),
            "radius_x_mm": self.radius_x_mm,
            "radius_y_mm": self.radius_y_mm,
            "fill_color": self.fill_color.to_hex(),
            "border_color": self.border_color.to_hex(),
            "is_solid": self.is_solid,
        }


@dataclass
class SchRoundRectangle:
    """Schematic rounded rectangle."""
    corner1: Point2D = field(default_factory=Point2D)
    corner2: Point2D = field(default_factory=Point2D)
    corner_radius_mm: float = 0.0
    fill_color: Color = field(default_factory=Color)
    border_color: Color = field(default_factory=Color)
    line_width: int = 1
    is_solid: bool = False
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "corner1": self.corner1.to_dict(),
            "corner2": self.corner2.to_dict(),
            "corner_radius_mm": self.corner_radius_mm,
            "fill_color": self.fill_color.to_hex(),
            "border_color": self.border_color.to_hex(),
            "is_solid": self.is_solid,
        }


@dataclass
class SchBezier:
    """Schematic bezier curve."""
    points: list[Point2D] = field(default_factory=list)
    color: Color = field(default_factory=Color)
    line_width: int = 1
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
            "color": self.color.to_hex(),
            "line_width": self.line_width,
        }


@dataclass
class SchText:
    """Schematic text object."""
    content: str = ""
    position: Point2D = field(default_factory=Point2D)
    font_size: int = 10
    rotation: int = 0
    color: Color = field(default_factory=Color)
    is_hidden: bool = False
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "position": self.position.to_dict(),
            "font_size": self.font_size,
            "rotation": self.rotation,
            "color": self.color.to_hex(),
            "is_hidden": self.is_hidden,
        }


@dataclass
class SchLabel:
    """Schematic text label."""
    text: str = ""
    position: Point2D = field(default_factory=Point2D)
    orientation: int = 0
    color: Color = field(default_factory=Color)
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "position": self.position.to_dict(),
            "orientation": self.orientation,
            "color": self.color.to_hex(),
        }


@dataclass
class SchImage:
    """Schematic embedded image."""
    filename: str = ""
    position: Point2D = field(default_factory=Point2D)
    corner: Point2D = field(default_factory=Point2D)
    is_embedded: bool = False
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "position": self.position.to_dict(),
            "corner": self.corner.to_dict(),
            "is_embedded": self.is_embedded,
        }


@dataclass
class SchWire:
    """Schematic wire (electrical connection)."""
    points: list[Point2D] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
        }


@dataclass
class SchBus:
    """Schematic bus."""
    points: list[Point2D] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
        }


@dataclass
class SchBusEntry:
    """Schematic bus entry."""
    position: Point2D = field(default_factory=Point2D)
    corner: Point2D = field(default_factory=Point2D)

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position.to_dict(),
            "corner": self.corner.to_dict(),
        }


@dataclass
class SchNetLabel:
    """Schematic net label."""
    name: str = ""
    position: Point2D = field(default_factory=Point2D)
    orientation: int = 0
    color: Color = field(default_factory=Color)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "position": self.position.to_dict(),
            "orientation": self.orientation,
            "color": self.color.to_hex(),
        }


@dataclass
class SchPowerPort:
    """Schematic power port symbol."""
    name: str = ""
    style: str = "arrow"
    position: Point2D = field(default_factory=Point2D)
    orientation: int = 0
    is_cross_sheet: bool = False
    color: Color = field(default_factory=Color)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "style": self.style,
            "position": self.position.to_dict(),
            "orientation": self.orientation,
            "is_cross_sheet": self.is_cross_sheet,
        }


@dataclass
class SchPort:
    """Schematic port."""
    name: str = ""
    position: Point2D = field(default_factory=Point2D)
    width_mm: float = 0.0
    height_mm: float = 0.0
    io_type: str = "unspecified"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "position": self.position.to_dict(),
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "io_type": self.io_type,
        }


@dataclass
class SchJunction:
    """Schematic wire junction."""
    position: Point2D = field(default_factory=Point2D)
    color: Color = field(default_factory=Color)

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position.to_dict(),
        }


@dataclass
class SchNoErc:
    """Schematic No-ERC marker."""
    position: Point2D = field(default_factory=Point2D)

    def to_dict(self) -> dict[str, Any]:
        return {"position": self.position.to_dict()}


@dataclass
class SchSheetSymbol:
    """Hierarchical sheet symbol."""
    position: Point2D = field(default_factory=Point2D)
    width_mm: float = 0.0
    height_mm: float = 0.0
    sheet_name: str = ""
    file_name: str = ""
    entries: list[SchSheetEntry] = field(default_factory=list)
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position.to_dict(),
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "sheet_name": self.sheet_name,
            "file_name": self.file_name,
            "entries": [e.to_dict() for e in self.entries],
        }


@dataclass
class SchSheetEntry:
    """Port entry on a sheet symbol."""
    name: str = ""
    io_type: str = "unspecified"
    side: int = 0
    position_offset_mm: float = 0.0
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "io_type": self.io_type,
            "side": self.side,
            "position_offset_mm": self.position_offset_mm,
        }


@dataclass
class SchParameter:
    """A parameter/attribute on a component."""
    name: str = ""
    value: str = ""
    position: Point2D = field(default_factory=Point2D)
    is_hidden: bool = False
    owner_index: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "position": self.position.to_dict(),
            "is_hidden": self.is_hidden,
        }


@dataclass
class SchComponent:
    """Schematic component instance."""
    owner_index: int = 0
    refdes: str = ""
    lib_reference: str = ""
    position: Point2D = field(default_factory=Point2D)
    rotation: int = 0
    is_mirrored: bool = False
    part_count: int = 1
    current_part_id: int = 1
    description: str = ""
    source_library: str = ""
    unique_id: str = ""
    pins: list[SchPin] = field(default_factory=list)
    parameters: list[SchParameter] = field(default_factory=list)
    graphic_primitives: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "refdes": self.refdes,
            "lib_reference": self.lib_reference,
            "position": self.position.to_dict(),
            "rotation": self.rotation,
            "is_mirrored": self.is_mirrored,
            "part_count": self.part_count,
            "current_part_id": self.current_part_id,
            "description": self.description,
            "source_library": self.source_library,
            "unique_id": self.unique_id,
            "pins": [p.to_dict() for p in self.pins],
            "parameters": [p.to_dict() for p in self.parameters],
            "graphic_primitives": [model_to_dict(p) for p in self.graphic_primitives],
        }


@dataclass
class SchTitleBlock:
    """Sheet title block information."""
    title: str = ""
    date: str = ""
    revision: str = ""
    company: str = ""
    author: str = ""
    sheet_number: str = ""
    sheet_total: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "date": self.date,
            "revision": self.revision,
            "company": self.company,
            "author": self.author,
            "sheet_number": self.sheet_number,
            "sheet_total": self.sheet_total,
        }


@dataclass
class SchSheet:
    """Sheet properties (paper size, grid, etc.)."""
    size: str = "A4"
    width_mm: float = 297.0
    height_mm: float = 210.0
    grid_size_mm: float = 2.54
    title_block: SchTitleBlock = field(default_factory=SchTitleBlock)
    font_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "size": self.size,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "grid_size_mm": self.grid_size_mm,
            "title_block": self.title_block.to_dict(),
        }


@dataclass
class SchDocument:
    """Complete parsed schematic document."""
    filename: str = ""
    sheet: SchSheet = field(default_factory=SchSheet)
    components: list[SchComponent] = field(default_factory=list)
    wires: list[SchWire] = field(default_factory=list)
    buses: list[SchBus] = field(default_factory=list)
    bus_entries: list[SchBusEntry] = field(default_factory=list)
    net_labels: list[SchNetLabel] = field(default_factory=list)
    power_ports: list[SchPowerPort] = field(default_factory=list)
    ports: list[SchPort] = field(default_factory=list)
    junctions: list[SchJunction] = field(default_factory=list)
    no_ercs: list[SchNoErc] = field(default_factory=list)
    polylines: list[SchPolyline] = field(default_factory=list)
    polygons: list[SchPolygon] = field(default_factory=list)
    rectangles: list[SchRectangle] = field(default_factory=list)
    lines: list[SchLine] = field(default_factory=list)
    arcs: list[SchArc] = field(default_factory=list)
    ellipses: list[SchEllipse] = field(default_factory=list)
    round_rectangles: list[SchRoundRectangle] = field(default_factory=list)
    beziers: list[SchBezier] = field(default_factory=list)
    texts: list[SchText] = field(default_factory=list)
    labels: list[SchLabel] = field(default_factory=list)
    images: list[SchImage] = field(default_factory=list)
    sheet_symbols: list[SchSheetSymbol] = field(default_factory=list)
    raw_record_count: int = 0
    unknown_record_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "sheet": self.sheet.to_dict(),
            "components": [c.to_dict() for c in self.components],
            "wires": [w.to_dict() for w in self.wires],
            "buses": [b.to_dict() for b in self.buses],
            "bus_entries": [b.to_dict() for b in self.bus_entries],
            "net_labels": [n.to_dict() for n in self.net_labels],
            "power_ports": [p.to_dict() for p in self.power_ports],
            "ports": [p.to_dict() for p in self.ports],
            "junctions": [j.to_dict() for j in self.junctions],
            "no_ercs": [n.to_dict() for n in self.no_ercs],
            "polylines": [p.to_dict() for p in self.polylines],
            "polygons": [p.to_dict() for p in self.polygons],
            "rectangles": [r.to_dict() for r in self.rectangles],
            "lines": [l.to_dict() for l in self.lines],
            "arcs": [a.to_dict() for a in self.arcs],
            "ellipses": [e.to_dict() for e in self.ellipses],
            "round_rectangles": [r.to_dict() for r in self.round_rectangles],
            "beziers": [b.to_dict() for b in self.beziers],
            "texts": [t.to_dict() for t in self.texts],
            "labels": [l.to_dict() for l in self.labels],
            "images": [i.to_dict() for i in self.images],
            "sheet_symbols": [s.to_dict() for s in self.sheet_symbols],
            "statistics": {
                "total_records": self.raw_record_count,
                "unknown_records": self.unknown_record_count,
                "component_count": len(self.components),
                "wire_count": len(self.wires),
                "net_label_count": len(self.net_labels),
            },
        }
