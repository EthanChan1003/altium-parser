"""Parser for Altium PcbLib (PCB footprint library) files."""

from __future__ import annotations

import logging
from pathlib import Path

from ..core.ole_reader import OleReader
from ..core.kv_parser import parse_kv_record
from ..core.binary_reader import BinaryReader
from ..core.units import pcb_to_mm
from ..core.constants import layer_id_to_name, PAD_SHAPE_NAMES
from ..core.exceptions import CorruptedDataError
from ..models.common import Point2D
from ..models.pcb import PcbPad, PcbTrack, PcbArc, PcbText, PcbRegion
from ..models.pcblib import PcbFootprintLibrary, PcbFootprint

logger = logging.getLogger(__name__)


class PcbLibParser:
    """Parser for .PcbLib files."""

    def __init__(self, file_path: str | Path):
        self._file_path = Path(file_path)

    def parse(self) -> PcbFootprintLibrary:
        """Parse the PcbLib file and return a PcbFootprintLibrary model."""
        lib = PcbFootprintLibrary(filename=self._file_path.name)

        with OleReader(self._file_path) as ole:
            logger.debug("OLE structure:\n%s", ole.dump_structure())

            # Get footprint names from Library/ComponentParamsTOC
            footprint_names = self._get_footprint_names(ole)

            # Parse each footprint storage
            for name in footprint_names:
                fp = self._parse_footprint(ole, name)
                if fp:
                    lib.footprints.append(fp)

        logger.info("Parsed %s: %d footprints", self._file_path.name, len(lib.footprints))
        return lib

    def _get_footprint_names(self, ole: OleReader) -> list[str]:
        """Extract footprint names from the Library."""
        names = []

        # Try Library/ComponentParamsTOC/Data
        toc_data = ole.read_stream_safe("Library/ComponentParamsTOC/Data")
        if toc_data:
            reader = BinaryReader(toc_data)
            while not reader.is_eof() and reader.remaining() >= 4:
                try:
                    record_len = reader.read_uint32()
                    if record_len == 0 or record_len > reader.remaining():
                        break
                    record_data = reader.read_bytes(record_len)
                    kv = parse_kv_record(record_data)
                    name = kv.get("PATTERN", kv.get("NAME", ""))
                    if name:
                        names.append(name)
                except CorruptedDataError:
                    break

        if not names:
            # Fallback: enumerate top-level storages
            all_storages = ole.get_root_storage_names()
            names = [s for s in all_storages
                     if s.upper() not in ("LIBRARY", "FILEHEADER", "FILEVERSIONINFO")]

        return names

    def _parse_footprint(self, ole: OleReader, name: str) -> PcbFootprint | None:
        """Parse a single footprint from its storage."""
        storage_name = name[:31].replace("/", "_")
        fp = PcbFootprint(name=name)

        # Read parameters
        params_data = ole.read_stream_safe(f"{storage_name}/Parameters")
        if params_data:
            try:
                kv = parse_kv_record(params_data)
                fp.description = kv.get("DESCRIPTION", "")
                fp.height_mm = pcb_to_mm(self._get_int(kv, "HEIGHT", 0))
                fp.parameters = {k: v for k, v in kv.items()}
            except Exception:
                pass

        # Read primitive data
        data = ole.read_stream_safe(f"{storage_name}/Data")
        if not data:
            # Try alternate paths
            for alt in [name, name.replace(" ", "_")]:
                data = ole.read_stream_safe(f"{alt}/Data")
                if data:
                    storage_name = alt
                    break
            if not data:
                logger.warning("Cannot find data stream for footprint '%s'", name)
                return fp

        # Read WideStrings for text content
        wide_strings: dict[int, str] = {}
        ws_data = ole.read_stream_safe(f"{storage_name}/WideStrings")
        if ws_data:
            wide_strings = self._parse_wide_strings(ws_data)

        # Parse the data stream
        self._parse_primitives(data, fp, wide_strings)

        return fp

    def _parse_primitives(self, data: bytes, fp: PcbFootprint,
                          wide_strings: dict[int, str]) -> None:
        """Parse PCB primitives from footprint data stream."""
        reader = BinaryReader(data)

        # First read the footprint name block (Pascal string with 4-byte length)
        if reader.remaining() >= 4:
            try:
                name_len = reader.read_uint32()
                if name_len > 0 and name_len <= reader.remaining():
                    reader.skip(name_len)  # Skip the name string
            except CorruptedDataError:
                return

        text_idx = 0
        while not reader.is_eof() and reader.remaining() >= 5:
            try:
                # Each primitive: 1 byte type ID, then 4-byte length, then data
                prim_type = reader.read_uint8()
                prim_len = reader.read_uint32()

                if prim_len == 0 or prim_len > reader.remaining():
                    break

                prim_data = reader.read_bytes(prim_len)
                self._dispatch_primitive(prim_type, prim_data, fp, wide_strings, text_idx)

                if prim_type == 5:  # Text type
                    text_idx += 1

            except CorruptedDataError:
                break

    def _dispatch_primitive(self, prim_type: int, data: bytes, fp: PcbFootprint,
                            wide_strings: dict[int, str], text_idx: int) -> None:
        """Dispatch a primitive record to the appropriate builder."""
        try:
            if prim_type == 1:  # Arc
                arc = self._build_arc(data)
                if arc:
                    fp.arcs.append(arc)
            elif prim_type == 2:  # Pad
                pad = self._build_pad(data)
                if pad:
                    fp.pads.append(pad)
            elif prim_type == 4:  # Track
                track = self._build_track(data)
                if track:
                    fp.tracks.append(track)
            elif prim_type == 5:  # Text
                text = self._build_text(data, wide_strings, text_idx)
                if text:
                    fp.texts.append(text)
            elif prim_type == 6:  # Fill
                pass  # Fill in footprint is less common
            elif prim_type == 11:  # Region
                region = self._build_region(data)
                if region:
                    fp.regions.append(region)
        except Exception as e:
            logger.debug("Error parsing primitive type %d: %s", prim_type, e)

    def _build_track(self, data: bytes) -> PcbTrack | None:
        """Build a track from binary data."""
        if len(data) < 37:
            return None
        reader = BinaryReader(data)
        track = PcbTrack()
        layer_id = reader.read_uint8()
        reader.skip(5)  # flags and padding
        net_id = reader.read_uint16()
        reader.skip(2)  # polygon index
        component_id = reader.read_uint16()
        reader.skip(4)  # reserved

        x1 = reader.read_int32()
        y1 = reader.read_int32()
        x2 = reader.read_int32()
        y2 = reader.read_int32()
        width = reader.read_int32()

        track.start = Point2D(x_mm=pcb_to_mm(x1), y_mm=pcb_to_mm(y1))
        track.end = Point2D(x_mm=pcb_to_mm(x2), y_mm=pcb_to_mm(y2))
        track.width_mm = pcb_to_mm(width)
        track.layer_id = layer_id
        track.layer = layer_id_to_name(layer_id)
        return track

    def _build_arc(self, data: bytes) -> PcbArc | None:
        """Build an arc from binary data."""
        if len(data) < 45:
            return None
        reader = BinaryReader(data)
        arc = PcbArc()
        layer_id = reader.read_uint8()
        reader.skip(5)
        net_id = reader.read_uint16()
        reader.skip(2)
        component_id = reader.read_uint16()
        reader.skip(4)

        cx = reader.read_int32()
        cy = reader.read_int32()
        radius = reader.read_int32()
        start_angle = reader.read_float64()
        end_angle = reader.read_float64()
        width = reader.read_int32()

        arc.center = Point2D(x_mm=pcb_to_mm(cx), y_mm=pcb_to_mm(cy))
        arc.radius_mm = pcb_to_mm(radius)
        arc.start_angle = start_angle
        arc.end_angle = end_angle
        arc.width_mm = pcb_to_mm(width)
        arc.layer_id = layer_id
        arc.layer = layer_id_to_name(layer_id)
        return arc

    def _build_pad(self, data: bytes) -> PcbPad | None:
        """Build a pad from binary data."""
        if len(data) < 50:
            return None
        reader = BinaryReader(data)
        pad = PcbPad()

        layer_id = reader.read_uint8()
        reader.skip(5)  # flags
        net_id = reader.read_uint16()
        reader.skip(2)
        component_id = reader.read_uint16()
        reader.skip(4)

        x = reader.read_int32()
        y = reader.read_int32()
        top_x_size = reader.read_int32()
        top_y_size = reader.read_int32()

        # Mid and bot sizes may follow
        mid_x_size = reader.read_int32() if reader.remaining() >= 4 else top_x_size
        mid_y_size = reader.read_int32() if reader.remaining() >= 4 else top_y_size
        bot_x_size = reader.read_int32() if reader.remaining() >= 4 else top_x_size
        bot_y_size = reader.read_int32() if reader.remaining() >= 4 else top_y_size
        hole_size = reader.read_int32() if reader.remaining() >= 4 else 0
        shape = reader.read_uint8() if reader.remaining() >= 1 else 1

        pad.position = Point2D(x_mm=pcb_to_mm(x), y_mm=pcb_to_mm(y))
        pad.top_size = Point2D(x_mm=pcb_to_mm(top_x_size), y_mm=pcb_to_mm(top_y_size))
        pad.mid_size = Point2D(x_mm=pcb_to_mm(mid_x_size), y_mm=pcb_to_mm(mid_y_size))
        pad.bottom_size = Point2D(x_mm=pcb_to_mm(bot_x_size), y_mm=pcb_to_mm(bot_y_size))
        pad.hole_size_mm = pcb_to_mm(hole_size)
        pad.shape = PAD_SHAPE_NAMES.get(shape, f"shape_{shape}")
        pad.layer_id = layer_id
        pad.layer = layer_id_to_name(layer_id)
        pad.pad_type = "through_hole" if pad.hole_size_mm > 0 else "smd"

        # Try to read pad designator
        if reader.remaining() >= 1:
            try:
                name_len = reader.read_uint8()
                if 0 < name_len <= reader.remaining():
                    pad.designator = reader.read_bytes(name_len).decode("latin-1", errors="replace")
            except CorruptedDataError:
                pass

        return pad

    def _build_text(self, data: bytes, wide_strings: dict[int, str],
                    text_idx: int) -> PcbText | None:
        """Build a text from binary data."""
        if len(data) < 25:
            return None
        reader = BinaryReader(data)
        text = PcbText()

        layer_id = reader.read_uint8()
        reader.skip(5)
        reader.skip(2)  # net
        reader.skip(2)  # polygon
        component_id = reader.read_uint16()
        reader.skip(4)

        x = reader.read_int32()
        y = reader.read_int32()
        height = reader.read_int32() if reader.remaining() >= 4 else 100000

        text.position = Point2D(x_mm=pcb_to_mm(x), y_mm=pcb_to_mm(y))
        text.height_mm = pcb_to_mm(height)
        text.layer_id = layer_id
        text.layer = layer_id_to_name(layer_id)

        # Prefer wide string content
        text.content = wide_strings.get(text_idx, "")

        # Try inline text if no wide string
        if not text.content and reader.remaining() >= 1:
            try:
                text.content = reader.read_pascal_string()
            except CorruptedDataError:
                pass

        return text

    def _build_region(self, data: bytes) -> PcbRegion | None:
        """Build a region from binary data."""
        if len(data) < 14:
            return None
        reader = BinaryReader(data)
        region = PcbRegion()

        layer_id = reader.read_uint8()
        reader.skip(5)
        net_id = reader.read_uint16()
        reader.skip(4)

        region.layer_id = layer_id
        region.layer = layer_id_to_name(layer_id)

        # Read vertex count and vertices
        if reader.remaining() >= 4:
            vertex_count = reader.read_uint32()
            for _ in range(min(vertex_count, 10000)):
                if reader.remaining() < 8:
                    break
                x = reader.read_int32()
                y = reader.read_int32()
                region.vertices.append(Point2D(x_mm=pcb_to_mm(x), y_mm=pcb_to_mm(y)))

        return region

    def _parse_wide_strings(self, data: bytes) -> dict[int, str]:
        """Parse WideStrings data into index → string map."""
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
