# tests/ir/test_Node.py
# testing balikrun.ir.Node
from __future__ import annotations

import pytest

from balikrun.ir import Node

def test_Node_requires_task_id_for_TASK_nodes():
    """
    TASK nodes must include task_id because the engine resolves execution via task_id.
    """
    with pytest.raises(ValueError):
        Node.model_validate({"node_id": "t", "kind": "TASK"})

def test_Node_allows_missing_task_id_for_non_TASK_nodes():
    """
    ENTRY/EXIT/etc. nodes must not require task_id.
    """
    n = Node.model_validate({"node_id": "entry", "kind": "ENTRY"})
    assert n.task_id is None

def test_Node_meta_defaults_to_empty_dict():
    """
    meta is optional and defaults to {} for stable consumption by UI/debug tools.
    """
    n = Node.model_validate({"node_id": "x", "kind": "EXIT"})
    assert n.meta == {}

def test_Node_forbids_extra_fields():
    """
    IR models are strict JSON contracts. Unknown fields must be rejected.
    """
    with pytest.raises(ValueError):
        Node.model_validate({"node_id": "x", "kind": "EXIT", "extra": 123})
