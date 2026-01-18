# tests/ir/test_Edge.py
from __future__ import annotations
import pytest
from balikrun.ir import Edge


def test_Edge_minimal_fields():
    """
    Edges minimally require src and dst.
    label/guard/meta are optional.
    """
    e = Edge.model_validate({"src": "a", "dst": "b"})
    assert e.src == "a"
    assert e.dst == "b"
    assert e.label is None
    assert e.guard is None
    assert e.meta == {}

def test_Edge_rejects_empty_src_or_dst():
    """
    src and dst are identifiers; empty strings are invalid.
    """
    with pytest.raises(ValueError):
        Edge.model_validate({"src": "", "dst": "b"})
    with pytest.raises(ValueError):
        Edge.model_validate({"src": "a", "dst": ""})
