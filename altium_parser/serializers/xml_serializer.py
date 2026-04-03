"""XML serializer for Altium parser output."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from xml.dom import minidom


def serialize_to_xml(
    model: Any,
    file_type: str,
    source_file: str,
    output_path: str | Path | None = None,
    pretty: bool = True,
) -> str:
    """Serialize a parsed Altium model to XML.

    Args:
        model: Any model with a to_dict() method.
        file_type: File type string (e.g., "SchDoc", "PcbDoc").
        source_file: Original source filename.
        output_path: If provided, write XML to this file.
        pretty: If True, use indented formatting.

    Returns:
        The XML string.
    """
    root = ET.Element("altium-document")
    root.set("schema-version", "1.0")
    root.set("generator", "altium-parser")
    root.set("file-type", file_type)
    root.set("source-file", source_file)

    data_dict = model.to_dict()
    _dict_to_xml(root, data_dict)

    xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)

    if pretty:
        xml_str = _pretty_print_xml(xml_str)

    full_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

    if output_path:
        Path(output_path).write_text(full_xml, encoding="utf-8")

    return full_xml


def _dict_to_xml(parent: ET.Element, data: Any, tag_name: str = "") -> None:
    """Recursively convert a dict/list/scalar to XML elements."""
    if isinstance(data, dict):
        for key, value in data.items():
            xml_key = _to_xml_tag(key)
            if isinstance(value, (dict, list)):
                child = ET.SubElement(parent, xml_key)
                _dict_to_xml(child, value, xml_key)
            elif value is None:
                pass
            else:
                # Simple scalar → attribute
                parent.set(xml_key, str(value))

    elif isinstance(data, list):
        # For lists, create child elements with singular tag name
        singular = _singularize(tag_name)
        for item in data:
            child = ET.SubElement(parent, singular)
            if isinstance(item, dict):
                _dict_to_xml(child, item, singular)
            else:
                child.text = str(item)

    else:
        parent.text = str(data) if data is not None else ""


def _to_xml_tag(key: str) -> str:
    """Convert a Python dict key to a valid XML tag name."""
    # Replace underscores with hyphens for XML convention
    tag = key.replace("_", "-")
    # Ensure valid XML name
    if tag and tag[0].isdigit():
        tag = "n" + tag
    return tag


def _singularize(tag: str) -> str:
    """Naive singularization of a plural XML tag name."""
    singular_map = {
        "components": "component",
        "pins": "pin",
        "wires": "wire",
        "buses": "bus",
        "bus-entries": "bus-entry",
        "net-labels": "net-label",
        "power-ports": "power-port",
        "ports": "port",
        "junctions": "junction",
        "no-ercs": "no-erc",
        "polylines": "polyline",
        "polygons": "polygon",
        "rectangles": "rectangle",
        "lines": "line",
        "arcs": "arc",
        "ellipses": "ellipse",
        "round-rectangles": "round-rectangle",
        "beziers": "bezier",
        "texts": "text",
        "labels": "label",
        "images": "image",
        "sheet-symbols": "sheet-symbol",
        "parameters": "parameter",
        "graphic-primitives": "graphic-primitive",
        "tracks": "track",
        "pads": "pad",
        "vias": "via",
        "fills": "fill",
        "regions": "region",
        "nets": "net",
        "layer-stackup": "layer",
        "design-rules": "rule",
        "polygon-pours": "polygon-pour",
        "model-3d-refs": "model-3d-ref",
        "vertices": "vertex",
        "points": "point",
        "entries": "entry",
        "documents": "document",
        "symbols": "symbol",
        "footprints": "footprint",
    }
    return singular_map.get(tag, tag.rstrip("s") if tag.endswith("s") else tag + "-item")


def _pretty_print_xml(xml_str: str) -> str:
    """Pretty-print XML string with proper indentation."""
    try:
        dom = minidom.parseString(xml_str)
        pretty = dom.toprettyxml(indent="  ")
        # Remove the XML declaration added by minidom (we add our own)
        lines = pretty.split("\n")
        if lines and lines[0].startswith("<?xml"):
            lines = lines[1:]
        # Remove blank lines
        lines = [line for line in lines if line.strip()]
        return "\n".join(lines)
    except Exception:
        return xml_str
