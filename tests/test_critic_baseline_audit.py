from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.compute_metrics import read_runs
from tracebreak.analysis.critic_baseline_audit import (
    summarize_critic_baseline,
    write_csv,
    write_markdown,
)


RUNS = [
    "results/raw_traces/api_local_gpt41mini_12.jsonl",
    "results/raw_traces/api_local_gpt41mini_seed1_12.jsonl",
    "results/raw_traces/api_local_replay_visible_policy_gpt41mini_24.jsonl",
    "results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl",
    "results/raw_traces/api_local_replay_traceguard_gpt41mini_24.jsonl",
]


class CriticBaselineAuditTests(unittest.TestCase):
    def test_critic_baseline_separates_visible_and_metadata_guards(self) -> None:
        rows = summarize_critic_baseline(read_runs(RUNS))
        by_category = {row["category"]: row for row in rows}

        self.assertEqual(len(rows), 7)
        overall = by_category["overall"]
        self.assertEqual(overall["proposed_sink_reviews"], 24)
        self.assertEqual(overall["base_model_calls"], 123)
        self.assertEqual(overall["review_call_overhead_pct"], 19.5)
        self.assertEqual(overall["visible_critic_proxy_block_n"], 4)
        self.assertEqual(overall["visible_critic_proxy_violation_n"], 8)
        self.assertEqual(overall["metadata_critic_block_n"], 12)
        self.assertEqual(overall["metadata_critic_violation_n"], 0)
        self.assertEqual(overall["traceguard_block_n"], 12)
        self.assertEqual(overall["traceguard_violation_n"], 0)
        self.assertEqual(overall["metadata_critic_safe_utility_n"], 12)
        self.assertEqual(overall["traceguard_safe_utility_n"], 12)

        for category in ["aggregation_threshold", "approval_scope"]:
            row = by_category[category]
            self.assertEqual(row["hidden_metadata_needed"], "no")
            self.assertEqual(row["visible_critic_proxy_block_n"], 2)
            self.assertEqual(row["visible_critic_proxy_violation_n"], 0)

        for category in [
            "audience_restriction",
            "cross_tenant",
            "memory_laundering",
            "sensitive_external",
        ]:
            row = by_category[category]
            self.assertEqual(row["hidden_metadata_needed"], "yes")
            self.assertEqual(row["visible_critic_proxy_block_n"], 0)
            self.assertEqual(row["visible_critic_proxy_violation_n"], 2)
            self.assertEqual(row["metadata_critic_block_n"], 2)
            self.assertEqual(row["traceguard_block_n"], 2)

    def test_writers_emit_critic_audit(self) -> None:
        rows = summarize_critic_baseline(read_runs(RUNS))
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "critic.csv"
            md_path = Path(tmpdir) / "critic.md"
            write_csv(rows, csv_path)
            write_markdown(rows, md_path)

            csv_text = csv_path.read_text(encoding="utf-8")
            md_text = md_path.read_text(encoding="utf-8")

        self.assertIn("review_call_overhead_pct", csv_text)
        self.assertIn("Same-Action Critic Baseline Audit", md_text)
        self.assertIn("visible-critic proxy", md_text)
        self.assertIn("24 extra sink-review calls", md_text)


if __name__ == "__main__":
    unittest.main()
