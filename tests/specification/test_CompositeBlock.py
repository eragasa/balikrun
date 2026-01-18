# tests/specification/test_CompositeBlock.py
from __future__ import annotations

import pytest

from balikrun.specification import CompositeBlock


def test_CompositeBlock_minimal_fields():
    """
    CompositeBlock is a named, nestable region. It is intended to compile as SESE.
    """
    c = CompositeBlock.model_validate(
        {"kind": "composite", "name": "packaging", "body": {"kind": "task_ref", "task_id": "bundle"}}
    )
    assert c.name == "packaging"
    assert c.body.kind == "task_ref"


def test_CompositeBlock_forbids_extra_fields():
    """
    Specification models are strict JSON contracts. Unknown fields must be rejected.
    """
    with pytest.raises(ValueError):
        CompositeBlock.model_validate(
            {
                "kind": "composite",
                "name": "x",
                "body": {"kind": "task_ref", "task_id": "t"},
                "extra": 123,
            }
        )
