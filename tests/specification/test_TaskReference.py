# tests/specification/test_TaskReference.py
from __future__ import annotations

import pytest

from balikrun.specification import TaskReference


def test_TaskReference_minimal_fields():
    """
    TaskReference is the leaf node of the AST.

    It is stateless: it names a task template (`task_id`) but does not represent a run.
    """
    t = TaskReference.model_validate({"kind": "task_ref", "task_id": "ingest"})
    assert t.kind == "task_ref"
    assert t.task_id == "ingest"
    assert t.node_id is None


def test_TaskReference_forbids_extra_fields():
    """
    Specification models are strict JSON contracts. Unknown fields must be rejected.
    """
    with pytest.raises(ValueError):
        TaskReference.model_validate({"kind": "task_ref", "task_id": "x", "extra": 123})
