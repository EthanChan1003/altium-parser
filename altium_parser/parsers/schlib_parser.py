"""Parser for Altium SchLib (schematic library) files."""

from __future__ import annotations

import logging
from pathlib import Path

from ..core.ole_reader import OleReader
from ..core.kv_parser import parse_kv_record
from ..core.binary_reader import BinaryReader
from ..core.units import sch_to_mm, delphi_color_to_rgb
from ..core.constants import (
    SchRecordType, PinElectricalType, PIN_ELECTRICAL_NAMES,
)
from ..core.exceptions import CorruptedDataError
from ..models.common import Point2D, Color
from ..models.schematic import (
    SchPin, SchPolyline, SchPolygon, SchRectangle, SchLine,
    SchArc, SchEllipse, SchRoundRectangle, SchBezier, SchText,
    SchParameter,
)
from ..models.schlib import SchLibrary, SchSymbol

logger = logging.getLogger(__name__)


class SchLibParser:
    """Parser for .SchLib files."""

    def __init__(self, file_path: str | Path):
        self._file_path = Path(file_path)

    def parse(self) -> SchLibrary:
        """Parse the SchLib file and return a SchLibrary model."""
        lib = SchLibrary(filename=self._file_path.name)

        with OleReader(self._file_path) as ole:
            logger.debug("OLE structure:\n%s", ole.dump_structure())

            # Get component names from the FileHeader stream
            component_names = self._get_component_names(ole)

            # Parse each component's storage
            for name in component_names:
                symbol = self._parse_symbol(ole, name)
                if symbol:
                    lib.symbols.append(symbol)

        logger.info("Parsed %s: %d symbols", self._file_path.name, len(lib.symbols))
        return lib

    def _get_component_names(self, ole: OleReader) -> list[str]:
        """Extract component names from the FileHeader stream."""
        data = ole.read_stream_safe("FileHeader")
        if not data:
            # Fallback: enumerate top-level storages
            return ole.get_root_storage_names()

        names = []
        records = self._parse_header_records(data)

        for kv in records:
            # The FileHeader contains component list records
            # Look for LIBREFERENCE or COMPONENTNAME
            name = kv.get("LIBREFERENCE", kv.get("COMPONENTNAME", ""))
            if name:
                names.append(name)

        if not names:
            # Fallback: enumerate top-level storages excluding FileHeader
            all_storages = ole.get_root_storage_names()
            names = [s for s in all_storages if s.upper() not in ("FILEHEADER", "STORAGE")]

        return names

    def _parse_header_records(self, data: bytes) -> list[dict[str, str]]:
        """Parse records from the FileHeader stream."""
        records: list[dict[str, str]] = []
        reader = BinaryReader(data)

        while not reader.is_eof():
            if reader.remaining() < 4:
                break
            try:
                payload_len = reader.read_uint16()
                _null = reader.read_uint8()
                record_type_byte = reader.read_uint8()

                if payload_len == 0:
                    continue
                if reader.remaining() < payload_len:
                    break
                if record_type_byte == 0:
                    payload = reader.read_bytes(payload_len)
                    kv = parse_kv_record(payload)
                    records.append(kv)
                else:
                    reader.skip(payload_len)
            except CorruptedDataError:
                break

        return records

    def _parse_symbol(self, ole: OleReader, name: str) -> SchSymbol | None:
        """Parse a single symbol from its storage."""
        # Altium truncates storage names to 31 chars and replaces / with _
        storage_name = name[:31].replace("/", "_")

        data_path = f"{storage_name}/Data"
        data = ole.read_stream_safe(data_path)
        if not data:
            # Try alternate path formats
            for alt in [name, name.replace(" ", "_")]:
                data = ole.read_stream_safe(f"{alt}/Data")
                if data:
                    break
            if not data:
                logger.warning("Cannot find data stream for symbol '%s'", name)
                return None

        symbol = SchSymbol(name=name)
        records = self._parse_header_records(data)

        for kv in records:
            record_type_str = kv.get("RECORD", "")
            if not record_type_str:
                continue
            try:
                record_type = int(record_type_str)
            except ValueError:
                continue

            self._dispatch_record(record_type, kv, symbol)

        # Try to get description from parameters
        for param in symbol.parameters:
            if param.name.upper() in ("DESCRIPTION", "COMPONENTDESCRIPTION"):
                symbol.description = param.value
                break

        return symbol

    def _dispatch_record(self, record_type: int, kv: dict[str, str], symbol: SchSymbol) -> None:
        """Route a record to the appropriate symbol list."""
        if record_type == SchRecordType.PIN:
            symbol.pins.append(self._build_pin(kv))
        elif record_type == SchRecordType.POLYLINE:
            symbol.polylines.append(self._build_polyline(kv))
        elif record_type == SchRecordType.POLYGON:
            symbol.polygons.append(self._build_polygon(kv))
        elif record_type == SchRecordType.RECTANGLE:
            symbol.rectangles.append(self._build_rectangle(kv))
        elif record_type == SchRecordType.LINE:
            symbol.lines.append(self._build_line(kv))
        elif record_type == SchRecordType.ARC:
            symbol.arcs.append(self._build_arc(kv))
        elif record_type == SchRecordType.ELLIPSE:
            symbol.ellipses.append(self._build_ellipse(kv))
        elif record_type == SchRecordType.ROUND_RECTANGLE:
            symbol.round_rectangles.append(self._build_round_rect(kv))
        elif record_type == SchRecordType.BEZIER:
            symbol.beziers.append(self._build_bezier(kv))
        elif record_type == SchRecordType.LABEL:
            symbol.texts.append(self._build_text(kv))
        elif record_type == SchRecordType.DESIGNATOR:
            symbol.designator_prefix = kv.get("TEXT", "")
        elif record_type == SchRecordType.PARAMETER:
            symbol.parameters.append(self._build_parameter(kv))
        elif record_type == SchRecordType.COMPONENT:
            symbol.part_count = max(1, self._get_int(kv, "PARTCOUNT", 1) - 1)
            if not symbol.description:
                symbol.description = kv.get("COMPONENTDESCRIPTION", "")

    # -- Primitive builders (reuse logic from SchDocParser) --

    def _build_pin(self, kv: dict[str, str]) -> SchPin:
        pin = SchPin()
        pin.name = kv.get("NAME", "")
        pin.number = kv.get("DESIGNATOR", "")
        elec_type = self._get_int(kv, "ELECTRICAL", 4)
        pin.electrical_type = PIN_ELECTRICAL_NAMES.get(elec_type, "passive")
        pin.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        conglomerate = self._get_int(kv, "PINCONGLOMERATE", 0)
        pin.orientation = conglomerate & 0x03
        pin.is_hidden = (conglomerate & 0x04) != 0
        pin.length_mm = sch_to_mm(self._get_int(kv, "PINLENGTH", 30))
        return pin

    def _build_polyline(self, kv: dict[str, str]) -> SchPolyline:
        poly = SchPolyline()
        poly.points = self._extract_points(kv)
        poly.color = self._parse_color(kv, "COLOR")
        poly.line_width = self._get_int(kv, "LINEWIDTH", 1)
        return poly

    def _build_polygon(self, kv: dict[str, str]) -> SchPolygon:
        poly = SchPolygon()
        poly.points = self._extract_points(kv)
        poly.fill_color = self._parse_color(kv, "AREACOLOR")
        poly.border_color = self._parse_color(kv, "COLOR")
        return poly

    def _build_rectangle(self, kv: dict[str, str]) -> SchRectangle:
        rect = SchRectangle()
        rect.corner1 = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        rect.corner2 = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "CORNER.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "CORNER.Y", 0)),
        )
        rect.fill_color = self._parse_color(kv, "AREACOLOR")
        rect.border_color = self._parse_color(kv, "COLOR")
        rect.is_solid = kv.get("ISSOLID", "F") == "T"
        return rect

    def _build_line(self, kv: dict[str, str]) -> SchLine:
        line = SchLine()
        line.start = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        line.end = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "CORNER.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "CORNER.Y", 0)),
        )
        line.color = self._parse_color(kv, "COLOR")
        return line

    def _build_arc(self, kv: dict[str, str]) -> SchArc:
        arc = SchArc()
        arc.center = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        arc.radius_mm = sch_to_mm(self._get_int(kv, "RADIUS", 0))
        arc.start_angle = self._get_float(kv, "STARTANGLE", 0.0)
        arc.end_angle = self._get_float(kv, "ENDANGLE", 360.0)
        arc.color = self._parse_color(kv, "COLOR")
        return arc

    def _build_ellipse(self, kv: dict[str, str]) -> SchEllipse:
        ell = SchEllipse()
        ell.center = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        ell.radius_x_mm = sch_to_mm(self._get_int(kv, "RADIUS", 0))
        ell.radius_y_mm = sch_to_mm(self._get_int(kv, "SECONDARYRADIUS", 0))
        ell.is_solid = kv.get("ISSOLID", "F") == "T"
        return ell

    def _build_round_rect(self, kv: dict[str, str]) -> SchRoundRectangle:
        rr = SchRoundRectangle()
        rr.corner1 = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        rr.corner2 = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "CORNER.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "CORNER.Y", 0)),
        )
        rr.corner_radius_mm = sch_to_mm(self._get_int(kv, "CORNERXRADIUS", 0))
        rr.is_solid = kv.get("ISSOLID", "F") == "T"
        return rr

    def _build_bezier(self, kv: dict[str, str]) -> SchBezier:
        bez = SchBezier()
        bez.points = self._extract_points(kv)
        bez.color = self._parse_color(kv, "COLOR")
        return bez

    def _build_text(self, kv: dict[str, str]) -> SchText:
        txt = SchText()
        txt.content = kv.get("TEXT", "")
        txt.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        txt.color = self._parse_color(kv, "COLOR")
        return txt

    def _build_parameter(self, kv: dict[str, str]) -> SchParameter:
        param = SchParameter()
        param.name = kv.get("NAME", "")
        param.value = kv.get("TEXT", "")
        param.is_hidden = kv.get("ISHIDDEN", "F") == "T"
        return param

    # -- Helpers --

    def _extract_points(self, kv: dict[str, str]) -> list[Point2D]:
        count = self._get_int(kv, "LOCATIONCOUNT", 0)
        points = []
        for i in range(1, count + 1):
            x = self._get_int(kv, f"X{i}", 0)
            y = self._get_int(kv, f"Y{i}", 0)
            points.append(Point2D(x_mm=sch_to_mm(x), y_mm=sch_to_mm(y)))
        return points

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

    @staticmethod
    def _parse_color(kv: dict[str, str], key: str) -> Color:
        val = kv.get(key, "")
        if not val:
            return Color()
        try:
            color_int = int(val)
            r, g, b = delphi_color_to_rgb(color_int)
            return Color(r=r, g=g, b=b)
        except (ValueError, TypeError):
            return Color()
