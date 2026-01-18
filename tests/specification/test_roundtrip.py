# tests/specification/test_roundtrip.py
from __future__ import annotations

import pytest

from balikrun.specification import (
    ChoiceBlock,
    LoopBlock,
    ParallelBlock,
    SequenceBlock,
)


def test_roundtrip_nested_spec_canonical_dump():
    """
    Lock-down test:
    - parse a nested spec from JSON (dict)
    - dump back to python
    - assert canonical (stable) structure
    """
    spec_dict = {
        "kind": "sequence",
        "items": [
            {"kind": "task_ref", "task_id": "ingest"},
            {
                "kind": "parallel",
                "join": "AND",
                "branches": [
                    {"label": "train", "body": {"kind": "task_ref", "task_id": "train"}},
                    {"label": "eval", "body": {"kind": "task_ref", "task_id": "eval"}},
                ],
            },
            {
                "kind": "choice",
                "cases": [
                    {
                        "label": "publish",
                        "guard": "is_good",
                        "body": {"kind": "task_ref", "task_id": "publish"},
                    }
                ],
                "default": {
                    "kind": "loop",
                    "guard": "not_good",
                    "max_iters": 3,
                    "body": {"kind": "task_ref", "task_id": "tune"},
                },
            },
            {
                "kind": "composite",
                "name": "packaging",
                "body": {
                    "kind": "sequence",
                    "items": [
                        {"kind": "task_ref", "task_id": "bundle"},
                        {"kind": "task_ref", "task_id": "upload"},
                    ],
                },
            },
        ],
    }

    spec = SequenceBlock.model_validate(spec_dict)
    dumped = spec.model_dump(mode="python")

    expected = {
        "node_id": None,
        "kind": "sequence",
        "items": [
            {"node_id": None, "kind": "task_ref", "task_id": "ingest"},
            {
                "node_id": None,
                "kind": "parallel",
                "branches": [
                    {
                        "node_id": None,
                        "label": "train",
                        "body": {"node_id": None, "kind": "task_ref", "task_id": "train"},
                    },
                    {
                        "node_id": None,
                        "label": "eval",
                        "body": {"node_id": None, "kind": "task_ref", "task_id": "eval"},
                    },
                ],
                "join": "AND",
            },
            {
                "node_id": None,
                "kind": "choice",
                "cases": [
                    {
                        "node_id": None,
                        "label": "publish",
                        "guard": "is_good",
                        "body": {"node_id": None, "kind": "task_ref", "task_id": "publish"},
                    }
                ],
                "default": {
                    "node_id": None,
                    "kind": "loop",
                    "body": {"node_id": None, "kind": "task_ref", "task_id": "tune"},
                    "guard": "not_good",
                    "max_iters": 3,
                },
            },
            {
                "node_id": None,
                "kind": "composite",
                "name": "packaging",
                "body": {
                    "node_id": None,
                    "kind": "sequence",
                    "items": [
                        {"node_id": None, "kind": "task_ref", "task_id": "bundle"},
                        {"node_id": None, "kind": "task_ref", "task_id": "upload"},
                    ],
                },
            },
        ],
    }

    assert dumped == expected


def test_label_uniqueness_is_enforced():
    with pytest.raises(ValueError):
        ChoiceBlock.model_validate(
            {
                "kind": "choice",
                "cases": [
                    {"label": "x", "guard": "g1", "body": {"kind": "task_ref", "task_id": "a"}},
                    {"label": "x", "guard": "g2", "body": {"kind": "task_ref", "task_id": "b"}},
                ],
            }
        )

    with pytest.raises(ValueError):
        ParallelBlock.model_validate(
            {
                "kind": "parallel",
                "branches": [
                    {"label": "x", "body": {"kind": "task_ref", "task_id": "a"}},
                    {"label": "x", "body": {"kind": "task_ref", "task_id": "b"}},
                ],
            }
        )


def test_loop_max_iters_positive_when_provided():
    with pytest.raises(ValueError):
        LoopBlock.model_validate(
            {"kind": "loop", "guard": "g", "max_iters": 0, "body": {"kind": "task_ref", "task_id": "t"}}
        )
