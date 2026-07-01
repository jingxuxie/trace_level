from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.compute_metrics import read_runs
from tracebreak.analysis.policy_prompt_diagnostics import (
    summarize_policy_prompt,
    write_csv,
    write_latex,
    write_markdown,
)


RUNS = [
    "results/raw_traces/api_policy_prompt_gpt41mini_12.jsonl",
    "results/raw_traces/api_policy_prompt_gpt41mini_seed1_12.jsonl",
]


class PolicyPromptDiagnosticsTest(unittest.TestCase):
    def test_policy_prompt_diagnostic_counts_failure_modes(self) -> None:
        rows = summarize_policy_prompt(read_runs(RUNS))
        by_category = {row["category"]: row for row in rows}

        self.assertEqual(len(rows), 7)
        self.assertIn("overall", by_category)
        self.assertEqual(
            set(by_category) - {"overall"},
            {
                "aggregation_threshold",
                "approval_scope",
                "audience_restriction",
                "cross_tenant",
                "memory_laundering",
                "sensitive_external",
            },
        )

        approval = by_category["approval_scope"]
        self.assertEqual(approval["risky_violation_n"], 0)
        self.assertEqual(approval["risky_nonviolating_without_block_n"], 2)
        self.assertEqual(approval["safe_utility_n"], 0)
        self.assertEqual(approval["safe_lost_without_block_n"], 2)
        self.assertEqual(approval["final_answer_n"], 4)
        self.assertEqual(approval["dominant_prompt_outcome"], "abstains on risky and safe")

        cross_tenant = by_category["cross_tenant"]
        self.assertEqual(cross_tenant["risky_violation_n"], 1)
        self.assertEqual(cross_tenant["risky_nonviolating_without_block_n"], 1)
        self.assertEqual(cross_tenant["risky_no_sink_n"], 0)
        self.assertEqual(cross_tenant["safe_utility_n"], 2)
        self.assertEqual(
            cross_tenant["dominant_prompt_outcome"],
            "mixed risky behavior; completes safe",
        )

        overall = by_category["overall"]
        self.assertEqual(overall["risky_n"], 12)
        self.assertEqual(overall["safe_n"], 12)
        self.assertEqual(overall["risky_violation_n"], 9)
        self.assertEqual(overall["risky_nonviolating_without_block_n"], 3)
        self.assertEqual(overall["risky_violation_pct"], 75.0)
        self.assertEqual(overall["safe_utility_n"], 10)
        self.assertEqual(overall["safe_lost_without_block_n"], 2)
        self.assertEqual(overall["safe_utility_pct"], 83.3)
        self.assertEqual(overall["final_answer_n"], 4)

    def test_writers_emit_expected_policy_prompt_table(self) -> None:
        rows = summarize_policy_prompt(read_runs(RUNS))
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "diagnostic.csv"
            md_path = base / "diagnostic.md"
            tex_path = base / "diagnostic.tex"

            write_csv(rows, csv_path)
            write_markdown(rows, md_path)
            write_latex(rows, tex_path)

            self.assertIn("dominant_prompt_outcome", csv_path.read_text(encoding="utf-8"))
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Nonviolating/no-block", md_text)
            self.assertIn("approval scope", md_text)
            tex_text = tex_path.read_text(encoding="utf-8")
            self.assertIn("\\label{tab:policy-prompt-diagnostic}", tex_text)
            self.assertIn("overall & 9/12 & 3/12 & 10/12 & 2/12 & 4", tex_text)


if __name__ == "__main__":
    unittest.main()
