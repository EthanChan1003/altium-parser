"""Data models for Altium PrjPcb (project) files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProjectDocument:
    """A document reference within an Altium project."""
    path: str = ""
    doc_type: str = ""  # SchDoc, PcbDoc, etc.

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "doc_type": self.doc_type,
        }


@dataclass
class AltiumProject:
    """Parsed Altium project (.PrjPcb) file."""
    filename: str = ""
    version: str = ""
    documents: list[ProjectDocument] = field(default_factory=list)
    parameters: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "documents": [d.to_dict() for d in self.documents],
            "parameters": self.parameters,
        }
