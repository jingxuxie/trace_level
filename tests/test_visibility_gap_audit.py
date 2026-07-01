from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.compute_metrics import read_runs
from tracebreak.analysis.visibility_gap_audit import (
    summarize_visibility_gap,
    write_csv,
    write_latex,
    write_markdown,
)


RUNS = [
    "results/raw_traces/api_local_replay_visible_policy_gpt41mini_24.jsonl",
    "results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl",
    "results/raw_traces/api_local_replay_traceguard_gpt41mini_24.jsonl",
]


class VisibilityGapAuditTest(unittest.TestCase):
    def test_visibility_gap_separates_visible_and_hidden_policy_facts(self) -> None:
        rows = summarize_visibility_gap(read_runs(RUNS))
        by_category = {row["category"]: row for row in rows}

        self.assertEqual(len(rows), 7)
        for category in ["aggregation_threshold", "approval_scope"]:
            row = by_category[category]
            self.assertEqual(row["risky_n"], 2)
            self.assertEqual(row["safe_n"], 2)
            self.assertEqual(row["visible_policy_block_n"], 2)
            self.assertEqual(row["visible_policy_violation_n"], 0)
            self.assertEqual(row["metadata_critic_block_n"], 2)
            self.assertEqual(row["traceguard_block_n"], 2)

        for category in [
            "audience_restriction",
            "cross_tenant",
            "memory_laundering",
            "sensitive_external",
        ]:
            row = by_category[category]
            self.assertIn("hidden", row["decisive_fact"])
            self.assertEqual(row["risky_n"], 2)
            self.assertEqual(row["visible_policy_block_n"], 0)
            self.assertEqual(row["visible_policy_violation_n"], 2)
            self.assertEqual(row["metadata_critic_block_n"], 2)
            self.assertEqual(row["traceguard_block_n"], 2)
            self.assertEqual(row["visible_policy_safe_utility_n"], 2)
            self.assertEqual(row["metadata_critic_safe_utility_n"], 2)
            self.assertEqual(row["traceguard_safe_utility_n"], 2)

        overall = by_category["overall"]
        self.assertEqual(overall["risky_n"], 12)
        self.assertEqual(overall["visible_policy_block_n"], 4)
        self.assertEqual(overall["visible_policy_violation_n"], 8)
        self.assertEqual(overall["metadata_critic_block_n"], 12)
        self.assertEqual(overall["metadata_critic_violation_n"], 0)
        self.assertEqual(overall["traceguard_block_n"], 12)
        self.assertEqual(overall["traceguard_violation_n"], 0)
        self.assertEqual(overall["visible_policy_safe_utility_n"], 12)
        self.assertEqual(overall["metadata_critic_safe_utility_n"], 12)
        self.assertEqual(overall["traceguard_safe_utility_n"], 12)

    def test_writers_emit_visibility_gap_audit(self) -> None:
        rows = summarize_visibility_gap(read_runs(RUNS))
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "audit.csv"
            md_path = base / "audit.md"
            tex_path = base / "audit.tex"

            write_csv(rows, csv_path)
            write_markdown(rows, md_path)
            write_latex(rows, tex_path)

            self.assertIn("visible_policy_violation_n", csv_path.read_text(encoding="utf-8"))
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Same-Action Visibility-Gap Audit", md_text)
            self.assertIn("hidden source tenant tag", md_text)
            tex_text = tex_path.read_text(encoding="utf-8")
            self.assertIn("\\label{tab:visibility-gap-audit}", tex_text)
            self.assertIn("overall & visible subset + hidden metadata & 4/12 & 8/12 & 12/12 & 12/12", tex_text)


if __name__ == "__main__":
    unittest.main()
