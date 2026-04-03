"""File extension to parser dispatcher."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .parsers.prjpcb_parser import PrjPcbParser
from .parsers.schdoc_parser import SchDocParser
from .parsers.pcbdoc_parser import PcbDocParser
from .parsers.schlib_parser import SchLibParser
from .parsers.pcblib_parser import PcbLibParser

# Map of supported file extensions to (parser_class, file_type_name)
PARSER_REGISTRY: dict[str, tuple[type, str]] = {
    ".prjpcb": (PrjPcbParser, "PrjPcb"),
    ".schdoc": (SchDocParser, "SchDoc"),
    ".pcbdoc": (PcbDocParser, "PcbDoc"),
    ".schlib": (SchLibParser, "SchLib"),
    ".pcblib": (PcbLibParser, "PcbLib"),
}

SUPPORTED_EXTENSIONS = set(PARSER_REGISTRY.keys())


def get_file_type(file_path: str | Path) -> str:
    """Get the Altium file type name from a file path."""
    ext = Path(file_path).suffix.lower()
    entry = PARSER_REGISTRY.get(ext)
    if entry:
        return entry[1]
    raise ValueError(f"Unsupported file extension '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")


def parse_file(file_path: str | Path) -> Any:
    """Parse an Altium file and return the appropriate model.

    Args:
        file_path: Path to the Altium file.

    Returns:
        The parsed model (AltiumProject, SchDocument, PcbDocument, etc.)

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    entry = PARSER_REGISTRY.get(ext)
    if not entry:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    parser_class, _ = entry
    parser = parser_class(path)
    return parser.parse()
