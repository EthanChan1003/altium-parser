"""JSON serializer for Altium parser output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def serialize_to_json(
    model: Any,
    file_type: str,
    source_file: str,
    output_path: str | Path | None = None,
    pretty: bool = True,
) -> str:
    """Serialize a parsed Altium model to JSON.

    Args:
        model: Any model with a to_dict() method.
        file_type: File type string (e.g., "SchDoc", "PcbDoc").
        source_file: Original source filename.
        output_path: If provided, write JSON to this file.
        pretty: If True, use indented formatting.

    Returns:
        The JSON string.
    """
    envelope = {
        "schema_version": "1.1",
        "generator": "altium-parser",
        "file_type": file_type,
        "source_file": source_file,
        "data": model.to_dict(),
    }

    indent = 2 if pretty else None
    json_str = json.dumps(envelope, indent=indent, ensure_ascii=False, default=str)

    if output_path:
        Path(output_path).write_text(json_str, encoding="utf-8")

    return json_str
