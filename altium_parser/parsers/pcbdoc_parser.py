"""Parser for Altium PcbDoc (PCB document) files."""

from __future__ import annotations

import logging
import struct
from pathlib import Path
from typing import Any

from ..core.ole_reader import OleReader
from ..core.kv_parser import parse_kv_record
from ..core.binary_reader import BinaryReader
from ..core.units import pcb_to_mm
from ..core.constants import layer_id_to_name, PAD_SHAPE_NAMES
from ..core.exceptions import CorruptedDataError
from ..models.common import Point2D, BoundingBox
from ..models.pcb import (
    PcbDocument, BoardOutline, StackupLayer, PcbNet, PcbComponent,
    PcbTrack, PcbArc, PcbPad, PcbVia, PcbFill, PcbRegion,
    PcbText, PcbDesignRule, PcbPolygonPour,
)

logger = logging.getLogger(__name__)

# Binary record type identifiers (from altium2kicad)
RECORD_TYPE_TRACK = 0x04
RECORD_TYPE_VIA = 0x03
RECORD_TYPE_ARC = 0x01
RECORD_TYPE_PAD = 0x02
RECORD_TYPE_FILL = 0x06

# Binary mil to mm conversion factor
# 1 mil = 0.0254 mm, and binary mil uses 10000 units per mil
BINARY_MIL_TO_MM = 1.0 / 39.370078740158 / 10000.0


class PcbDocParser:
    """Parser for .PcbDoc files."""

    def __init__(self, file_path: str | Path):
        self._file_path = Path(file_path)

    def parse(self) -> PcbDocument:
        """Parse the PcbDoc file and return a PcbDocument model."""
        doc = PcbDocument(filename=self._file_path.name)

        with OleReader(self._file_path) as ole:
            logger.debug("OLE structure:\n%s", ole.dump_structure())

            # Parse nets first (needed for net_id → name resolution)
            net_map = self._parse_nets(ole)
            for net in net_map.values():
                doc.nets.append(net)

            # Parse board info and layer stackup
            self._parse_board(ole, doc)

            # Parse components
            doc.components = self._parse_components(ole)

            # Parse primitives
            doc.tracks = self._parse_tracks(ole, net_map)
            doc.arcs = self._parse_arcs(ole, net_map)
            doc.pads = self._parse_pads(ole, net_map)
            doc.vias = self._parse_vias(ole, net_map)
            doc.fills = self._parse_fills(ole, net_map)
            doc.texts = self._parse_texts(ole)
            doc.regions = self._parse_regions(ole, net_map)
            doc.design_rules = self._parse_rules(ole)
            doc.polygon_pours = self._parse_polygons(ole, net_map)

        logger.info(
            "Parsed %s: %d components, %d tracks, %d pads, %d vias, %d nets",
            self._file_path.name,
            len(doc.components), len(doc.tracks), len(doc.pads),
            len(doc.vias), len(doc.nets),
        )
        return doc

    # -- Utility: read PcbDoc record stream --

    def _read_pcb_records(self, ole: OleReader, storage: str) -> list[dict[str, str]]:
        """Read text-based records from a PcbDoc storage (Header+Data pattern).

        Many PcbDoc storages use text-based pipe-delimited records where each
        record is prefixed with a 4-byte length.
        """
        data_path = f"{storage}/Data"
        data = ole.read_stream_safe(data_path)
        if not data:
            return []

        records = []
        reader = BinaryReader(data)

        while not reader.is_eof() and reader.remaining() >= 4:
            try:
                record_len = reader.read_uint32()
                if record_len == 0 or record_len > reader.remaining():
                    break
                record_data = reader.read_bytes(record_len)
                kv = parse_kv_record(record_data)
                if kv:
                    records.append(kv)
            except CorruptedDataError:
                break

        return records

    def _read_pcb_binary_records(self, ole: OleReader, storage: str) -> list[bytes]:
        """Read binary records from a PcbDoc storage.

        Binary records are prefixed with a 4-byte length field.
        """
        data_path = f"{storage}/Data"
        data = ole.read_stream_safe(data_path)
        if not data:
            return []

        records = []
        reader = BinaryReader(data)

        while not reader.is_eof() and reader.remaining() >= 4:
            try:
                record_len = reader.read_uint32()
                if record_len == 0 or record_len > reader.remaining():
                    break
                record_data = reader.read_bytes(record_len)
                records.append(record_data)
            except CorruptedDataError:
                break

        return records

    def _read_binary_records_typed(
        self, ole: OleReader, storage: str, expected_type: int
    ) -> list[tuple[int, bytes]]:
        """Read typed binary records from a PcbDoc storage.

        Format: [record_type (1 byte)][length (4 bytes)][data (length bytes)]
        Returns list of (record_index, data) tuples.
        """
        data = ole.read_stream_safe(f"{storage}/Data")
        if not data:
            return []

        records = []
        pos = 0

        while pos < len(data) - 5:
            rec_type = data[pos]
            if rec_type != expected_type:
                # Try to skip to next record or abort
                logger.debug(
                    "Unexpected record type 0x%02x at pos %d (expected 0x%02x)",
                    rec_type, pos, expected_type
                )
                break

            pos += 1
            if pos + 4 > len(data):
                break

            rec_len = struct.unpack("<I", data[pos:pos+4])[0]
            pos += 4

            if rec_len == 0 or rec_len > 10000 or pos + rec_len > len(data):
                break

            rec_data = data[pos:pos+rec_len]
            records.append((len(records), rec_data))
            pos += rec_len

        return records

    @staticmethod
    def _bmil_to_mm(data: bytes) -> float:
        """Convert binary mil (4-byte signed int) to millimeters.

        Binary mil: internal Altium coordinate unit
        1 mil = 0.0254 mm, binary uses 10000 units per mil
        """
        val = struct.unpack("<i", data)[0]
        return val * BINARY_MIL_TO_MM

    @staticmethod
    def _get_int16(data: bytes, offset: int) -> int:
        """Get signed 16-bit integer from binary data."""
        if offset + 2 > len(data):
            return 0
        return struct.unpack("<h", data[offset:offset+2])[0]

    @staticmethod
    def _get_uint8(data: bytes, offset: int) -> int:
        """Get unsigned 8-bit integer from binary data."""
        if offset >= len(data):
            return 0
        return data[offset]

    # -- Net parsing --

    def _parse_nets(self, ole: OleReader) -> dict[int, PcbNet]:
        """Parse Nets6 storage to build net_id → PcbNet mapping."""
        net_map: dict[int, PcbNet] = {}
        records = self._read_pcb_records(ole, "Nets6")

        for i, kv in enumerate(records):
            net = PcbNet()
            net.id = i + 1  # Net IDs are 1-based
            net.name = kv.get("NAME", f"Net{i+1}")
            net_map[net.id] = net

        # Always include unconnected net
        net_map[0] = PcbNet(id=0, name="No Net")

        logger.debug("Parsed %d nets", len(net_map) - 1)
        return net_map

    # -- Board parsing --

    def _parse_board(self, ole: OleReader, doc: PcbDocument) -> None:
        """Parse Board6 for board outline and layer stackup."""
        records = self._read_pcb_records(ole, "Board6")
        if not records:
            logger.warning("Board6 storage not found or empty")
            return

        kv = records[0]  # First record is the main board record

        # Board outline vertices
        vertices = []
        vertex_count = self._get_int(kv, "SHAPEBASEDREGION_VERTICECOUNT",
                         self._get_int(kv, "VERTICECOUNT", 0))

        for i in range(vertex_count):
            x = pcb_to_mm(self._get_int(kv, f"VX{i}", 0))
            y = pcb_to_mm(self._get_int(kv, f"VY{i}", 0))
            vertices.append(Point2D(x_mm=x, y_mm=y))

        if not vertices:
            # Try alternate board outline extraction from tracks on keepout layer
            pass

        if vertices:
            xs = [v.x_mm for v in vertices]
            ys = [v.y_mm for v in vertices]
            bbox = BoundingBox(
                x1_mm=min(xs), y1_mm=min(ys),
                x2_mm=max(xs), y2_mm=max(ys),
            )
            doc.board_outline = BoardOutline(vertices=vertices, bounding_box=bbox)

        # Layer stackup
        layer_count = self._get_int(kv, "LAYERCOUNT", 2)
        for i in range(1, layer_count + 1):
            layer = StackupLayer()
            layer.id = i
            prefix = f"LAYER{i}"
            layer.name = kv.get(f"{prefix}NAME", layer_id_to_name(i))
            layer.copper_thickness_mm = self._get_float(kv, f"{prefix}COPTHICK", 0.035)
            layer.dielectric_constant = self._get_float(kv, f"{prefix}DIELCONST", 4.2)
            layer.dielectric_height_mm = self._get_float(kv, f"{prefix}DIELHEIGHT", 0.2)
            layer.material = kv.get(f"{prefix}DIELMATERIAL", "FR-4")
            doc.layer_stackup.append(layer)

        # If no detailed stackup, create default top/bottom
        if not doc.layer_stackup:
            doc.layer_stackup = [
                StackupLayer(id=1, name="Top Layer"),
                StackupLayer(id=32, name="Bottom Layer"),
            ]

    # -- Component parsing --

    def _parse_components(self, ole: OleReader) -> list[PcbComponent]:
        """Parse Components6 storage."""
        records = self._read_pcb_records(ole, "Components6")
        components = []

        for kv in records:
            comp = PcbComponent()
            # PcbDoc uses SOURCEDESIGNATOR, not DESIGNATOR
            comp.designator = kv.get("SOURCEDESIGNATOR", kv.get("DESIGNATOR", ""))
            # PcbDoc uses SOURCEDESCRIPTION for component description/comment
            comp.comment = kv.get("SOURCEDESCRIPTION", kv.get("COMMENT", ""))
            comp.footprint_name = kv.get("PATTERN", kv.get("FOOTPRINTDESCRIPTION", ""))
            # X and Y may include unit suffix (e.g., "4104.4882mil")
            comp.position = Point2D(
                x_mm=self._parse_coordinate(kv.get("X", "0")),
                y_mm=self._parse_coordinate(kv.get("Y", "0")),
            )
            comp.rotation = self._get_float(kv, "ROTATION", 0.0)
            layer_str = kv.get("LAYER", "TOP").upper()
            comp.layer = "bottom" if layer_str == "BOTTOM" or self._get_int(kv, "LAYER", 1) == 32 else "top"
            comp.is_locked = kv.get("LOCKED", "FALSE").upper() == "TRUE"
            comp.source_unique_id = kv.get("SOURCEFOOTPRINTLIBRARY", "")
            components.append(comp)

        return components

    # -- Track parsing --

    def _parse_tracks(self, ole: OleReader, net_map: dict[int, PcbNet]) -> list[PcbTrack]:
        """Parse Tracks6 storage.

        Tracks6 uses binary format:
        [record_type=0x04][length:4bytes][data]

        Data structure (from altium2kicad):
        - byte 0: layer
        - byte 3-4: net (int16)
        - byte 7-8: component (int16)
        - byte 13-16: X1 (int32, binary mil)
        - byte 17-20: Y1 (int32, binary mil)
        - byte 21-24: X2 (int32, binary mil)
        - byte 25-28: Y2 (int32, binary mil)
        - byte 29-32: width (int32, binary mil)
        """
        tracks = []

        # Try binary format first
        records = self._read_binary_records_typed(ole, "Tracks6", RECORD_TYPE_TRACK)

        if records:
            logger.debug("Parsing %d binary track records", len(records))
            for idx, rec_data in records:
                if len(rec_data) < 33:
                    continue

                track = PcbTrack()
                track.layer_id = self._get_uint8(rec_data, 0)
                track.layer = layer_id_to_name(track.layer_id)
                track.net_id = self._get_int16(rec_data, 3)
                track.net = net_map.get(track.net_id, PcbNet()).name
                track.component_id = self._get_int16(rec_data, 7)

                track.start = Point2D(
                    x_mm=self._bmil_to_mm(rec_data[13:17]),
                    y_mm=self._bmil_to_mm(rec_data[17:21]),
                )
                track.end = Point2D(
                    x_mm=self._bmil_to_mm(rec_data[21:25]),
                    y_mm=self._bmil_to_mm(rec_data[25:29]),
                )
                track.width_mm = self._bmil_to_mm(rec_data[29:33])
                tracks.append(track)
        else:
            # Fallback to text format
            kv_records = self._read_pcb_records(ole, "Tracks6")
            for kv in kv_records:
                track = PcbTrack()
                track.start = Point2D(
                    x_mm=pcb_to_mm(self._get_int(kv, "X1", 0)),
                    y_mm=pcb_to_mm(self._get_int(kv, "Y1", 0)),
                )
                track.end = Point2D(
                    x_mm=pcb_to_mm(self._get_int(kv, "X2", 0)),
                    y_mm=pcb_to_mm(self._get_int(kv, "Y2", 0)),
                )
                track.width_mm = pcb_to_mm(self._get_int(kv, "WIDTH", 0))
                track.layer_id = self._get_int(kv, "LAYER", 1)
                track.layer = layer_id_to_name(track.layer_id)
                track.net_id = self._get_int(kv, "NET", 0)
                track.net = net_map.get(track.net_id, PcbNet()).name
                track.component_id = self._get_int(kv, "COMPONENT", -1)
                tracks.append(track)

        return tracks

    # -- Arc parsing --

    def _parse_arcs(self, ole: OleReader, net_map: dict[int, PcbNet]) -> list[PcbArc]:
        """Parse Arcs6 storage.

        Arcs6 uses binary format:
        [record_type=0x01][length:4bytes][data]

        Data structure (from altium2kicad):
        - byte 0: layer
        - byte 3-4: net (int16)
        - byte 7-8: component (int16)
        - byte 13-16: X (center, int32, binary mil)
        - byte 17-20: Y (center, int32, binary mil)
        - byte 21-24: radius (int32, binary mil)
        - byte 25-32: start angle (double)
        - byte 33-40: end angle (double)
        - byte 41-44: width (int32, binary mil)
        """
        arcs = []

        # Try binary format first
        records = self._read_binary_records_typed(ole, "Arcs6", RECORD_TYPE_ARC)

        if records:
            logger.debug("Parsing %d binary arc records", len(records))
            for idx, rec_data in records:
                if len(rec_data) < 45:
                    continue

                arc = PcbArc()
                arc.layer_id = self._get_uint8(rec_data, 0)
                arc.layer = layer_id_to_name(arc.layer_id)
                arc.net_id = self._get_int16(rec_data, 3)
                arc.net = net_map.get(arc.net_id, PcbNet()).name
                arc.component_id = self._get_int16(rec_data, 7)

                arc.center = Point2D(
                    x_mm=self._bmil_to_mm(rec_data[13:17]),
                    y_mm=self._bmil_to_mm(rec_data[17:21]),
                )
                arc.radius_mm = self._bmil_to_mm(rec_data[21:25])

                # Start and end angles are doubles (8 bytes each)
                if len(rec_data) >= 41:
                    arc.start_angle = struct.unpack("<d", rec_data[25:33])[0]
                    arc.end_angle = struct.unpack("<d", rec_data[33:41])[0]
                    arc.width_mm = self._bmil_to_mm(rec_data[41:45])
                else:
                    arc.start_angle = 0.0
                    arc.end_angle = 360.0
                    arc.width_mm = 0.0

                arcs.append(arc)
        else:
            # Fallback to text format
            kv_records = self._read_pcb_records(ole, "Arcs6")
            for kv in kv_records:
                arc = PcbArc()
                arc.center = Point2D(
                    x_mm=pcb_to_mm(self._get_int(kv, "LOCATION.X", self._get_int(kv, "X", 0))),
                    y_mm=pcb_to_mm(self._get_int(kv, "LOCATION.Y", self._get_int(kv, "Y", 0))),
                )
                arc.radius_mm = pcb_to_mm(self._get_int(kv, "RADIUS", 0))
                arc.start_angle = self._get_float(kv, "STARTANGLE", 0.0)
                arc.end_angle = self._get_float(kv, "ENDANGLE", 360.0)
                arc.width_mm = pcb_to_mm(self._get_int(kv, "WIDTH", 0))
                arc.layer_id = self._get_int(kv, "LAYER", 1)
                arc.layer = layer_id_to_name(arc.layer_id)
                arc.net_id = self._get_int(kv, "NET", 0)
                arc.net = net_map.get(arc.net_id, PcbNet()).name
                arcs.append(arc)

        return arcs

    # -- Pad parsing --

    def _parse_pads(self, ole: OleReader, net_map: dict[int, PcbNet]) -> list[PcbPad]:
        """Parse Pads6 storage.

        Pads6 uses a complex binary format with embedded sub-records:
        [record_type=0x02][sub_records...][pad_data]

        Format (from altium2kicad):
        - byte 0: record type (0x02)
        - Then 6 embedded sub-records, each with [length:4bytes][data]
        - Pad data fields start at position (starts[4] - 23)

        Pad data offsets (from pad_data_pos):
        - byte 23: layer
        - byte 26-27: net (int16)
        - byte 30-31: component (int16)
        - byte 36-39: X (int32, binary mil)
        - byte 40-43: Y (int32, binary mil)
        - byte 44-47: XSIZE (int32, binary mil)
        - byte 48-51: YSIZE (int32, binary mil)
        - byte 52-55: MIDXSIZE
        - byte 56-59: MIDYSIZE
        - byte 60-63: BOTXSIZE
        - byte 64-67: BOTYSIZE
        - byte 68-71: holesize (int32, binary mil)
        - byte 72: shape
        - byte 75-82: rotation (double)
        - byte 83: plated
        """
        pads = []

        # Read raw data
        data = ole.read_stream_safe("Pads6/Data")
        if not data:
            return pads

        pos = 0
        while pos < len(data) - 100:
            # Check record type
            if data[pos] != RECORD_TYPE_PAD:
                break

            pos += 1  # Skip record type

            # Parse the 6 embedded sub-records to find the data position
            tpos = pos  # Start from current position
            lengths = []
            for _ in range(6):
                if tpos + 4 > len(data):
                    break
                sublen = struct.unpack("<I", data[tpos:tpos+4])[0]
                lengths.append(sublen)
                tpos += 4 + sublen

            if len(lengths) < 5:
                break

            # Calculate pad data start position
            # starts[4] = pos + sum(4 + lengths[i]) for i in 0..3 + 4
            # But we want starts[4] - 23
            starts_4 = pos
            for i in range(4):
                starts_4 += 4 + lengths[i]
            starts_4 += 4  # Move to start of 5th sub-record content

            pad_data_pos = starts_4 - 23

            # Check bounds
            if pad_data_pos + 84 > len(data):
                break

            # Extract pad fields
            pad = PcbPad()

            # Name: from first sub-record
            if lengths[0] > 0 and pos + 4 < len(data):
                name_data = data[pos + 4:pos + 4 + lengths[0]]
                # First byte of name_data is the actual name length
                if len(name_data) > 1:
                    name_len = name_data[0]
                    pad.designator = name_data[1:1 + name_len].decode('utf-8', errors='replace')

            # Layer at offset 23
            pad.layer_id = data[pad_data_pos + 23]
            pad.layer = layer_id_to_name(pad.layer_id)

            # Net at offset 26-27
            pad.net_id = struct.unpack("<h", data[pad_data_pos + 26:pad_data_pos + 28])[0]
            pad.net = net_map.get(pad.net_id, PcbNet()).name

            # Component at offset 30-31
            pad.component_id = struct.unpack("<h", data[pad_data_pos + 30:pad_data_pos + 32])[0]

            # Position at offset 36-43
            pad.position = Point2D(
                x_mm=self._bmil_to_mm(data[pad_data_pos + 36:pad_data_pos + 40]),
                y_mm=self._bmil_to_mm(data[pad_data_pos + 40:pad_data_pos + 44]),
            )

            # Sizes at offset 44-67
            pad.top_size = Point2D(
                x_mm=self._bmil_to_mm(data[pad_data_pos + 44:pad_data_pos + 48]),
                y_mm=self._bmil_to_mm(data[pad_data_pos + 48:pad_data_pos + 52]),
            )
            pad.mid_size = Point2D(
                x_mm=self._bmil_to_mm(data[pad_data_pos + 52:pad_data_pos + 56]),
                y_mm=self._bmil_to_mm(data[pad_data_pos + 56:pad_data_pos + 60]),
            )
            pad.bottom_size = Point2D(
                x_mm=self._bmil_to_mm(data[pad_data_pos + 60:pad_data_pos + 64]),
                y_mm=self._bmil_to_mm(data[pad_data_pos + 64:pad_data_pos + 68]),
            )

            # Hole size at offset 68-71
            pad.hole_size_mm = self._bmil_to_mm(data[pad_data_pos + 68:pad_data_pos + 72])

            # Shape at offset 72
            shape_id = data[pad_data_pos + 72]
            pad.shape = PAD_SHAPE_NAMES.get(shape_id, f"shape_{shape_id}")

            # Rotation at offset 75-82 (double)
            if pad_data_pos + 83 < len(data):
                pad.rotation = struct.unpack("<d", data[pad_data_pos + 75:pad_data_pos + 83])[0]
            else:
                pad.rotation = 0.0

            # Plated at offset 83
            if pad_data_pos + 84 <= len(data):
                pad.is_plated = data[pad_data_pos + 83] == 1
            else:
                pad.is_plated = True

            pad.pad_type = "through_hole" if pad.hole_size_mm > 0 else "smd"

            pads.append(pad)

            # Move to next record
            # Total record length = sum of all 6 sub-records + their length fields
            next_pos = pos
            for sublen in lengths:
                next_pos += 4 + sublen
            pos = next_pos

        # If no binary records found, try text format
        if not pads:
            kv_records = self._read_pcb_records(ole, "Pads6")
            for kv in kv_records:
                pad = PcbPad()
                pad.designator = kv.get("NAME", "")
                pad.position = Point2D(
                    x_mm=pcb_to_mm(self._get_int(kv, "X", 0)),
                    y_mm=pcb_to_mm(self._get_int(kv, "Y", 0)),
                )
                pad.top_size = Point2D(
                    x_mm=pcb_to_mm(self._get_int(kv, "XSIZE", 0)),
                    y_mm=pcb_to_mm(self._get_int(kv, "YSIZE", 0)),
                )
                pad.mid_size = Point2D(
                    x_mm=pcb_to_mm(self._get_int(kv, "MIDXSIZE", self._get_int(kv, "XSIZE", 0))),
                    y_mm=pcb_to_mm(self._get_int(kv, "MIDYSIZE", self._get_int(kv, "YSIZE", 0))),
                )
                pad.bottom_size = Point2D(
                    x_mm=pcb_to_mm(self._get_int(kv, "BOTXSIZE", self._get_int(kv, "XSIZE", 0))),
                    y_mm=pcb_to_mm(self._get_int(kv, "BOTYSIZE", self._get_int(kv, "YSIZE", 0))),
                )
                pad.hole_size_mm = pcb_to_mm(self._get_int(kv, "HOLESIZE", 0))
                shape_id = self._get_int(kv, "SHAPE", 1)
                pad.shape = PAD_SHAPE_NAMES.get(shape_id, f"shape_{shape_id}")
                pad.rotation = self._get_float(kv, "ROTATION", 0.0)
                pad.layer_id = self._get_int(kv, "LAYER", 74)  # Default to multi-layer
                pad.layer = layer_id_to_name(pad.layer_id)
                pad.net_id = self._get_int(kv, "NET", 0)
                pad.net = net_map.get(pad.net_id, PcbNet()).name
                pad.component_id = self._get_int(kv, "COMPONENT", -1)
                pad.is_plated = kv.get("PLATED", "TRUE").upper() == "TRUE"
                pad.pad_type = "through_hole" if pad.hole_size_mm > 0 else "smd"

                # Hole shape
                hole_shape_id = self._get_int(kv, "HOLESHAPE", 0)
                hole_shape_names = {0: "round", 1: "square", 2: "slot"}
                pad.hole_shape = hole_shape_names.get(hole_shape_id, "round")

                pads.append(pad)

        return pads

    # -- Via parsing --

    def _parse_vias(self, ole: OleReader, net_map: dict[int, PcbNet]) -> list[PcbVia]:
        """Parse Vias6 storage.

        Vias6 uses binary format:
        [record_type=0x03][length:4bytes][data]

        Data structure (from altium2kicad):
        - byte 0: layer1 (start layer)
        - byte 1: layer2 (end layer)
        - byte 3-4: net (int16)
        - byte 13-16: X (int32, binary mil)
        - byte 17-20: Y (int32, binary mil)
        - byte 21-24: diameter (int32, binary mil)
        - byte 25-28: holesize (int32, binary mil)
        """
        vias = []

        # Try binary format first
        records = self._read_binary_records_typed(ole, "Vias6", RECORD_TYPE_VIA)

        if records:
            logger.debug("Parsing %d binary via records", len(records))
            for idx, rec_data in records:
                if len(rec_data) < 29:
                    continue

                via = PcbVia()
                via.start_layer_id = self._get_uint8(rec_data, 0)
                via.end_layer_id = self._get_uint8(rec_data, 1)
                via.start_layer = layer_id_to_name(via.start_layer_id)
                via.end_layer = layer_id_to_name(via.end_layer_id)
                via.net_id = self._get_int16(rec_data, 3)
                via.net = net_map.get(via.net_id, PcbNet()).name

                via.position = Point2D(
                    x_mm=self._bmil_to_mm(rec_data[13:17]),
                    y_mm=self._bmil_to_mm(rec_data[17:21]),
                )
                via.diameter_mm = self._bmil_to_mm(rec_data[21:25])
                via.hole_mm = self._bmil_to_mm(rec_data[25:29])
                vias.append(via)
        else:
            # Fallback to text format
            kv_records = self._read_pcb_records(ole, "Vias6")
            for kv in kv_records:
                via = PcbVia()
                via.position = Point2D(
                    x_mm=pcb_to_mm(self._get_int(kv, "X", 0)),
                    y_mm=pcb_to_mm(self._get_int(kv, "Y", 0)),
                )
                via.diameter_mm = pcb_to_mm(self._get_int(kv, "DIAMETER", 0))
                via.hole_mm = pcb_to_mm(self._get_int(kv, "HOLESIZE", 0))
                via.start_layer_id = self._get_int(kv, "STARTLAYER", 1)
                via.end_layer_id = self._get_int(kv, "ENDLAYER", 32)
                via.start_layer = layer_id_to_name(via.start_layer_id)
                via.end_layer = layer_id_to_name(via.end_layer_id)
                via.net_id = self._get_int(kv, "NET", 0)
                via.net = net_map.get(via.net_id, PcbNet()).name
                via.is_tented_top = kv.get("TENTINGTOP", "FALSE").upper() == "TRUE"
                via.is_tented_bottom = kv.get("TENTINGBOTTOM", "FALSE").upper() == "TRUE"
                vias.append(via)

        return vias

    # -- Fill parsing --

    def _parse_fills(self, ole: OleReader, net_map: dict[int, PcbNet]) -> list[PcbFill]:
        """Parse Fills6 storage."""
        records = self._read_pcb_records(ole, "Fills6")
        fills = []

        for kv in records:
            fill = PcbFill()
            fill.corner1 = Point2D(
                x_mm=pcb_to_mm(self._get_int(kv, "X1", 0)),
                y_mm=pcb_to_mm(self._get_int(kv, "Y1", 0)),
            )
            fill.corner2 = Point2D(
                x_mm=pcb_to_mm(self._get_int(kv, "X2", 0)),
                y_mm=pcb_to_mm(self._get_int(kv, "Y2", 0)),
            )
            fill.rotation = self._get_float(kv, "ROTATION", 0.0)
            fill.layer_id = self._get_int(kv, "LAYER", 1)
            fill.layer = layer_id_to_name(fill.layer_id)
            fill.net_id = self._get_int(kv, "NET", 0)
            fill.net = net_map.get(fill.net_id, PcbNet()).name
            fills.append(fill)

        return fills

    # -- Text parsing --

    def _parse_texts(self, ole: OleReader) -> list[PcbText]:
        """Parse Texts6 storage."""
        records = self._read_pcb_records(ole, "Texts6")

        # Try to load WideStrings6 for UTF-16 text content
        wide_strings: dict[int, str] = {}
        ws_data = ole.read_stream_safe("WideStrings6/Data")
        if ws_data:
            wide_strings = self._parse_wide_strings(ws_data)

        texts = []
        for i, kv in enumerate(records):
            text = PcbText()
            # Prefer wide string if available
            text.content = wide_strings.get(i, kv.get("TEXT", ""))
            text.position = Point2D(
                x_mm=pcb_to_mm(self._get_int(kv, "X", 0)),
                y_mm=pcb_to_mm(self._get_int(kv, "Y", 0)),
            )
            text.height_mm = pcb_to_mm(self._get_int(kv, "HEIGHT", 100000))
            text.rotation = self._get_float(kv, "ROTATION", 0.0)
            text.layer_id = self._get_int(kv, "LAYER", 33)
            text.layer = layer_id_to_name(text.layer_id)
            text.is_mirrored = kv.get("MIRRORED", "FALSE").upper() == "TRUE"
            text.component_id = self._get_int(kv, "COMPONENT", -1)

            kind = self._get_int(kv, "TEXTKIND", 0)
            text.font = {0: "stroke", 1: "truetype", 2: "barcode"}.get(kind, "stroke")
            texts.append(text)

        return texts

    # -- Region parsing --

    def _parse_regions(self, ole: OleReader, net_map: dict[int, PcbNet]) -> list[PcbRegion]:
        """Parse Regions6 and ShapeBasedRegions6."""
        regions = []

        for storage_name in ("Regions6", "ShapeBasedRegions6"):
            records = self._read_pcb_records(ole, storage_name)
            for kv in records:
                region = PcbRegion()
                region.layer_id = self._get_int(kv, "LAYER", 1)
                region.layer = layer_id_to_name(region.layer_id)
                region.net_id = self._get_int(kv, "NET", 0)
                region.net = net_map.get(region.net_id, PcbNet()).name
                region.is_keepout = kv.get("KEEPOUT", "FALSE").upper() == "TRUE"
                region.kind = self._get_int(kv, "KIND", 0)

                # Parse vertices
                vertex_count = self._get_int(kv, "VERTICECOUNT", 0)
                for i in range(vertex_count):
                    x = pcb_to_mm(self._get_int(kv, f"VX{i}", 0))
                    y = pcb_to_mm(self._get_int(kv, f"VY{i}", 0))
                    region.vertices.append(Point2D(x_mm=x, y_mm=y))

                regions.append(region)

        return regions

    # -- Rules parsing --

    def _parse_rules(self, ole: OleReader) -> list[PcbDesignRule]:
        """Parse Rules6 storage."""
        records = self._read_pcb_records(ole, "Rules6")
        rules = []

        for kv in records:
            rule = PcbDesignRule()
            rule.name = kv.get("NAME", "")
            rule.rule_type = kv.get("RULEKIND", "")
            rule.priority = self._get_int(kv, "PRIORITY", 0)
            rule.enabled = kv.get("ENABLED", "TRUE").upper() == "TRUE"

            # Extract value based on rule type
            rule_kind = rule.rule_type.upper()
            if "CLEARANCE" in rule_kind:
                rule.value_mm = pcb_to_mm(self._get_int(kv, "GAP", self._get_int(kv, "VALUE", 0)))
            elif "WIDTH" in rule_kind:
                rule.value_mm = pcb_to_mm(self._get_int(kv, "MINWIDTH",
                                           self._get_int(kv, "PREFERREDWIDTH", 0)))
            elif "HOLESIZE" in rule_kind:
                rule.value_mm = pcb_to_mm(self._get_int(kv, "MINLIMIT",
                                           self._get_int(kv, "VALUE", 0)))
            else:
                rule.value_mm = pcb_to_mm(self._get_int(kv, "VALUE", 0))

            scope_str = kv.get("SCOPE1EXPRESSION", kv.get("SCOPE", "All"))
            rule.scope = scope_str
            rules.append(rule)

        return rules

    # -- Polygon pour parsing --

    def _parse_polygons(self, ole: OleReader, net_map: dict[int, PcbNet]) -> list[PcbPolygonPour]:
        """Parse Polygons6 storage."""
        records = self._read_pcb_records(ole, "Polygons6")
        polygons = []

        for kv in records:
            poly = PcbPolygonPour()
            poly.net_id = self._get_int(kv, "NET", 0)
            poly.net = net_map.get(poly.net_id, PcbNet()).name
            poly.layer_id = self._get_int(kv, "LAYER", 1)
            poly.layer = layer_id_to_name(poly.layer_id)
            poly.clearance_mm = pcb_to_mm(self._get_int(kv, "TRACKWIDTH", 0))
            poly.min_track_width_mm = pcb_to_mm(self._get_int(kv, "MINPRIMLENGTH", 0))

            pour_mode = self._get_int(kv, "POURMODE", 0)
            poly.pour_mode = {0: "none", 1: "solid", 2: "hatched"}.get(pour_mode, "solid")

            # Parse vertices
            vertex_count = self._get_int(kv, "VERTICECOUNT", 0)
            for i in range(vertex_count):
                x = pcb_to_mm(self._get_int(kv, f"VX{i}", 0))
                y = pcb_to_mm(self._get_int(kv, f"VY{i}", 0))
                poly.vertices.append(Point2D(x_mm=x, y_mm=y))

            polygons.append(poly)

        return polygons

    # -- Helpers --

    def _parse_wide_strings(self, data: bytes) -> dict[int, str]:
        """Parse WideStrings6 data stream into index → string map."""
        result: dict[int, str] = {}
        reader = BinaryReader(data)
        idx = 0

        while not reader.is_eof() and reader.remaining() >= 4:
            try:
                text = reader.read_widestring_pascal32()
                if text:
                    result[idx] = text
                idx += 1
            except CorruptedDataError:
                break

        return result

    @staticmethod
    def _get_int(kv: dict[str, str], key: str, default: int = 0) -> int:
        val = kv.get(key, "")
        if not val:
            return default
        try:
            return int(val)
        except ValueError:
            try:
                return int(float(val))
            except ValueError:
                return default

    @staticmethod
    def _get_float(kv: dict[str, str], key: str, default: float = 0.0) -> float:
        val = kv.get(key, "")
        if not val:
            return default
        try:
            return float(val)
        except ValueError:
            return default

    def _parse_coordinate(self, value: str) -> float:
        """Parse a coordinate value that may include a unit suffix.
        
        Examples:
            "4104.4882mil" -> pcb_to_mm(4104.4882)
            "2608.4252mil" -> pcb_to_mm(2608.4252)
            "100" -> pcb_to_mm(100)
        """
        if not value:
            return 0.0
        
        # Remove any unit suffix (mil, mm, in, etc.)
        value = value.strip()
        
        # Extract numeric part
        numeric_part = ""
        for char in value:
            if char.isdigit() or char in ".-+eE":
                numeric_part += char
            else:
                break  # Stop at first non-numeric character
        
        if not numeric_part:
            return 0.0
        
        try:
            numeric_value = float(numeric_part)
        except ValueError:
            return 0.0
        
        # Check for explicit mm unit
        if "mm" in value.lower():
            return numeric_value
        
        # Default: treat as PCB internal units (1 unit = 0.01 mil, or 0.000254 mm)
        # But if the value includes "mil" suffix, it's in mils
        if "mil" in value.lower():
            # Value is in mils, convert to mm
            return numeric_value * 0.0254
        
        # Otherwise, treat as PCB internal units (0.01 mil)
        return pcb_to_mm(int(numeric_value))
