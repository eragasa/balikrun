# tests/specification/test_SequenceBlock.py
from __future__ import annotations

import pytest

from balikrun.specification import SequenceBlock


def test_SequenceBlock_requires_non_empty_items():
    """
    A SequenceBlock represents ordered composition and must contain at least one child.
    """
    with pytest.raises(ValueError):
        SequenceBlock.model_validate({"kind": "sequence", "items": []})


def test_SequenceBlock_preserves_order():
    """
    SequenceBlock order is semantically meaningful and must be preserved.
    """
    s = SequenceBlock.model_validate(
        {
            "kind": "sequence",
            "items": [
                {"kind": "task_ref", "task_id": "a"},
                {"kind": "task_ref", "task_id": "b"},
                {"kind": "task_ref", "task_id": "c"},
            ],
        }
    )
    assert [x.task_id for x in s.items] == ["a", "b", "c"]
