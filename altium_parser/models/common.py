"""Common data models shared across all Altium file type parsers."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Point2D:
    """A 2D coordinate point."""
    x_mm: float = 0.0
    y_mm: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {"x_mm": self.x_mm, "y_mm": self.y_mm}


@dataclass
class BoundingBox:
    """Axis-aligned bounding box."""
    x1_mm: float = 0.0
    y1_mm: float = 0.0
    x2_mm: float = 0.0
    y2_mm: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {"x1_mm": self.x1_mm, "y1_mm": self.y1_mm,
                "x2_mm": self.x2_mm, "y2_mm": self.y2_mm}


@dataclass
class Color:
    """RGB color."""
    r: int = 0
    g: int = 0
    b: int = 0

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_dict(self) -> dict[str, Any]:
        return {"r": self.r, "g": self.g, "b": self.b, "hex": self.to_hex()}


@dataclass
class LayerRef:
    """Reference to a PCB layer."""
    id: int = 0
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}


def model_to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass model to a plain dict.

    Handles nested dataclasses, lists, and basic types.
    """
    if obj is None:
        return None
    if isinstance(obj, (int, float, str, bool)):
        return obj
    if isinstance(obj, list):
        return [model_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: model_to_dict(v) for k, v in obj.items()}
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dataclass_fields__"):
        return {k: model_to_dict(v) for k, v in asdict(obj).items()}
    return obj
