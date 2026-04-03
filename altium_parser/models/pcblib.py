"""Data models for Altium PcbLib (PCB footprint library) files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .pcb import PcbPad, PcbTrack, PcbArc, PcbText, PcbRegion, PcbModel3DRef


@dataclass
class PcbFootprint:
    """A PCB footprint definition in a library."""
    name: str = ""
    description: str = ""
    height_mm: float = 0.0
    pads: list[PcbPad] = field(default_factory=list)
    tracks: list[PcbTrack] = field(default_factory=list)
    arcs: list[PcbArc] = field(default_factory=list)
    texts: list[PcbText] = field(default_factory=list)
    regions: list[PcbRegion] = field(default_factory=list)
    model_3d_ref: PcbModel3DRef | None = None
    parameters: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "height_mm": self.height_mm,
            "pads": [p.to_dict() for p in self.pads],
            "tracks": [t.to_dict() for t in self.tracks],
            "arcs": [a.to_dict() for a in self.arcs],
            "texts": [t.to_dict() for t in self.texts],
            "regions": [r.to_dict() for r in self.regions],
            "parameters": self.parameters,
            "statistics": {
                "pad_count": len(self.pads),
                "track_count": len(self.tracks),
            },
        }
        if self.model_3d_ref:
            d["model_3d_ref"] = self.model_3d_ref.to_dict()
        return d


@dataclass
class PcbFootprintLibrary:
    """Parsed PCB footprint library (.PcbLib) file."""
    filename: str = ""
    footprints: list[PcbFootprint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "footprints": [f.to_dict() for f in self.footprints],
            "statistics": {
                "footprint_count": len(self.footprints),
            },
        }
