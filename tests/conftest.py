"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_kv_bytes():
    """Sample pipe-delimited KV record bytes."""
    return b"|RECORD=1|LIBREFERENCE=RES_0402|COMPONENTDESCRIPTION=Resistor 10K|LOCATION.X=500|LOCATION.Y=300|ORIENTATION=0|"


@pytest.fixture
def sample_kv_with_special():
    """KV record with special characters."""
    return b"|RECORD=41|NAME=Value|TEXT=10K=5%|OWNERINDEX=3|ISHIDDEN=T|"


@pytest.fixture
def sample_wire_kv():
    """Wire record with coordinate points."""
    return b"|RECORD=27|LOCATIONCOUNT=3|X1=100|Y1=200|X2=300|Y2=200|X3=300|Y3=400|"


@pytest.fixture
def sample_prjpcb_text():
    """Sample PrjPcb file content."""
    return """[Design]
Version=1.0
DocumentCount=3

[Document1]
DocumentPath=TopSheet.SchDoc

[Document2]
DocumentPath=Board.PcbDoc

[Document3]
DocumentPath=Components.SchLib
"""
