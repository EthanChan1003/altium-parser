"""Tests for JSON and XML serializers."""

from altium_parser.serializers.json_serializer import serialize_to_json
from altium_parser.serializers.xml_serializer import serialize_to_xml
from altium_parser.models.project import AltiumProject, ProjectDocument

import json


class _MockModel:
    """Simple mock model for testing serializers."""

    def to_dict(self):
        return {
            "components": [
                {"refdes": "U1", "position": {"x_mm": 10.0, "y_mm": 20.0}},
                {"refdes": "R1", "position": {"x_mm": 30.0, "y_mm": 40.0}},
            ],
            "statistics": {"component_count": 2},
        }


class TestJsonSerializer:
    def test_basic_serialization(self):
        model = _MockModel()
        result = serialize_to_json(model, "SchDoc", "test.SchDoc")
        parsed = json.loads(result)

        assert parsed["schema_version"] == "1.0"
        assert parsed["generator"] == "altium-parser"
        assert parsed["file_type"] == "SchDoc"
        assert parsed["source_file"] == "test.SchDoc"
        assert len(parsed["data"]["components"]) == 2
        assert parsed["data"]["components"][0]["refdes"] == "U1"

    def test_compact_output(self):
        model = _MockModel()
        pretty = serialize_to_json(model, "SchDoc", "test.SchDoc", pretty=True)
        compact = serialize_to_json(model, "SchDoc", "test.SchDoc", pretty=False)
        assert len(compact) < len(pretty)
        assert "\n" not in compact

    def test_project_model(self):
        project = AltiumProject(
            filename="test.PrjPcb",
            version="1.0",
            documents=[
                ProjectDocument(path="Sheet.SchDoc", doc_type="SchDoc"),
            ],
        )
        result = serialize_to_json(project, "PrjPcb", "test.PrjPcb")
        parsed = json.loads(result)
        assert parsed["file_type"] == "PrjPcb"
        assert len(parsed["data"]["documents"]) == 1


class TestXmlSerializer:
    def test_basic_serialization(self):
        model = _MockModel()
        result = serialize_to_xml(model, "PcbDoc", "test.PcbDoc")

        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert 'file-type="PcbDoc"' in result
        assert 'source-file="test.PcbDoc"' in result
        assert "altium-document" in result

    def test_contains_components(self):
        model = _MockModel()
        result = serialize_to_xml(model, "SchDoc", "test.SchDoc")
        assert "component" in result
        assert "U1" in result
        assert "R1" in result

    def test_project_model(self):
        project = AltiumProject(
            filename="test.PrjPcb",
            version="1.0",
            documents=[
                ProjectDocument(path="Sheet.SchDoc", doc_type="SchDoc"),
            ],
        )
        result = serialize_to_xml(project, "PrjPcb", "test.PrjPcb")
        assert "PrjPcb" in result
        assert "Sheet.SchDoc" in result
