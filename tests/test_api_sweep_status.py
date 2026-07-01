from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.api_sweep_status import (
    model_slug,
    planned_result_path,
    summarize_sweep,
)
from tracebreak.analysis.estimate_api_cost import Price
from tracebreak.data.generate_tasks import generate
from tracebreak.experiments.run_api_condition import condition_label


class ApiSweepStatusTests(unittest.TestCase):
    def test_model_slug_matches_existing_file_convention(self) -> None:
        self.assertEqual(model_slug("gpt-5.4-mini"), "gpt54mini")
        self.assertEqual(model_slug("gpt-5.5"), "gpt55")
        self.assertEqual(model_slug("gpt-4.1-mini"), "gpt41mini")

    def test_planned_result_path_includes_modes_and_offset(self) -> None:
        path = planned_result_path(
            "results/raw_traces",
            condition="api_traceguard",
            model="gpt-5.4-mini",
            limit=12,
            offset=24,
            source_ref_mode="drop_at_sink",
            recovery_mode="after_block",
        )
        self.assertEqual(
            str(path),
            "results/raw_traces/api_traceguard_drop_at_sink_recover_gpt54mini_offset24_12.jsonl",
        )

    def test_summarize_sweep_counts_completed_and_remaining_cost(self) -> None:
        tasks = list(generate(num_seeds=1, first_seed=100))[:2]
        with tempfile.TemporaryDirectory() as tmpdir:
            result_path = planned_result_path(
                tmpdir,
                condition="api_traceguard",
                model="gpt-5.4-mini",
                limit=2,
                offset=0,
                source_ref_mode="cooperative",
                recovery_mode="stop",
            )
            result_path.write_text(
                json.dumps(
                    _completed_row(
                        tasks[0],
                        condition="api_traceguard",
                        model="gpt-5.4-mini",
                    ),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            rows = summarize_sweep(
                tasks,
                tasks_path="custom_tasks.jsonl",
                conditions=["api_traceguard"],
                models=["gpt-5.4-mini"],
                results_dir=tmpdir,
                api_key_path="../apikey.txt",
                api_mode="chat",
                cache_dir="results/api_cache",
                max_steps=8,
                recovery_mode="stop",
                recovery_steps=3,
                source_ref_mode="cooperative",
                max_output_tokens=100,
                chars_per_token=3.5,
                prices={"gpt-5.4-mini": Price(1.0, 2.0)},
                offset=0,
                limit=2,
            )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["expected"], 2)
        self.assertEqual(row["completed"], 1)
        self.assertEqual(row["missing"], 1)
        self.assertEqual(row["parse_errors"], 1)
        self.assertEqual(row["prompt_tokens"], 100)
        self.assertEqual(row["completion_tokens"], 20)
        self.assertGreater(row["remaining_nominal_cost_usd"], 0)
        self.assertEqual(row["api_mode"], "chat")
        self.assertIn("--api-mode chat", row["run_command"])
        self.assertIn("--resume", row["run_command"])
        self.assertIn("--max-estimated-cost-usd", row["run_command"])
        self.assertIn("custom_tasks.jsonl", row["run_command"])


def _completed_row(task: dict, *, condition: str, model: str) -> dict:
    return {
        "run_id": f"{condition}_{model}_{task['task_id']}",
        "condition": condition_label(condition, "cooperative", "stop"),
        "base_condition": condition,
        "source_ref_mode": "cooperative",
        "recovery_mode": "stop",
        "recovery_steps": 3,
        "model": model,
        "task_id": task["task_id"],
        "category": task["category"],
        "risk_label": task["risk_label"],
        "world_seed": task["world_seed"],
        "trace": [],
        "visible_trace": [],
        "metrics": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "parse_errors": 1,
        },
    }


if __name__ == "__main__":
    unittest.main()
