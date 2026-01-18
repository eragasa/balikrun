# tests/compile/test_SequenceBlock.py
from __future__ import annotations

from balikrun.compile import CompileOptions, compile_to_graph_ir
from balikrun.ir import NodeKind
from balikrun.specification import SequenceBlock, TaskReference


def test_single_task_sequence_emits_ENTRY_TASK_EXIT():
    spec = SequenceBlock(items=[TaskReference(task_id="t1")])
    g = compile_to_graph_ir(spec, options=CompileOptions(graph_id="g", node_id_prefix="n"))

    # Graph-level entry/exit nodes exist.
    assert g.entry_id != g.exit_id
    kinds = {n.node_id: n.kind for n in g.nodes}
    assert kinds[g.entry_id] == NodeKind.ENTRY
    assert kinds[g.exit_id] == NodeKind.EXIT

    # Exactly one TASK node exists and it has the correct task_id.
    task_nodes = [n for n in g.nodes if n.kind == NodeKind.TASK]
    assert len(task_nodes) == 1
    assert task_nodes[0].task_id == "t1"

    # Edges: ENTRY->TASK and TASK->EXIT
    assert len(g.edges) == 2
    assert (g.edges[0].src, g.edges[0].dst) == (g.entry_id, task_nodes[0].node_id)
    assert (g.edges[1].src, g.edges[1].dst) == (task_nodes[0].node_id, g.exit_id)

def test_two_task_sequence_preserves_order():
    specification = SequenceBlock(
        items=[
            TaskReference(task_id="a"), 
            TaskReference(task_id="b")
        ]
    )
    g = compile_to_graph_ir(
        specification, 
        options=CompileOptions(graph_id="g", node_id_prefix="n"))

    task_nodes = [n for n in g.nodes if n.kind == NodeKind.TASK]
    assert [n.task_id for n in task_nodes] == ["a", "b"]

    # Edges: ENTRY->a, a->b, b->EXIT (order-independent).
    assert len(g.edges) == 3
    edge_pairs = {(e.src, e.dst) for e in g.edges}
    assert edge_pairs == {
        (g.entry_id, task_nodes[0].node_id),
        (task_nodes[0].node_id, task_nodes[1].node_id),
        (task_nodes[1].node_id, g.exit_id),
    }


def test_preserves_spec_node_id_for_TaskReference_when_enabled():
    spec = SequenceBlock(items=[TaskReference(task_id="t1", node_id="task_ingest")])
    g = compile_to_graph_ir(spec, options=CompileOptions(graph_id="g", node_id_prefix="n", preserve_spec_node_ids=True))

    task_nodes = [n for n in g.nodes if n.kind == NodeKind.TASK]
    assert len(task_nodes) == 1
    assert task_nodes[0].node_id == "task_ingest"
