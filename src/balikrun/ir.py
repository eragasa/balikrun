# src/balikrun/ir.py
from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal, Optional

from pydantic import (
   BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator
)

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class IRModel(BaseModel):
    """
    Base class for GraphIR models.

    Notes:
    - Intended to be persisted as JSON.
    - Frozen + forbid extra fields for versioned reproducibility.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")


class NodeKind(str, Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"

    TASK = "TASK"

    DECISION = "DECISION"
    MERGE = "MERGE"

    FORK = "FORK"
    JOIN = "JOIN"


class Node(IRModel):
    """
    One node in the compiled workflow graph.
    """
    node_id: NonEmptyStr
    kind: NodeKind

    task_id: Optional[NonEmptyStr] = None
    guard: Optional[NonEmptyStr] = None
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _require_task_id_for_task_nodes(self) -> "Node":
        if self.kind == NodeKind.TASK and (self.task_id is None or str(self.task_id).strip() == ""):
            raise ValueError("Node.task_id is required when Node.kind == TASK.")
        return self

class Edge(IRModel):
    """
    Directed edge between nodes.

    label: stable human-readable discriminator (e.g., branch/case label)
    guard: optional predicate reference applied to this edge (edge guard)
    """
    src: NonEmptyStr
    dst: NonEmptyStr
    label: Optional[NonEmptyStr] = None
    guard: Optional[NonEmptyStr] = None
    meta: dict[str, Any] = Field(default_factory=dict)


class GraphIR(IRModel):
    """
    Graph Intermediate Representation.

    entry_id and exit_id define the SESE interface for the compiled workflow as a whole.
    """
    graph_id: NonEmptyStr
    nodes: list[Node]
    edges: list[Edge]
    entry_id: NonEmptyStr
    exit_id: NonEmptyStr

    @field_validator("nodes")
    @classmethod
    def _node_ids_unique(cls, v: list[Node]) -> list[Node]:
        ids = [n.node_id for n in v]
        if len(set(ids)) != len(ids):
            raise ValueError("GraphIR.nodes node_id values must be unique.")
        return v

    @field_validator("edges")
    @classmethod
    def _edges_no_duplicate_triplets(cls, v: list[Edge]) -> list[Edge]:
        seen: set[tuple[str, str, Optional[str]]] = set()
        for e in v:
            key = (e.src, e.dst, e.label)
            if key in seen:
                raise ValueError("GraphIR.edges must not contain duplicate (src,dst,label) edges.")
            seen.add(key)
        return v

    @field_validator("entry_id")
    @classmethod
    def _entry_exit_nodes_exist(cls, v: str, info):
        # this validator runs for entry_id; we also check exit_id below
        nodes = info.data.get("nodes") or []
        node_ids = {n.node_id for n in nodes}
        if v not in node_ids:
            raise ValueError("GraphIR.entry_id must reference an existing node_id.")
        return v

    @field_validator("exit_id")
    @classmethod
    def _exit_node_exists(cls, v: str, info):
        nodes = info.data.get("nodes") or []
        node_ids = {n.node_id for n in nodes}
        if v not in node_ids:
            raise ValueError("GraphIR.exit_id must reference an existing node_id.")
        return v

    @field_validator("edges")
    @classmethod
    def _edge_endpoints_exist(cls, v: list[Edge], info) -> list[Edge]:
        nodes = info.data.get("nodes") or []
        node_ids = {n.node_id for n in nodes}
        for e in v:
            if e.src not in node_ids:
                raise ValueError(f"GraphIR edge src '{e.src}' not found in nodes.")
            if e.dst not in node_ids:
                raise ValueError(f"GraphIR edge dst '{e.dst}' not found in nodes.")
        return v
