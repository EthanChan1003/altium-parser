"""Parser for Altium PrjPcb (project) files."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ..models.project import AltiumProject, ProjectDocument

logger = logging.getLogger(__name__)


class PrjPcbParser:
    """Parser for .PrjPcb project files (plain text INI format)."""

    def __init__(self, file_path: str | Path):
        self._file_path = Path(file_path)

    def parse(self) -> AltiumProject:
        """Parse the PrjPcb file and return an AltiumProject model."""
        project = AltiumProject(filename=self._file_path.name)

        text = self._file_path.read_text(encoding="utf-8", errors="replace")
        sections = self._parse_ini(text)

        # Extract design section
        design = sections.get("Design", {})
        project.version = design.get("Version", "")

        # Extract document references
        doc_count = int(design.get("DocumentCount", "0"))
        for i in range(1, doc_count + 1):
            doc_section = sections.get(f"Document{i}", {})
            if not doc_section:
                continue

            doc = ProjectDocument()
            doc.path = doc_section.get("DocumentPath", "")
            doc.doc_type = self._infer_doc_type(doc.path)
            project.documents.append(doc)

        # Store remaining parameters
        for key, value in design.items():
            if key not in ("Version", "DocumentCount"):
                project.parameters[key] = value

        logger.info(
            "Parsed %s: %d documents referenced",
            self._file_path.name, len(project.documents),
        )
        return project

    def _parse_ini(self, text: str) -> dict[str, dict[str, str]]:
        """Parse INI-style text into sections.

        Altium PrjPcb files use a variant of INI format with [Section] headers
        and Key=Value pairs.
        """
        sections: dict[str, dict[str, str]] = {}
        current_section = ""

        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith(";") or line.startswith("#"):
                continue

            # Section header
            match = re.match(r"^\[(.+)\]$", line)
            if match:
                current_section = match.group(1)
                if current_section not in sections:
                    sections[current_section] = {}
                continue

            # Key=Value pair
            eq_pos = line.find("=")
            if eq_pos > 0 and current_section:
                key = line[:eq_pos].strip()
                value = line[eq_pos + 1:].strip()
                sections[current_section][key] = value

        return sections

    @staticmethod
    def _infer_doc_type(path: str) -> str:
        """Infer document type from file extension."""
        ext = Path(path).suffix.lower()
        type_map = {
            ".schdoc": "SchDoc",
            ".pcbdoc": "PcbDoc",
            ".schlib": "SchLib",
            ".pcblib": "PcbLib",
            ".outjob": "OutputJob",
            ".harness": "Harness",
            ".schdot": "SchDot",
        }
        return type_map.get(ext, ext.lstrip(".").upper() if ext else "Unknown")
