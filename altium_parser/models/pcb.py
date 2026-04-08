"""Data models for Altium PcbDoc (PCB document) files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .common import Point2D, BoundingBox, model_to_dict, _round_coord


@dataclass
class StackupLayer:
    """A layer in the PCB stackup."""
    id: int = 0
    name: str = ""
    copper_thickness_mm: float = 0.035
    dielectric_constant: float = 4.2
    dielectric_height_mm: float = 0.2
    material: str = "FR-4"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "copper_thickness_mm": self.copper_thickness_mm,
            "dielectric_constant": self.dielectric_constant,
            "dielectric_height_mm": self.dielectric_height_mm,
            "material": self.material,
        }


@dataclass
class BoardOutline:
    """PCB board outline."""
    vertices: list[Point2D] = field(default_factory=list)
    bounding_box: BoundingBox = field(default_factory=BoundingBox)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertices": [v.to_dict() for v in self.vertices],
            "bounding_box": self.bounding_box.to_dict(),
        }


@dataclass
class PcbNet:
    """A net definition."""
    id: int = 0
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}


@dataclass
class PcbComponent:
    """A placed component on the PCB."""
    designator: str = ""
    comment: str = ""
    footprint_name: str = ""
    position: Point2D = field(default_factory=Point2D)
    rotation: float = 0.0
    layer: str = "top"
    is_locked: bool = False
    source_unique_id: str = ""
    bounding_box: BoundingBox = field(default_factory=BoundingBox)
    model_3d_name: str = ""
    # Child primitives (populated after initial parsing)
    pads: list[PcbPad] = field(default_factory=list)
    # Silkscreen primitives (Top Overlay layer elements belonging to this component)
    silkscreen_tracks: list[PcbTrack] = field(default_factory=list)
    silkscreen_arcs: list[PcbArc] = field(default_factory=list)
    # Component texts (Designator, Comment, etc.)
    texts: list[PcbText] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "designator": self.designator,
            "comment": self.comment,
            "footprint_name": self.footprint_name,
            "position": self.position.to_dict(),
            "rotation": self.rotation,
            "layer": self.layer,
            "is_locked": self.is_locked,
            "source_unique_id": self.source_unique_id,
        }
        if self.model_3d_name:
            d["model_3d_name"] = self.model_3d_name
        if self.pads:
            d["pads"] = [p.to_dict() for p in self.pads]
        if self.silkscreen_tracks:
            d["silkscreen_tracks"] = [t.to_dict() for t in self.silkscreen_tracks]
        if self.silkscreen_arcs:
            d["silkscreen_arcs"] = [a.to_dict() for a in self.silkscreen_arcs]
        if self.texts:
            d["texts"] = [t.to_dict() for t in self.texts]
        # Always output bounding box if we have any child elements
        if self.pads or self.silkscreen_tracks or self.silkscreen_arcs or self.texts:
            d["bounding_box"] = self.bounding_box.to_dict()
        return d


@dataclass
class PcbTrack:
    """A copper track segment."""
    start: Point2D = field(default_factory=Point2D)
    end: Point2D = field(default_factory=Point2D)
    width_mm: float = 0.0
    layer: str = ""
    layer_id: int = 0
    net: str = ""
    net_id: int = 0
    component_id: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "width_mm": _round_coord(self.width_mm),
            "layer": self.layer,
            "net": self.net,
        }


@dataclass
class PcbArc:
    """A copper arc segment."""
    center: Point2D = field(default_factory=Point2D)
    radius_mm: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 360.0
    width_mm: float = 0.0
    layer: str = ""
    layer_id: int = 0
    net: str = ""
    net_id: int = 0
    component_id: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "center": self.center.to_dict(),
            "radius_mm": _round_coord(self.radius_mm),
            "start_angle": _round_coord(self.start_angle, 2),
            "end_angle": _round_coord(self.end_angle, 2),
            "width_mm": _round_coord(self.width_mm),
            "layer": self.layer,
            "net": self.net,
        }


@dataclass
class PcbPad:
    """A pad on the PCB."""
    designator: str = ""
    position: Point2D = field(default_factory=Point2D)
    top_size: Point2D = field(default_factory=Point2D)
    mid_size: Point2D = field(default_factory=Point2D)
    bottom_size: Point2D = field(default_factory=Point2D)
    hole_size_mm: float = 0.0
    hole_shape: str = "round"
    shape: str = "round"
    rotation: float = 0.0
    layer: str = ""
    layer_id: int = 0
    net: str = ""
    net_id: int = 0
    component_id: int = -1
    is_plated: bool = True
    pad_type: str = "smd"
    slot_width_mm: float = 0.0
    slot_height_mm: float = 0.0
    slot_rotation: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = {
            "designator": self.designator,
            "position": self.position.to_dict(),
            "top_size": self.top_size.to_dict(),
            "hole_size_mm": _round_coord(self.hole_size_mm),
            "shape": self.shape,
            "rotation": _round_coord(self.rotation, 2),
            "layer": self.layer,
            "net": self.net,
            "pad_type": self.pad_type,
        }
        if self.hole_size_mm > 0:
            d["mid_size"] = self.mid_size.to_dict()
            d["bottom_size"] = self.bottom_size.to_dict()
            d["hole_shape"] = self.hole_shape
            d["is_plated"] = self.is_plated
            if self.hole_shape == "slot":
                d["slot_width_mm"] = _round_coord(self.slot_width_mm)
                d["slot_height_mm"] = _round_coord(self.slot_height_mm)
                d["slot_rotation"] = _round_coord(self.slot_rotation, 2)
        return d


@dataclass
class PcbVia:
    """A via (plated through-hole for layer transitions)."""
    position: Point2D = field(default_factory=Point2D)
    diameter_mm: float = 0.0
    hole_mm: float = 0.0
    start_layer: str = ""
    start_layer_id: int = 0
    end_layer: str = ""
    end_layer_id: int = 0
    net: str = ""
    net_id: int = 0
    is_tented_top: bool = False
    is_tented_bottom: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position.to_dict(),
            "diameter_mm": _round_coord(self.diameter_mm),
            "hole_mm": _round_coord(self.hole_mm),
            "start_layer": self.start_layer,
            "end_layer": self.end_layer,
            "net": self.net,
            "is_tented_top": self.is_tented_top,
            "is_tented_bottom": self.is_tented_bottom,
        }


@dataclass
class PcbFill:
    """A solid fill region."""
    corner1: Point2D = field(default_factory=Point2D)
    corner2: Point2D = field(default_factory=Point2D)
    rotation: float = 0.0
    layer: str = ""
    layer_id: int = 0
    net: str = ""
    net_id: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "corner1": self.corner1.to_dict(),
            "corner2": self.corner2.to_dict(),
            "rotation": _round_coord(self.rotation, 2),
            "layer": self.layer,
            "net": self.net,
        }


@dataclass
class PcbRegion:
    """A polygon region (copper pour, board cutout, etc.)."""
    vertices: list[PolygonVertex] = field(default_factory=list)
    layer: str = ""
    layer_id: int = 0
    net: str = ""
    net_id: int = 0
    is_keepout: bool = False
    kind: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertices": [v.to_dict() for v in self.vertices],
            "layer": self.layer,
            "net": self.net,
            "is_keepout": self.is_keepout,
        }


@dataclass
class PcbText:
    """A text string on the PCB."""
    content: str = ""
    position: Point2D = field(default_factory=Point2D)
    height_mm: float = 1.0
    width_mm: float = 0.0
    rotation: float = 0.0
    layer: str = ""
    layer_id: int = 0
    font: str = "stroke"
    is_mirrored: bool = False
    component_id: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "position": self.position.to_dict(),
            "height_mm": self.height_mm,
            "rotation": self.rotation,
            "layer": self.layer,
            "font": self.font,
            "is_mirrored": self.is_mirrored,
        }


@dataclass
class PcbDesignRule:
    """A PCB design rule."""
    name: str = ""
    rule_type: str = ""
    value_mm: float = 0.0
    scope: str = "all"
    priority: int = 0
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rule_type": self.rule_type,
            "value_mm": self.value_mm,
            "scope": self.scope,
            "priority": self.priority,
            "enabled": self.enabled,
        }


@dataclass
class PolygonVertex:
    """多边形顶点，支持直线和圆弧"""
    position: Point2D = field(default_factory=Point2D)
    kind: int = 0  # 0=line segment, 1=arc
    # 以下字段仅在 kind=1 时有意义
    cx_mm: float = 0.0  # 弧心 X
    cy_mm: float = 0.0  # 弧心 Y
    start_angle: float = 0.0
    end_angle: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "position": self.position.to_dict(),
            "kind": self.kind,
            "x_mm": round(self.position.x_mm, 6),   # 向后兼容
            "y_mm": round(self.position.y_mm, 6),   # 向后兼容
        }
        if self.kind == 1:
            d["cx_mm"] = round(self.cx_mm, 6)
            d["cy_mm"] = round(self.cy_mm, 6)
            d["start_angle"] = self.start_angle
            d["end_angle"] = self.end_angle
        return d


@dataclass
class PcbFromTo:
    """飞线（ratsnest）连接"""
    start: Point2D = field(default_factory=Point2D)
    end: Point2D = field(default_factory=Point2D)
    net: str = ""
    net_id: int = -1
    from_component: str = ""
    from_pad: str = ""
    to_component: str = ""
    to_pad: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "net": self.net,
            "net_id": self.net_id,
            "from_component": self.from_component,
            "from_pad": self.from_pad,
            "to_component": self.to_component,
            "to_pad": self.to_pad,
        }


@dataclass
class PcbDimension:
    """PCB尺寸标注"""
    kind: str = ""  # linear, radial, diameter, datum, center, angular, baseline, leader
    start: Point2D = field(default_factory=Point2D)
    end: Point2D = field(default_factory=Point2D)
    text_position: Point2D = field(default_factory=Point2D)
    value_text: str = ""
    height_mm: float = 0.0
    layer: str = ""
    layer_id: int = 0
    line_width_mm: float = 0.0
    text_height_mm: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "text_position": self.text_position.to_dict(),
            "value_text": self.value_text,
            "height_mm": self.height_mm,
            "layer": self.layer,
            "layer_id": self.layer_id,
            "line_width_mm": round(self.line_width_mm, 6),
            "text_height_mm": round(self.text_height_mm, 6),
        }


@dataclass
class PcbPolygonPour:
    """A polygon pour definition."""
    net: str = ""
    net_id: int = 0
    layer: str = ""
    layer_id: int = 0
    vertices: list[PolygonVertex] = field(default_factory=list)
    pour_mode: str = "solid"
    clearance_mm: float = 0.254
    min_track_width_mm: float = 0.254

    def to_dict(self) -> dict[str, Any]:
        return {
            "net": self.net,
            "layer": self.layer,
            "vertices": [v.to_dict() for v in self.vertices],
            "pour_mode": self.pour_mode,
            "clearance_mm": _round_coord(self.clearance_mm),
            "min_track_width_mm": _round_coord(self.min_track_width_mm),
        }


@dataclass
class PcbModel3DRef:
    """A 3D model reference."""
    name: str = ""
    file_path: str = ""
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    offset_x_mm: float = 0.0
    offset_y_mm: float = 0.0
    offset_z_mm: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "file_path": self.file_path,
            "rotation": {
                "x": _round_coord(self.rotation_x, 2),
                "y": _round_coord(self.rotation_y, 2),
                "z": _round_coord(self.rotation_z, 2),
            },
            "offset_mm": {
                "x": _round_coord(self.offset_x_mm),
                "y": _round_coord(self.offset_y_mm),
                "z": _round_coord(self.offset_z_mm),
            },
        }


@dataclass
class PcbDocument:
    """Complete parsed PCB document."""
    filename: str = ""
    board_outline: BoardOutline = field(default_factory=BoardOutline)
    layer_stackup: list[StackupLayer] = field(default_factory=list)
    nets: list[PcbNet] = field(default_factory=list)
    components: list[PcbComponent] = field(default_factory=list)
    tracks: list[PcbTrack] = field(default_factory=list)
    arcs: list[PcbArc] = field(default_factory=list)
    pads: list[PcbPad] = field(default_factory=list)
    vias: list[PcbVia] = field(default_factory=list)
    fills: list[PcbFill] = field(default_factory=list)
    regions: list[PcbRegion] = field(default_factory=list)
    texts: list[PcbText] = field(default_factory=list)
    polygon_pours: list[PcbPolygonPour] = field(default_factory=list)
    design_rules: list[PcbDesignRule] = field(default_factory=list)
    model_3d_refs: list[PcbModel3DRef] = field(default_factory=list)
    from_tos: list[PcbFromTo] = field(default_factory=list)
    dimensions: list[PcbDimension] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "board_outline": self.board_outline.to_dict(),
            "layer_stackup": [l.to_dict() for l in self.layer_stackup],
            "nets": [n.to_dict() for n in self.nets],
            "components": [c.to_dict() for c in self.components],
            "tracks": [t.to_dict() for t in self.tracks],
            "arcs": [a.to_dict() for a in self.arcs],
            "pads": [p.to_dict() for p in self.pads],
            "vias": [v.to_dict() for v in self.vias],
            "fills": [f.to_dict() for f in self.fills],
            "regions": [r.to_dict() for r in self.regions],
            "texts": [t.to_dict() for t in self.texts],
            "polygon_pours": [p.to_dict() for p in self.polygon_pours],
            "design_rules": [r.to_dict() for r in self.design_rules],
            "model_3d_refs": [m.to_dict() for m in self.model_3d_refs],
            "from_tos": [ft.to_dict() for ft in self.from_tos],
            "dimensions": [d.to_dict() for d in self.dimensions],
            "statistics": {
                "component_count": len(self.components),
                "track_count": len(self.tracks),
                "pad_count": len(self.pads),
                "via_count": len(self.vias),
                "net_count": len(self.nets),
                "layer_count": len(self.layer_stackup),
                "from_to_count": len(self.from_tos),
                "dimension_count": len(self.dimensions),
            },
        }
