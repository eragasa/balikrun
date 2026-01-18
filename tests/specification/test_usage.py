# tests/specification/test_usage.py
from __future__ import annotations

from balikrun.specification import (
    ChoiceBlock,
    ChoiceCase,
    CompositeBlock,
    LoopBlock,
    ParallelBlock,
    ParallelBranch,
    SequenceBlock,
    TaskReference,
)


def test_Specification_usage_nested_blocks_roundtrip():
    """
    Canonical usage example for developers.

    This constructs a realistic nested workflow specification and round-trips it through
    model_dump()/model_validate() to demonstrate JSON persistence behavior.
    """
    spec = SequenceBlock(
        items=[
            TaskReference(task_id="ingest"),
            ParallelBlock(
                branches=[
                    ParallelBranch(label="train", body=TaskReference(task_id="train")),
                    ParallelBranch(label="eval", body=TaskReference(task_id="eval")),
                ]
            ),
            ChoiceBlock(
                cases=[
                    ChoiceCase(label="publish", guard="is_good", body=TaskReference(task_id="publish")),
                ],
                default=LoopBlock(
                    guard="not_good",
                    max_iters=3,
                    body=TaskReference(task_id="tune"),
                ),
            ),
            CompositeBlock(
                name="packaging",
                body=SequenceBlock(
                    items=[
                        TaskReference(task_id="bundle"),
                        TaskReference(task_id="upload"),
                    ]
                ),
            ),
        ]
    )

    payload = spec.model_dump(mode="python")
    spec2 = SequenceBlock.model_validate(payload)

    assert spec2.kind == "sequence"
    assert [b.kind for b in spec2.items] == ["task_ref", "parallel", "choice", "composite"]
