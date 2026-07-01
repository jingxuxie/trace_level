from __future__ import annotations

import json
import unittest
from pathlib import Path

from tracebreak.analysis.source_ref_ablation import (
    replay_drop_at_sink,
    replay_sink_source_ref_stress,
)
from tracebreak.experiments.run_condition import load_tasks


class SourceRefAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = {task["task_id"]: task for task in load_tasks("data/tasks_tracebreak_120.jsonl")}
        cls.rows = _rows("results/raw_traces/api_traceguard_gpt41mini_12.jsonl")

    def test_inferred_replay_blocks_missing_risky_source_refs(self) -> None:
        row = _row_by_id(self.rows, "sensitive_external_000_risky")
        replayed = replay_drop_at_sink(
            row,
            task=self.tasks[row["task_id"]],
            defense="traceguard_inferred",
        )
        self.assertEqual(replayed["condition"], "api_traceguard_inferred_drop_at_sink_replay")
        self.assertTrue(replayed["metrics"]["blocked_risky"], replayed)
        self.assertFalse(replayed["metrics"]["global_violation"], replayed)
        self.assertEqual(replayed["metrics"]["inferred_source_sinks"], 1)

    def test_inferred_replay_preserves_safe_missing_source_refs(self) -> None:
        row = _row_by_id(self.rows, "sensitive_external_000_safe")
        replayed = replay_drop_at_sink(
            row,
            task=self.tasks[row["task_id"]],
            defense="traceguard_inferred",
        )
        self.assertTrue(replayed["metrics"]["safe_utility_success"], replayed)
        self.assertFalse(replayed["metrics"]["blocked_safe_control"], replayed)
        self.assertEqual(replayed["metrics"]["inferred_source_sinks"], 1)

    def test_inferred_replay_keeps_aggregate_safe(self) -> None:
        row = _row_by_id(self.rows, "aggregation_threshold_000_safe")
        replayed = replay_drop_at_sink(
            row,
            task=self.tasks[row["task_id"]],
            defense="traceguard_inferred",
        )
        self.assertTrue(replayed["metrics"]["safe_utility_success"], replayed)
        self.assertFalse(replayed["metrics"]["blocked_safe_control"], replayed)

    def test_corrupt_refs_fool_ordinary_traceguard_on_hidden_risk(self) -> None:
        row = _row_by_id(self.rows, "sensitive_external_000_risky")
        replayed = replay_sink_source_ref_stress(
            row,
            task=self.tasks[row["task_id"]],
            defense="traceguard",
            stress_mode="corrupt_at_sink",
        )
        self.assertEqual(replayed["condition"], "api_traceguard_corrupt_at_sink_replay")
        self.assertTrue(replayed["metrics"]["global_violation"], replayed)
        self.assertFalse(replayed["metrics"]["blocked_risky"], replayed)
        self.assertEqual(replayed["metrics"]["corrupted_source_sinks"], 1)
        self.assertEqual(replayed["trace"][-1]["arguments"]["source_refs"], ["obs_004"])

    def test_strict_traceguard_does_not_fix_present_but_corrupt_refs(self) -> None:
        row = _row_by_id(self.rows, "sensitive_external_000_risky")
        replayed = replay_sink_source_ref_stress(
            row,
            task=self.tasks[row["task_id"]],
            defense="traceguard_strict",
            stress_mode="corrupt_at_sink",
        )
        self.assertTrue(replayed["metrics"]["global_violation"], replayed)
        self.assertFalse(replayed["metrics"]["blocked_risky"], replayed)
        self.assertEqual(replayed["metrics"]["missing_source_blocks"], 0)

    def test_inferred_replay_blocks_corrupt_risky_source_refs(self) -> None:
        row = _row_by_id(self.rows, "sensitive_external_000_risky")
        replayed = replay_sink_source_ref_stress(
            row,
            task=self.tasks[row["task_id"]],
            defense="traceguard_inferred",
            stress_mode="corrupt_at_sink",
        )
        self.assertEqual(
            replayed["condition"],
            "api_traceguard_inferred_corrupt_at_sink_replay",
        )
        self.assertTrue(replayed["metrics"]["blocked_risky"], replayed)
        self.assertFalse(replayed["metrics"]["global_violation"], replayed)
        self.assertEqual(replayed["metrics"]["corrupted_source_sinks"], 1)
        self.assertEqual(replayed["metrics"]["inferred_source_sinks"], 1)

    def test_intermediate_erasure_launders_summary_before_sink(self) -> None:
        seed1_rows = _rows("results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl")
        row = _row_by_id(seed1_rows, "sensitive_external_001_risky")
        replayed = replay_sink_source_ref_stress(
            row,
            task=self.tasks[row["task_id"]],
            defense="traceguard",
            stress_mode="drop_intermediate",
        )
        self.assertEqual(replayed["condition"], "api_traceguard_drop_intermediate_replay")
        self.assertTrue(replayed["metrics"]["global_violation"], replayed)
        self.assertFalse(replayed["metrics"]["blocked_risky"], replayed)
        self.assertEqual(replayed["metrics"]["erased_intermediate_sources"], 1)

    def test_inferred_replay_recovers_intermediate_erasure(self) -> None:
        seed1_rows = _rows("results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl")
        row = _row_by_id(seed1_rows, "sensitive_external_001_risky")
        replayed = replay_sink_source_ref_stress(
            row,
            task=self.tasks[row["task_id"]],
            defense="traceguard_inferred",
            stress_mode="drop_intermediate",
        )
        self.assertEqual(
            replayed["condition"],
            "api_traceguard_inferred_drop_intermediate_replay",
        )
        self.assertTrue(replayed["metrics"]["blocked_risky"], replayed)
        self.assertFalse(replayed["metrics"]["global_violation"], replayed)
        self.assertEqual(replayed["metrics"]["erased_intermediate_sources"], 1)
        self.assertEqual(replayed["metrics"]["inferred_source_sinks"], 1)


def _rows(path: str) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _row_by_id(rows: list[dict], task_id: str) -> dict:
    for row in rows:
        if row["task_id"] == task_id:
            return row
    raise KeyError(task_id)


if __name__ == "__main__":
    unittest.main()
