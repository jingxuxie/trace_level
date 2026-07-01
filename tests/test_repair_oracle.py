from __future__ import annotations

import json
import unittest
from pathlib import Path

from tracebreak.experiments.run_condition import load_tasks
from tracebreak.analysis.repair_oracle import repair_oracle_row


class RepairOracleTests(unittest.TestCase):
    def test_sensitive_external_oracle_changes_to_safe_recipient(self) -> None:
        task_by_id = {
            task["task_id"]: task for task in load_tasks("data/tasks_tracebreak_120.jsonl")
        }
        row = _first_row("results/raw_traces/api_traceguard_gpt41mini_12.jsonl")
        task = task_by_id[row["task_id"]]
        safe_task = task_by_id[task["safe_control_pair"]]

        repaired = repair_oracle_row(row, task=task, safe_task=safe_task)
        repair_event = repaired["trace"][-1]

        self.assertEqual(repaired["condition"], "api_traceguard_repair_oracle")
        self.assertEqual(repair_event["actor"], "repair_oracle")
        self.assertFalse(repair_event["blocked"], repaired)
        self.assertEqual(repair_event["arguments"]["recipient_id"], "person_nina_sales")
        self.assertTrue(repaired["metrics"]["oracle_repair_success"], repaired)
        self.assertFalse(repaired["metrics"]["global_violation"], repaired)

    def test_deterministic_rows_get_scripted_model_label(self) -> None:
        task_by_id = {
            task["task_id"]: task for task in load_tasks("data/tasks_tracebreak_120.jsonl")
        }
        row = _first_row("results/raw_traces/traceguard.jsonl")
        self.assertNotIn("model", row)
        task = task_by_id[row["task_id"]]
        safe_task = task_by_id[task["safe_control_pair"]]

        repaired = repair_oracle_row(row, task=task, safe_task=safe_task)

        self.assertEqual(repaired["model"], "scripted")
        self.assertTrue(repaired["run_id"].startswith("traceguard_repair_oracle_scripted_"))
        self.assertEqual(repaired["condition"], "traceguard_repair_oracle")
        self.assertTrue(repaired["metrics"]["oracle_repair_success"], repaired)

    def test_aggregation_oracle_aggregates_before_email(self) -> None:
        task_by_id = {
            task["task_id"]: task for task in load_tasks("data/tasks_tracebreak_120.jsonl")
        }
        row = _row_by_id(
            "results/raw_traces/traceguard.jsonl",
            "aggregation_threshold_000_risky",
        )
        task = task_by_id[row["task_id"]]
        safe_task = task_by_id[task["safe_control_pair"]]

        repaired = repair_oracle_row(row, task=task, safe_task=safe_task)
        aggregate_event = repaired["trace"][-2]
        email_event = repaired["trace"][-1]

        self.assertEqual(aggregate_event["action"], "aggregate_records")
        self.assertFalse(aggregate_event["blocked"], repaired)
        self.assertEqual(email_event["action"], "send_email")
        self.assertFalse(email_event["blocked"], repaired)
        self.assertEqual(email_event["arguments"]["source_refs"], [aggregate_event["output_ref"]])
        self.assertTrue(email_event["tag"]["aggregate_only"], repaired)
        self.assertTrue(repaired["metrics"]["oracle_repair_success"], repaired)
        self.assertEqual(repaired["metrics"]["repair_steps_used"], 2)


def _first_row(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.loads(next(handle))


def _row_by_id(path: str, task_id: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == task_id:
                return row
    raise KeyError(task_id)


if __name__ == "__main__":
    unittest.main()
