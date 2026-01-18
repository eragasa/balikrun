# tests/ir/test_GraphIR.py
from __future__ import annotations

import pytest

from balikrun.ir import GraphIR, NodeKind


def test_GraphIR_minimal_valid_graph():
    """
    Minimal executable GraphIR:
      ENTRY -> TASK -> EXIT
    """
    g = GraphIR.model_validate(
        {
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
    )

    assert g.entry_id == "n0"
    assert g.exit_id == "n2"
    assert [n.kind for n in g.nodes] == [NodeKind.ENTRY, NodeKind.TASK, NodeKind.EXIT]
    assert g.nodes[1].task_id == "ingest"


def test_GraphIR_rejects_missing_entry_or_exit_nodes():
    """
    entry_id and exit_id must reference existing nodes.
    """
    with pytest.raises(ValueError):
        GraphIR.model_validate(
            {
                "graph_id": "bad",
                "nodes": [{"node_id": "n0", "kind": "ENTRY"}],
                "edges": [],
                "entry_id": "n0",
                "exit_id": "missing",
            }
        )


def test_GraphIR_rejects_edges_with_missing_endpoints():
    """
    Edge endpoints must exist in nodes.
    """
    with pytest.raises(ValueError):
        GraphIR.model_validate(
            {
                "graph_id": "bad2",
                "nodes": [{"node_id": "n0", "kind": "ENTRY"}, {"node_id": "n1", "kind": "EXIT"}],
                "edges": [{"src": "n0", "dst": "nope"}],
                "entry_id": "n0",
                "exit_id": "n1",
            }
        )


def test_GraphIR_rejects_duplicate_node_ids():
    """
    Node ids must be unique across the graph.
    """
    with pytest.raises(ValueError):
        GraphIR.model_validate(
            {
                "graph_id": "bad3",
                "nodes": [{"node_id": "n0", "kind": "ENTRY"}, {"node_id": "n0", "kind": "EXIT"}],
                "edges": [],
                "entry_id": "n0",
                "exit_id": "n0",
            }
        )


def test_GraphIR_rejects_duplicate_edges_by_src_dst_label():
    """
    Duplicate edges are defined as same (src, dst, label).
    """
    with pytest.raises(ValueError):
        GraphIR.model_validate(
            {
                "graph_id": "bad4",
                "nodes": [{"node_id": "a", "kind": "ENTRY"}, {"node_id": "b", "kind": "EXIT"}],
                "edges": [
                    {"src": "a", "dst": "b", "label": "x"},
                    {"src": "a", "dst": "b", "label": "x"},
                ],
                "entry_id": "a",
                "exit_id": "b",
            }
        )

def test_GraphIR_parses_all_NodeKind_values():
    """
    Lock down the enum surface so adding/removing kinds is an explicit change.
    """
    kinds = ["ENTRY", "EXIT", "TASK", "DECISION", "MERGE", "FORK", "JOIN"]
    for i, k in enumerate(kinds):
        node = {"node_id": f"n{i}", "kind": k}
        if k == "TASK":
            node["task_id"] = "t"
        g = GraphIR.model_validate(
            {
                "graph_id": f"g_{k}",
                "nodes": [node],
                "edges": [],
                "entry_id": node["node_id"],
                "exit_id": node["node_id"],
            }
        )
        assert g.nodes[0].kind.value == k
