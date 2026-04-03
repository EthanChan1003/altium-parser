"""Tests for PcbDoc parser (using synthetic data)."""

from altium_parser.models.pcb import (
    PcbDocument, PcbComponent, PcbTrack, PcbPad, PcbVia, PcbNet,
    StackupLayer, BoardOutline, PcbText, PcbArc,
)
from altium_parser.models.common import Point2D, BoundingBox
from altium_parser.core.units import pcb_to_mm
from altium_parser.core.constants import layer_id_to_name


class TestPcbDocModels:
    """Test PcbDoc models and serialization."""

    def test_component_to_dict(self):
        comp = PcbComponent(
            designator="U1",
            footprint_name="LQFP-64",
            position=Point2D(x_mm=45.0, y_mm=35.0),
            rotation=90.0,
            layer="top",
        )
        d = comp.to_dict()
        assert d["designator"] == "U1"
        assert d["footprint_name"] == "LQFP-64"
        assert d["position"]["x_mm"] == 45.0
        assert d["rotation"] == 90.0
        assert d["layer"] == "top"

    def test_track_to_dict(self):
        track = PcbTrack(
            start=Point2D(x_mm=10.0, y_mm=10.0),
            end=Point2D(x_mm=20.0, y_mm=10.0),
            width_mm=0.254,
            layer="Top Layer",
            net="VCC",
        )
        d = track.to_dict()
        assert d["start"]["x_mm"] == 10.0
        assert d["end"]["x_mm"] == 20.0
        assert d["width_mm"] == 0.254
        assert d["net"] == "VCC"

    def test_pad_smd_to_dict(self):
        pad = PcbPad(
            designator="1",
            position=Point2D(x_mm=12.0, y_mm=12.0),
            top_size=Point2D(x_mm=0.6, y_mm=1.2),
            shape="rectangular",
            layer="Multi-Layer",
            net="PA0",
            pad_type="smd",
        )
        d = pad.to_dict()
        assert d["designator"] == "1"
        assert d["pad_type"] == "smd"
        assert "hole_shape" not in d  # SMD pad has no hole info

    def test_pad_through_hole_to_dict(self):
        pad = PcbPad(
            designator="1",
            position=Point2D(x_mm=12.0, y_mm=12.0),
            top_size=Point2D(x_mm=1.6, y_mm=1.6),
            mid_size=Point2D(x_mm=1.6, y_mm=1.6),
            bottom_size=Point2D(x_mm=1.6, y_mm=1.6),
            hole_size_mm=0.8,
            shape="round",
            pad_type="through_hole",
        )
        d = pad.to_dict()
        assert d["hole_size_mm"] == 0.8
        assert "mid_size" in d
        assert "bottom_size" in d
        assert d["hole_shape"] == "round"

    def test_via_to_dict(self):
        via = PcbVia(
            position=Point2D(x_mm=15.0, y_mm=15.0),
            diameter_mm=0.6,
            hole_mm=0.3,
            start_layer="Top Layer",
            end_layer="Bottom Layer",
            net="GND",
        )
        d = via.to_dict()
        assert d["diameter_mm"] == 0.6
        assert d["hole_mm"] == 0.3
        assert d["net"] == "GND"

    def test_document_to_dict(self):
        doc = PcbDocument(filename="test.PcbDoc")
        doc.nets = [PcbNet(id=1, name="GND"), PcbNet(id=2, name="VCC")]
        doc.components.append(PcbComponent(designator="U1"))
        doc.tracks.append(PcbTrack(width_mm=0.254))
        doc.pads.append(PcbPad(designator="1"))
        doc.vias.append(PcbVia(diameter_mm=0.6))

        d = doc.to_dict()
        assert d["statistics"]["component_count"] == 1
        assert d["statistics"]["track_count"] == 1
        assert d["statistics"]["pad_count"] == 1
        assert d["statistics"]["via_count"] == 1
        assert d["statistics"]["net_count"] == 2

    def test_stackup_layer(self):
        layer = StackupLayer(
            id=1,
            name="Top Layer",
            copper_thickness_mm=0.035,
            dielectric_constant=4.2,
            material="FR-4",
        )
        d = layer.to_dict()
        assert d["name"] == "Top Layer"
        assert d["copper_thickness_mm"] == 0.035
        assert d["material"] == "FR-4"

    def test_board_outline(self):
        outline = BoardOutline(
            vertices=[
                Point2D(0, 0), Point2D(90, 0),
                Point2D(90, 70), Point2D(0, 70),
            ],
            bounding_box=BoundingBox(0, 0, 90, 70),
        )
        d = outline.to_dict()
        assert len(d["vertices"]) == 4
        assert d["bounding_box"]["x2_mm"] == 90


class TestPcbCoordinateConversion:
    """Test PcbDoc coordinate conversions."""

    def test_pcb_coordinate_to_mm(self):
        # 1 inch = 10000000 internal units = 25.4 mm
        assert abs(pcb_to_mm(10000000) - 25.4) < 0.001

    def test_10mil_track_width(self):
        # 10 mil = 100000 units = 0.254 mm
        assert abs(pcb_to_mm(100000) - 0.254) < 0.001

    def test_0402_pad_size(self):
        # 20 mil = 200000 units = 0.508 mm
        assert abs(pcb_to_mm(200000) - 0.508) < 0.001


class TestLayerNames:
    def test_top_layer(self):
        assert layer_id_to_name(1) == "Top Layer"

    def test_bottom_layer(self):
        assert layer_id_to_name(32) == "Bottom Layer"

    def test_mid_layers(self):
        assert layer_id_to_name(2) == "Mid Layer 1"
        assert layer_id_to_name(31) == "Mid Layer 30"

    def test_overlay_layers(self):
        assert layer_id_to_name(33) == "Top Overlay"
        assert layer_id_to_name(34) == "Bottom Overlay"

    def test_solder_mask(self):
        assert layer_id_to_name(37) == "Top Solder"
        assert layer_id_to_name(38) == "Bottom Solder"

    def test_mechanical_layers(self):
        assert layer_id_to_name(57) == "Mechanical 1"
        assert layer_id_to_name(72) == "Mechanical 16"

    def test_multi_layer(self):
        assert layer_id_to_name(74) == "Multi-Layer"

    def test_unknown_layer(self):
        result = layer_id_to_name(999)
        assert "Unknown" in result
