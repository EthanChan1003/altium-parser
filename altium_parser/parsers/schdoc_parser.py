"""Parser for Altium SchDoc (schematic document) files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..core.ole_reader import OleReader
from ..core.kv_parser import parse_kv_record
from ..core.binary_reader import BinaryReader
from ..core.units import sch_to_mm, delphi_color_to_rgb
from ..core.constants import (
    SchRecordType, PinElectricalType, PIN_ELECTRICAL_NAMES,
    PowerPortStyle, POWER_PORT_STYLE_NAMES,
    SheetStyle, SHEET_SIZE_MM, SHEET_STYLE_NAMES,
)
from ..core.exceptions import CorruptedDataError
from ..models.common import Point2D, Color
from ..models.schematic import (
    SchDocument, SchSheet, SchTitleBlock, SchComponent, SchPin,
    SchWire, SchBus, SchBusEntry, SchNetLabel, SchPowerPort, SchPort,
    SchJunction, SchNoErc, SchPolyline, SchPolygon, SchRectangle,
    SchLine, SchArc, SchEllipse, SchRoundRectangle, SchBezier,
    SchText, SchLabel, SchImage, SchSheetSymbol, SchSheetEntry,
    SchParameter,
)

logger = logging.getLogger(__name__)


class SchDocParser:
    """Parser for .SchDoc files."""

    def __init__(self, file_path: str | Path):
        self._file_path = Path(file_path)

    def parse(self) -> SchDocument:
        """Parse the SchDoc file and return a SchDocument model."""
        doc = SchDocument(filename=self._file_path.name)

        with OleReader(self._file_path) as ole:
            logger.debug("OLE structure:\n%s", ole.dump_structure())

            # Read the main FileHeader stream
            data = ole.read_stream("FileHeader")
            records = self._parse_records(data)

        doc.raw_record_count = len(records)

        # Build flat list of parsed objects
        parsed_objects: list[tuple[int, Any]] = []  # (record_index, object)
        component_indices: list[int] = []  # indices into parsed_objects for components

        for idx, kv in enumerate(records):
            record_type_str = kv.get("RECORD", "")
            if not record_type_str:
                continue
            try:
                record_type = int(record_type_str)
            except ValueError:
                doc.unknown_record_count += 1
                continue

            obj = self._dispatch_record(record_type, kv, idx)
            if obj is not None:
                parsed_objects.append((idx, obj))
                if isinstance(obj, SchComponent):
                    component_indices.append(len(parsed_objects) - 1)
            else:
                doc.unknown_record_count += 1

        # Build owner index mapping: record_index -> list of child objects
        components_by_index: dict[int, SchComponent] = {}
        sheet_symbols_by_index: dict[int, SchSheetSymbol] = {}

        for _, obj in parsed_objects:
            if isinstance(obj, SchComponent):
                components_by_index[obj.owner_index] = obj
            elif isinstance(obj, SchSheetSymbol):
                sheet_symbols_by_index[obj.owner_index] = obj

        # Assign children to parents via owner_index
        for _, obj in parsed_objects:
            owner = getattr(obj, "owner_index", -1)
            if owner < 0:
                continue

            if isinstance(obj, SchPin) and owner in components_by_index:
                components_by_index[owner].pins.append(obj)
            elif isinstance(obj, SchParameter) and owner in components_by_index:
                components_by_index[owner].parameters.append(obj)
            elif isinstance(obj, SchSheetEntry) and owner in sheet_symbols_by_index:
                sheet_symbols_by_index[owner].entries.append(obj)
            elif owner in components_by_index and isinstance(obj, (
                SchPolyline, SchPolygon, SchRectangle, SchLine, SchArc,
                SchEllipse, SchRoundRectangle, SchBezier, SchText, SchLabel,
            )):
                components_by_index[owner].graphic_primitives.append(obj)

        # Populate document
        for _, obj in parsed_objects:
            if isinstance(obj, SchSheet):
                doc.sheet = obj
            elif isinstance(obj, SchComponent):
                doc.components.append(obj)
            elif isinstance(obj, SchWire):
                doc.wires.append(obj)
            elif isinstance(obj, SchBus):
                doc.buses.append(obj)
            elif isinstance(obj, SchBusEntry):
                doc.bus_entries.append(obj)
            elif isinstance(obj, SchNetLabel):
                doc.net_labels.append(obj)
            elif isinstance(obj, SchPowerPort):
                doc.power_ports.append(obj)
            elif isinstance(obj, SchPort):
                doc.ports.append(obj)
            elif isinstance(obj, SchJunction):
                doc.junctions.append(obj)
            elif isinstance(obj, SchNoErc):
                doc.no_ercs.append(obj)
            elif isinstance(obj, SchSheetSymbol):
                doc.sheet_symbols.append(obj)
            elif isinstance(obj, SchImage):
                doc.images.append(obj)
            # Free-standing graphics (not owned by a component)
            elif isinstance(obj, SchPolyline) and obj.owner_index not in components_by_index:
                doc.polylines.append(obj)
            elif isinstance(obj, SchPolygon) and obj.owner_index not in components_by_index:
                doc.polygons.append(obj)
            elif isinstance(obj, SchRectangle) and obj.owner_index not in components_by_index:
                doc.rectangles.append(obj)
            elif isinstance(obj, SchLine) and obj.owner_index not in components_by_index:
                doc.lines.append(obj)
            elif isinstance(obj, SchArc) and obj.owner_index not in components_by_index:
                doc.arcs.append(obj)
            elif isinstance(obj, SchEllipse) and obj.owner_index not in components_by_index:
                doc.ellipses.append(obj)
            elif isinstance(obj, SchRoundRectangle) and obj.owner_index not in components_by_index:
                doc.round_rectangles.append(obj)
            elif isinstance(obj, SchBezier) and obj.owner_index not in components_by_index:
                doc.beziers.append(obj)
            elif isinstance(obj, SchText) and obj.owner_index not in components_by_index:
                doc.texts.append(obj)
            elif isinstance(obj, SchLabel) and obj.owner_index not in components_by_index:
                doc.labels.append(obj)

        # Extract designators from parameters
        for comp in doc.components:
            for param in comp.parameters:
                if param.name.upper() == "DESIGNATOR" and not comp.refdes:
                    comp.refdes = param.value
                elif param.name.upper() == "COMMENT" and not comp.description:
                    comp.description = param.value

        logger.info(
            "Parsed %s: %d components, %d wires, %d net labels, %d pins total",
            self._file_path.name,
            len(doc.components),
            len(doc.wires),
            len(doc.net_labels),
            sum(len(c.pins) for c in doc.components),
        )
        return doc

    def _parse_records(self, data: bytes) -> list[dict[str, str]]:
        """Parse all records from the FileHeader stream."""
        records: list[dict[str, str]] = []
        reader = BinaryReader(data)

        while not reader.is_eof():
            if reader.remaining() < 4:
                break
            try:
                payload_len = reader.read_uint16()
                _null = reader.read_uint8()  # null padding byte
                record_type_byte = reader.read_uint8()

                if payload_len == 0:
                    continue

                if reader.remaining() < payload_len:
                    logger.warning(
                        "Truncated record at offset %d: expected %d bytes, have %d",
                        reader.tell(), payload_len, reader.remaining()
                    )
                    break

                if record_type_byte == 0:
                    # Property-list record
                    payload = reader.read_bytes(payload_len)
                    kv = parse_kv_record(payload)
                    records.append(kv)
                elif record_type_byte == 1:
                    # Storage/binary record (e.g., embedded image)
                    reader.skip(payload_len)
                else:
                    reader.skip(payload_len)

            except CorruptedDataError as e:
                logger.warning("Corrupted data at offset %d: %s", reader.tell(), e)
                break

        return records

    def _dispatch_record(self, record_type: int, kv: dict[str, str], index: int) -> Any | None:
        """Dispatch a record to the appropriate builder method."""
        handlers = {
            SchRecordType.SHEET: self._build_sheet,
            SchRecordType.COMPONENT: self._build_component,
            SchRecordType.PIN: self._build_pin,
            SchRecordType.WIRE: self._build_wire,
            SchRecordType.BUS: self._build_bus,
            SchRecordType.BUS_ENTRY: self._build_bus_entry,
            SchRecordType.NET_LABEL: self._build_net_label,
            SchRecordType.POWER_PORT: self._build_power_port,
            SchRecordType.PORT: self._build_port,
            SchRecordType.JUNCTION: self._build_junction,
            SchRecordType.NO_ERC: self._build_no_erc,
            SchRecordType.POLYLINE: self._build_polyline,
            SchRecordType.POLYGON: self._build_polygon,
            SchRecordType.RECTANGLE: self._build_rectangle,
            SchRecordType.LINE: self._build_line,
            SchRecordType.ARC: self._build_arc,
            SchRecordType.ELLIPSE: self._build_ellipse,
            SchRecordType.ROUND_RECTANGLE: self._build_round_rectangle,
            SchRecordType.BEZIER: self._build_bezier,
            SchRecordType.LABEL: self._build_label,
            SchRecordType.DESIGNATOR: self._build_designator,
            SchRecordType.PARAMETER: self._build_parameter,
            SchRecordType.SHEET_SYMBOL: self._build_sheet_symbol,
            SchRecordType.SHEET_ENTRY: self._build_sheet_entry,
            SchRecordType.IMAGE: self._build_image,
            SchRecordType.TEXT_FRAME: self._build_text_frame,
        }

        handler = handlers.get(record_type)
        if handler:
            try:
                return handler(kv, index)
            except Exception as e:
                logger.warning("Error building record type %d at index %d: %s", record_type, index, e)
                return None

        # Known but unhandled types
        if record_type in (
            SchRecordType.HEADER, SchRecordType.SHEET_NAME, SchRecordType.SHEET_FILE_NAME,
            SchRecordType.TEMPLATE, SchRecordType.WARNING_SIGN, SchRecordType.IEEE_SYMBOL,
            SchRecordType.PIE, SchRecordType.ELLIPTICAL_ARC,
            SchRecordType.IMPLEMENTATION_LIST, SchRecordType.IMPLEMENTATION,
            SchRecordType.RECORD_46, SchRecordType.RECORD_47, SchRecordType.RECORD_48,
        ):
            return None  # Silently skip

        logger.debug("Unhandled record type %d at index %d", record_type, index)
        return None

    # -- Record builders --

    def _build_sheet(self, kv: dict[str, str], index: int) -> SchSheet:
        sheet = SchSheet()
        style_int = self._get_int(kv, "SHEETSTYLE", 0)
        try:
            style = SheetStyle(style_int)
            sheet.size = SHEET_STYLE_NAMES.get(style, f"Custom({style_int})")
            w, h = SHEET_SIZE_MM.get(style, (297.0, 210.0))
            sheet.width_mm = w
            sheet.height_mm = h
        except ValueError:
            # Custom sheet size
            sheet.size = f"Custom({style_int})"
            sheet.width_mm = sch_to_mm(self._get_int(kv, "CUSTOMX", 1170))
            sheet.height_mm = sch_to_mm(self._get_int(kv, "CUSTOMY", 827))

        sheet.grid_size_mm = sch_to_mm(self._get_int(kv, "VISIBLEGRIDSIZE", 10))
        sheet.font_count = self._get_int(kv, "FONTIDCOUNT", 0)

        # Title block
        tb = SchTitleBlock()
        tb.title = kv.get("TITLE", "")
        tb.date = kv.get("DATE", "")
        tb.revision = kv.get("REVISION", "")
        tb.company = kv.get("COMPANYNAME", "")
        tb.author = kv.get("AUTHOR", "")
        tb.sheet_number = kv.get("SHEETNUMBER", "")
        tb.sheet_total = kv.get("SHEETTOTAL", "")
        sheet.title_block = tb

        return sheet

    def _build_component(self, kv: dict[str, str], index: int) -> SchComponent:
        comp = SchComponent()
        comp.owner_index = index
        comp.lib_reference = kv.get("LIBREFERENCE", "")
        comp.description = kv.get("COMPONENTDESCRIPTION", "")
        comp.source_library = kv.get("SOURCELIBRARY", kv.get("SOURCELIBRARYNAME", ""))
        comp.unique_id = kv.get("UNIQUEID", "")
        comp.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        comp.rotation = self._get_int(kv, "ORIENTATION", 0)
        comp.is_mirrored = kv.get("ISMIRRORED", "F") == "T"
        comp.part_count = max(1, self._get_int(kv, "PARTCOUNT", 1) - 1)
        comp.current_part_id = self._get_int(kv, "CURRENTPARTID", 1)

        # Designator may be set directly or via a child DESIGNATOR record
        comp.refdes = kv.get("DESIGNATOR", "")

        return comp

    def _build_pin(self, kv: dict[str, str], index: int) -> SchPin:
        pin = SchPin()
        pin.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        pin.owner_part_id = self._get_int(kv, "OWNERPARTID", 0)
        pin.name = kv.get("NAME", "")
        pin.number = kv.get("DESIGNATOR", "")

        elec_type = self._get_int(kv, "ELECTRICAL", PinElectricalType.PASSIVE)
        pin.electrical_type = PIN_ELECTRICAL_NAMES.get(elec_type, "passive")

        pin.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )

        # Orientation from PINCONGLOMERATE
        conglomerate = self._get_int(kv, "PINCONGLOMERATE", 0)
        pin.orientation = conglomerate & 0x03
        pin.is_hidden = (conglomerate & 0x04) != 0

        pin.length_mm = sch_to_mm(self._get_int(kv, "PINLENGTH", 30))

        return pin

    def _build_wire(self, kv: dict[str, str], index: int) -> SchWire:
        wire = SchWire()
        wire.points = self._extract_coordinate_points(kv)
        return wire

    def _build_bus(self, kv: dict[str, str], index: int) -> SchBus:
        bus = SchBus()
        bus.points = self._extract_coordinate_points(kv)
        return bus

    def _build_bus_entry(self, kv: dict[str, str], index: int) -> SchBusEntry:
        entry = SchBusEntry()
        entry.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        entry.corner = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "CORNER.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "CORNER.Y", 0)),
        )
        return entry

    def _build_net_label(self, kv: dict[str, str], index: int) -> SchNetLabel:
        label = SchNetLabel()
        label.name = kv.get("TEXT", "")
        label.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        label.orientation = self._get_int(kv, "ORIENTATION", 0)
        label.color = self._parse_color(kv, "COLOR")
        return label

    def _build_power_port(self, kv: dict[str, str], index: int) -> SchPowerPort:
        port = SchPowerPort()
        port.name = kv.get("TEXT", "")
        port.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        port.orientation = self._get_int(kv, "ORIENTATION", 0)

        style_int = self._get_int(kv, "STYLE", 0)
        port.style = POWER_PORT_STYLE_NAMES.get(style_int, f"style_{style_int}")

        port.is_cross_sheet = kv.get("ISCROSSSHEETCONNECTOR", "F") == "T"
        port.color = self._parse_color(kv, "COLOR")
        return port

    def _build_port(self, kv: dict[str, str], index: int) -> SchPort:
        port = SchPort()
        port.name = kv.get("NAME", "")
        port.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        port.width_mm = sch_to_mm(self._get_int(kv, "WIDTH", 0))
        port.height_mm = sch_to_mm(self._get_int(kv, "HEIGHT", 0))
        io_type = self._get_int(kv, "IOTYPE", 0)
        io_names = {0: "unspecified", 1: "output", 2: "input", 3: "bidirectional"}
        port.io_type = io_names.get(io_type, "unspecified")
        return port

    def _build_junction(self, kv: dict[str, str], index: int) -> SchJunction:
        junc = SchJunction()
        junc.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        junc.color = self._parse_color(kv, "COLOR")
        return junc

    def _build_no_erc(self, kv: dict[str, str], index: int) -> SchNoErc:
        marker = SchNoErc()
        marker.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        return marker

    def _build_polyline(self, kv: dict[str, str], index: int) -> SchPolyline:
        poly = SchPolyline()
        poly.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        poly.points = self._extract_coordinate_points(kv)
        poly.color = self._parse_color(kv, "COLOR")
        poly.line_width = self._get_int(kv, "LINEWIDTH", 1)
        return poly

    def _build_polygon(self, kv: dict[str, str], index: int) -> SchPolygon:
        poly = SchPolygon()
        poly.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        poly.points = self._extract_coordinate_points(kv)
        poly.fill_color = self._parse_color(kv, "AREACOLOR")
        poly.border_color = self._parse_color(kv, "COLOR")
        poly.line_width = self._get_int(kv, "LINEWIDTH", 1)
        return poly

    def _build_rectangle(self, kv: dict[str, str], index: int) -> SchRectangle:
        rect = SchRectangle()
        rect.owner_index = self._get_int(kv, "OWNERINDEX", -1)
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
        rect.line_width = self._get_int(kv, "LINEWIDTH", 1)
        rect.is_solid = kv.get("ISSOLID", "F") == "T"
        return rect

    def _build_line(self, kv: dict[str, str], index: int) -> SchLine:
        line = SchLine()
        line.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        line.start = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        line.end = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "CORNER.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "CORNER.Y", 0)),
        )
        line.color = self._parse_color(kv, "COLOR")
        line.line_width = self._get_int(kv, "LINEWIDTH", 1)
        return line

    def _build_arc(self, kv: dict[str, str], index: int) -> SchArc:
        arc = SchArc()
        arc.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        arc.center = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        arc.radius_mm = sch_to_mm(self._get_int(kv, "RADIUS", 0))
        arc.start_angle = self._get_float(kv, "STARTANGLE", 0.0)
        arc.end_angle = self._get_float(kv, "ENDANGLE", 360.0)
        arc.line_width = self._get_int(kv, "LINEWIDTH", 1)
        arc.color = self._parse_color(kv, "COLOR")
        return arc

    def _build_ellipse(self, kv: dict[str, str], index: int) -> SchEllipse:
        ell = SchEllipse()
        ell.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        ell.center = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        ell.radius_x_mm = sch_to_mm(self._get_int(kv, "RADIUS", 0))
        ell.radius_y_mm = sch_to_mm(self._get_int(kv, "SECONDARYRADIUS", 0))
        ell.fill_color = self._parse_color(kv, "AREACOLOR")
        ell.border_color = self._parse_color(kv, "COLOR")
        ell.is_solid = kv.get("ISSOLID", "F") == "T"
        return ell

    def _build_round_rectangle(self, kv: dict[str, str], index: int) -> SchRoundRectangle:
        rr = SchRoundRectangle()
        rr.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        rr.corner1 = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        rr.corner2 = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "CORNER.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "CORNER.Y", 0)),
        )
        rr.corner_radius_mm = sch_to_mm(self._get_int(kv, "CORNERXRADIUS", 0))
        rr.fill_color = self._parse_color(kv, "AREACOLOR")
        rr.border_color = self._parse_color(kv, "COLOR")
        rr.is_solid = kv.get("ISSOLID", "F") == "T"
        return rr

    def _build_bezier(self, kv: dict[str, str], index: int) -> SchBezier:
        bez = SchBezier()
        bez.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        bez.points = self._extract_coordinate_points(kv)
        bez.color = self._parse_color(kv, "COLOR")
        bez.line_width = self._get_int(kv, "LINEWIDTH", 1)
        return bez

    def _build_label(self, kv: dict[str, str], index: int) -> SchLabel:
        lbl = SchLabel()
        lbl.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        lbl.text = kv.get("TEXT", "")
        lbl.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        lbl.orientation = self._get_int(kv, "ORIENTATION", 0)
        lbl.color = self._parse_color(kv, "COLOR")
        return lbl

    def _build_text_frame(self, kv: dict[str, str], index: int) -> SchText:
        txt = SchText()
        txt.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        txt.content = kv.get("TEXT", "")
        txt.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        txt.rotation = self._get_int(kv, "ORIENTATION", 0)
        txt.color = self._parse_color(kv, "COLOR")
        return txt

    def _build_designator(self, kv: dict[str, str], index: int) -> SchParameter:
        param = SchParameter()
        param.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        param.name = "Designator"
        param.value = kv.get("TEXT", "")
        param.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        param.is_hidden = kv.get("ISHIDDEN", "F") == "T"
        return param

    def _build_parameter(self, kv: dict[str, str], index: int) -> SchParameter:
        param = SchParameter()
        param.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        param.name = kv.get("NAME", "")
        param.value = kv.get("TEXT", "")
        param.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        param.is_hidden = kv.get("ISHIDDEN", "F") == "T"
        return param

    def _build_sheet_symbol(self, kv: dict[str, str], index: int) -> SchSheetSymbol:
        ss = SchSheetSymbol()
        ss.owner_index = index
        ss.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        ss.width_mm = sch_to_mm(self._get_int(kv, "XSIZE", 0))
        ss.height_mm = sch_to_mm(self._get_int(kv, "YSIZE", 0))
        ss.sheet_name = kv.get("SHEETNAME", "")
        ss.file_name = kv.get("FILENAME", "")
        return ss

    def _build_sheet_entry(self, kv: dict[str, str], index: int) -> SchSheetEntry:
        se = SchSheetEntry()
        se.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        se.name = kv.get("NAME", "")
        io_type = self._get_int(kv, "IOTYPE", 0)
        io_names = {0: "unspecified", 1: "output", 2: "input", 3: "bidirectional"}
        se.io_type = io_names.get(io_type, "unspecified")
        se.side = self._get_int(kv, "SIDE", 0)
        se.position_offset_mm = sch_to_mm(self._get_int(kv, "DISTANCEFROMEDGE", 0))
        return se

    def _build_image(self, kv: dict[str, str], index: int) -> SchImage:
        img = SchImage()
        img.owner_index = self._get_int(kv, "OWNERINDEX", -1)
        img.filename = kv.get("FILENAME", "")
        img.position = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
        )
        img.corner = Point2D(
            x_mm=sch_to_mm(self._get_int(kv, "CORNER.X", 0)),
            y_mm=sch_to_mm(self._get_int(kv, "CORNER.Y", 0)),
        )
        img.is_embedded = kv.get("EMBEDIMAGE", "F") == "T"
        return img

    # -- Helpers --

    def _extract_coordinate_points(self, kv: dict[str, str]) -> list[Point2D]:
        """Extract a list of coordinate points from numbered X1/Y1, X2/Y2 keys."""
        count = self._get_int(kv, "LOCATIONCOUNT", 0)
        points = []
        if count > 0:
            for i in range(1, count + 1):
                x = self._get_int(kv, f"X{i}", 0)
                y = self._get_int(kv, f"Y{i}", 0)
                points.append(Point2D(x_mm=sch_to_mm(x), y_mm=sch_to_mm(y)))
        else:
            # Fallback: try LOCATION.X/Y for single-point records
            if "LOCATION.X" in kv:
                points.append(Point2D(
                    x_mm=sch_to_mm(self._get_int(kv, "LOCATION.X", 0)),
                    y_mm=sch_to_mm(self._get_int(kv, "LOCATION.Y", 0)),
                ))
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
