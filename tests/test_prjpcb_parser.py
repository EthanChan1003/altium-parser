"""Tests for PrjPcb parser."""

import tempfile
from pathlib import Path

from altium_parser.parsers.prjpcb_parser import PrjPcbParser


class TestPrjPcbParser:
    def test_parse_basic_project(self, sample_prjpcb_text):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".PrjPcb", delete=False, encoding="utf-8") as f:
            f.write(sample_prjpcb_text)
            f.flush()

            parser = PrjPcbParser(f.name)
            project = parser.parse()

            assert project.filename.endswith(".PrjPcb")
            assert project.version == "1.0"
            assert len(project.documents) == 3
            assert project.documents[0].path == "TopSheet.SchDoc"
            assert project.documents[0].doc_type == "SchDoc"
            assert project.documents[1].path == "Board.PcbDoc"
            assert project.documents[1].doc_type == "PcbDoc"
            assert project.documents[2].path == "Components.SchLib"
            assert project.documents[2].doc_type == "SchLib"

        Path(f.name).unlink(missing_ok=True)

    def test_parse_empty_project(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".PrjPcb", delete=False, encoding="utf-8") as f:
            f.write("[Design]\nVersion=2.0\nDocumentCount=0\n")
            f.flush()

            parser = PrjPcbParser(f.name)
            project = parser.parse()

            assert project.version == "2.0"
            assert len(project.documents) == 0

        Path(f.name).unlink(missing_ok=True)

    def test_to_dict(self, sample_prjpcb_text):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".PrjPcb", delete=False, encoding="utf-8") as f:
            f.write(sample_prjpcb_text)
            f.flush()

            parser = PrjPcbParser(f.name)
            project = parser.parse()
            d = project.to_dict()

            assert "version" in d
            assert "documents" in d
            assert len(d["documents"]) == 3
            assert d["documents"][0]["path"] == "TopSheet.SchDoc"

        Path(f.name).unlink(missing_ok=True)
