# src/balikrun/specification.py
from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class JoinMode(str, Enum):
    AND = "AND"
    OR = "OR"


class SpecificationModel(BaseModel):
  """
  Base class for all specification-layer models.

  Notes:
  - These objects are intended to be persisted as JSON.
  - Keep models immutable to support versioning and reproducibility.
  - `node_id` is optional but recommended for stable diffs and UI identity.
  """
  node_id: Optional[NonEmptyStr] = None
  model_config = ConfigDict(frozen=True, extra="forbid")


class TaskReference(SpecificationModel):
  task_id: NonEmptyStr
  kind: Literal["task_ref"] = "task_ref"

class SequenceBlock(SpecificationModel):
  kind: Literal["sequence"] = "sequence"
  items: list["Block"]

  @field_validator("items")
  @classmethod
  def _items_nonempty(cls, v: list["Block"]) -> list["Block"]:
      if len(v) == 0:
          raise ValueError("SequenceBlock.items must be non-empty.")
      return v


class ChoiceCase(SpecificationModel):
  """
  One branch of a ChoiceBlock.

  guard is an optional opaque predicate reference resolved at runtime by the engine
  (e.g., a registry key, expression id, etc.). If guard is None, this case is an
  unconditional branch (useful for "else"-style branches inside `cases`).
  """
  label: NonEmptyStr
  guard: NonEmptyStr | None 
  body: "Block"


class ChoiceBlock(SpecificationModel):
  kind: Literal["choice"] = "choice"
  cases: list[ChoiceCase]
  default: Optional["Block"] = None

  @field_validator("cases")
  @classmethod
  def _cases_nonempty(cls, v: list[ChoiceCase]) -> list[ChoiceCase]:
    if len(v) == 0:
      raise ValueError("ChoiceBlock.cases must be non-empty.")
    return v

  @field_validator("cases")
  @classmethod
  def _case_labels_unique(cls, v: list[ChoiceCase]) -> list[ChoiceCase]:
    labels = [c.label for c in v]
    if len(set(labels)) != len(labels):
      raise ValueError("ChoiceBlock.cases labels must be unique.")
    return v


class ParallelBranch(SpecificationModel):
  """
  One branch of a ParallelBlock.
  """
  label: NonEmptyStr
  body: "Block"

class ParallelBlock(SpecificationModel):
    kind: Literal["parallel"] = "parallel"
    branches: list[ParallelBranch]
    join: JoinMode = JoinMode.AND

    @field_validator("branches")
    @classmethod
    def _branches_nonempty(cls, v: list[ParallelBranch]) -> list[ParallelBranch]:
        if len(v) == 0:
            raise ValueError("ParallelBlock.branches must be non-empty.")
        return v

class ParallelBlock(SpecificationModel):
  """
  Parallel fork/join region.

  join:
    - AND: join when all branches complete.
    - OR: join when any one branch completes.

  Note:
  OR-join requires an engine policy for the losing branches (e.g., cancel, skip, or
  allow completion but ignore). The specification records only intent; the engine
  defines the operational policy.
  """
  kind: Literal["parallel"] = "parallel"
  branches: list[ParallelBranch]
  join: JoinMode = JoinMode.AND

  @field_validator("branches")
  @classmethod
  def _branches_nonempty(cls, v: list[ParallelBranch]) -> list[ParallelBranch]:
    if len(v) == 0:
      raise ValueError("ParallelBlock.branches must be non-empty.")
    return v

  @field_validator("branches")
  @classmethod
  def _branch_labels_unique(cls, v: list[ParallelBranch]) -> list[ParallelBranch]:
    labels = [b.label for b in v]
    if len(set(labels)) != len(labels):
      raise ValueError("ParallelBlock.branches labels must be unique.")
    return v


class LoopBlock(SpecificationModel):
    kind: Literal["loop"] = "loop"
    body: "Block"
    guard: NonEmptyStr
    max_iters: Optional[int] = None

    @field_validator("max_iters")
    @classmethod
    def _max_iters_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("LoopBlock.max_iters must be positive when provided.")
        return v



class CompositeBlock(SpecificationModel):
  kind: Literal["composite"] = "composite"
  name: NonEmptyStr
  body: "Block"


Block = Annotated[
  Union[
    TaskReference,
    SequenceBlock,
    ChoiceBlock,
    ParallelBlock,
    LoopBlock,
    CompositeBlock,
  ],
  Field(discriminator="kind"),
]

# Resolve forward references.
TaskReference.model_rebuild()
SequenceBlock.model_rebuild()
ChoiceCase.model_rebuild()
ChoiceBlock.model_rebuild()
ParallelBranch.model_rebuild()
ParallelBlock.model_rebuild()
LoopBlock.model_rebuild()
CompositeBlock.model_rebuild()
