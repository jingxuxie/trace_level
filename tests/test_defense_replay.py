from __future__ import annotations

import json
import unittest
from pathlib import Path

from tracebreak.analysis.defense_replay import replay_row
from tracebreak.experiments.run_condition import load_tasks


class DefenseReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task_by_id = {
            task["task_id"]: task for task in load_tasks("data/tasks_tracebreak_120.jsonl")
        }
        self.row = _row_by_id(
            "results/raw_traces/api_local_gpt41mini_12.jsonl",
            "sensitive_external_000_risky",
        )
        self.task = self.task_by_id[self.row["task_id"]]

    def test_dlp_replay_allows_hidden_sensitive_external_violation(self) -> None:
        replayed = replay_row(self.row, task=self.task, defense_name="dlp")

        self.assertEqual(replayed["condition"], "api_local_replay_dlp")
        self.assertFalse(replayed["metrics"]["blocked_risky"], replayed)
        self.assertTrue(replayed["metrics"]["global_violation"], replayed)
        self.assertTrue(replayed["metrics"]["local_pass_violation"], replayed)

    def test_traceguard_replay_blocks_same_proposed_sink(self) -> None:
        replayed = replay_row(self.row, task=self.task, defense_name="traceguard")

        self.assertEqual(replayed["condition"], "api_local_replay_traceguard")
        self.assertTrue(replayed["metrics"]["blocked_risky"], replayed)
        self.assertFalse(replayed["metrics"]["global_violation"], replayed)
        self.assertEqual(
            replayed["trace"][-1]["defense_decision"]["reason_code"],
            "internal_data_to_external_recipient",
        )

    def test_metadata_critic_replay_blocks_hidden_sensitive_external_violation(self) -> None:
        replayed = replay_row(self.row, task=self.task, defense_name="metadata_critic")

        self.assertEqual(replayed["condition"], "api_local_replay_metadata_critic")
        self.assertTrue(replayed["metrics"]["blocked_risky"], replayed)
        self.assertFalse(replayed["metrics"]["global_violation"], replayed)
        self.assertEqual(replayed["replay_defense"], "metadata_critic")


def _row_by_id(path: str, task_id: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row["task_id"] == task_id:
                    return row
    raise KeyError(task_id)


if __name__ == "__main__":
    unittest.main()
