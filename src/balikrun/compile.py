# src/balikrun/compile.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from balikrun.ir import Edge, GraphIR, Node, NodeKind
from balikrun.specification import (
    Block,
    SequenceBlock,
    TaskReference,
)


@dataclass(frozen=True)
class CompileOptions:
    """
    Options controlling compilation behavior.

    graph_id:
      Identifier for the emitted GraphIR.

    node_id_prefix:
      Prefix used when generating node ids. Useful to avoid collisions across compilations.

    preserve_spec_node_ids:
      If True, and if a spec node has node_id, the compiler will use it where compatible.
      v0: only applied for TaskReference -> TASK node ids.
    """
    graph_id: str = "workflow"
    node_id_prefix: str = "n"
    preserve_spec_node_ids: bool = True


class _IdGen:
    """
    Deterministic id generator for compiler-emitted nodes.

    This keeps GraphIR stable across runs given the same spec structure.
    """
    def __init__(self, prefix: str):
        self._prefix = prefix
        self._i = 0

    def next(self) -> str:
        s = f"{self._prefix}{self._i}"
        self._i += 1
        return s


def compile_to_graph_ir(spec: Block, *, options: CompileOptions | None = None) -> GraphIR:
    """
    Compile a specification AST Block into GraphIR.

    v0 supports:
      - TaskReference
      - SequenceBlock

    Unsupported blocks raise NotImplementedError.
    """
    opts = options or CompileOptions()
    ids = _IdGen(prefix=opts.node_id_prefix)

    nodes: list[Node] = []
    edges: list[Edge] = []

    entry_id = ids.next()
    exit_id = ids.next()

    nodes.append(Node(node_id=entry_id, kind=NodeKind.ENTRY))
    nodes.append(Node(node_id=exit_id, kind=NodeKind.EXIT))

    entry_handle = _Handle(entry_id=entry_id, exit_id=exit_id)

    compiled = _compile_block(spec, nodes=nodes, edges=edges, ids=ids, opts=opts)

    # Wire global ENTRY -> compiled entry, compiled exit -> global EXIT
    edges.append(Edge(src=entry_id, dst=compiled.entry_id))
    edges.append(Edge(src=compiled.exit_id, dst=exit_id))

    return GraphIR(
        graph_id=opts.graph_id,
        nodes=nodes,
        edges=edges,
        entry_id=entry_id,
        exit_id=exit_id,
    )


@dataclass(frozen=True)
class _Handle:
    """
    A SESE-like interface for compiled regions.

    entry_id:
      Node id where control enters this compiled region.

    exit_id:
      Node id where control leaves this compiled region.
    """
    entry_id: str
    exit_id: str


def _compile_block(
    block: Block,
    *,
    nodes: list[Node],
    edges: list[Edge],
    ids: _IdGen,
    opts: CompileOptions,
) -> _Handle:
    """
    Internal compiler dispatch.
    """
    if isinstance(block, TaskReference):
        return _compile_task_ref(
            block, 
            nodes=nodes, 
            ids=ids, 
            opts=opts
        )

    if isinstance(block, SequenceBlock):
        return _compile_sequence(
            block, 
            nodes=nodes, 
            edges=edges, 
            ids=ids, 
            opts=opts
        )

    raise NotImplementedError(f"Compilation not implemented for kind={getattr(block, 'kind', type(block))!r}")


def _compile_task_ref(
    t: TaskReference,
    *,
    nodes: list[Node],
    ids: _IdGen,
    opts: CompileOptions,
) -> _Handle:
    """
    TaskReference -> single TASK node with identical entry/exit handle.
    """
    node_id = None
    if opts.preserve_spec_node_ids and t.node_id:
        node_id = t.node_id
    else:
        node_id = ids.next()

    nodes.append(Node(node_id=node_id, kind=NodeKind.TASK, task_id=t.task_id))
    return _Handle(entry_id=node_id, exit_id=node_id)


def _compile_sequence(
    s: SequenceBlock,
    *,
    nodes: list[Node],
    edges: list[Edge],
    ids: _IdGen,
    opts: CompileOptions,
) -> _Handle:
    """
    SequenceBlock -> chain child regions by edges: child[i].exit -> child[i+1].entry
    """
    child_handles: list[_Handle] = []
    for item in s.items:
        child_handles.append(_compile_block(item, nodes=nodes, edges=edges, ids=ids, opts=opts))

    # s.items is validated non-empty in the spec layer, but keep this guard anyway.
    if not child_handles:
        raise ValueError("SequenceBlock compiled with no children (should be prevented by specification validation).")

    for h0, h1 in zip(child_handles, child_handles[1:]):
        edges.append(Edge(src=h0.exit_id, dst=h1.entry_id))

    return _Handle(
        entry_id=child_handles[0].entry_id, 
        exit_id=child_handles[-1].exit_id)
