# tests/ir/roundtrip.py

# tests/ir/test_roundtrip.py
from __future__ import annotations

import pytest

from balikrun.ir import Edge, GraphIR, Node, NodeKind


def test_graphir_roundtrip_canonical_dump():
    g_dict = {
        "graph_id": "demo",
        "nodes": [
            {"node_id": "n0", "kind": "ENTRY"},
            {"node_id": "n1", "kind": "TASK", "task_id": "ingest"},
            {"node_id": "n2", "kind": "EXIT"},
        ],
        "edges": [
            {"src": "n0", "dst": "n1"},
            {"src": "n1", "dst": "n2"},
        ],
        "entry_id": "n0",
        "exit_id": "n2",
    }

    g = GraphIR.model_validate(g_dict)
    dumped = g.model_dump(mode="python")

    expected = {
        "graph_id": "demo",
        "nodes": [
            {"node_id": "n0", "kind": NodeKind.ENTRY, "task_id": None, "guard": None, "meta": {}},
            {"node_id": "n1", "kind": NodeKind.TASK, "task_id": "ingest", "guard": None, "meta": {}},
            {"node_id": "n2", "kind": NodeKind.EXIT, "task_id": None, "guard": None, "meta": {}},
        ],
        "edges": [
            {"src": "n0", "dst": "n1", "label": None, "guard": None, "meta": {}},
            {"src": "n1", "dst": "n2", "label": None, "guard": None, "meta": {}},
        ],
        "entry_id": "n0",
        "exit_id": "n2",
    }

    assert dumped == expected


def test_graphir_rejects_missing_endpoints():
    with pytest.raises(ValueError):
        GraphIR.model_validate(
            {
                "graph_id": "bad",
                "nodes": [{"node_id": "n0", "kind": "ENTRY"}, {"node_id": "n1", "kind": "EXIT"}],
                "edges": [{"src": "n0", "dst": "nX"}],
                "entry_id": "n0",
                "exit_id": "n1",
            }
        )


def test_graphir_requires_task_id_for_task_nodes():
    with pytest.raises(ValueError):
        GraphIR.model_validate(
            {
                "graph_id": "bad2",
                "nodes": [{"node_id": "n0", "kind": "ENTRY"}, {"node_id": "t", "kind": "TASK"}, {"node_id": "n1", "kind": "EXIT"}],
                "edges": [{"src": "n0", "dst": "t"}, {"src": "t", "dst": "n1"}],
                "entry_id": "n0",
                "exit_id": "n1",
            }
        )
