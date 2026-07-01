from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.compute_metrics import read_runs
from tracebreak.analysis.source_ref_compliance import (
    summarize_source_ref_compliance,
    write_csv,
    write_latex,
    write_markdown,
)


RUNS = [
    "results/raw_traces/api_local_gpt41mini_12.jsonl",
    "results/raw_traces/api_local_gpt41mini_seed1_12.jsonl",
    "results/raw_traces/api_dlp_gpt41mini_12.jsonl",
    "results/raw_traces/api_dlp_gpt41mini_seed1_12.jsonl",
    "results/raw_traces/api_policy_prompt_gpt41mini_12.jsonl",
    "results/raw_traces/api_policy_prompt_gpt41mini_seed1_12.jsonl",
    "results/raw_traces/api_traceguard_gpt41mini_12.jsonl",
    "results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl",
]


class SourceRefComplianceTest(unittest.TestCase):
    def test_cached_api_sinks_have_valid_nonempty_source_refs(self) -> None:
        rows = summarize_source_ref_compliance(read_runs(RUNS))
        by_condition = {row["condition"]: row for row in rows}

        self.assertEqual(len(rows), 5)
        for condition in ["api_local", "api_dlp", "api_policy_prompt", "api_traceguard"]:
            row = by_condition[condition]
            self.assertEqual(row["n"], 24)
            self.assertEqual(row["sink_valid_nonempty_refs"], row["sink_rows"])
            self.assertEqual(row["source_ref_compliance_pct"], 100.0)
            self.assertEqual(row["sink_missing_refs"], 0)
            self.assertEqual(row["sink_empty_refs"], 0)
            self.assertEqual(row["sink_malformed_refs"], 0)
            self.assertEqual(row["sink_invalid_ref_events"], 0)
            self.assertEqual(row["invalid_ref_count"], 0)

        self.assertEqual(by_condition["api_local"]["sink_rows"], 24)
        self.assertEqual(by_condition["api_dlp"]["sink_rows"], 24)
        self.assertEqual(by_condition["api_policy_prompt"]["sink_rows"], 20)
        self.assertEqual(by_condition["api_policy_prompt"]["final_answer_rows"], 4)
        self.assertEqual(by_condition["api_traceguard"]["sink_rows"], 24)
        self.assertEqual(by_condition["api_traceguard"]["blocked_sink_rows"], 12)

        overall = by_condition["overall"]
        self.assertEqual(overall["n"], 96)
        self.assertEqual(overall["sink_rows"], 92)
        self.assertEqual(overall["sink_valid_nonempty_refs"], 92)
        self.assertEqual(overall["final_answer_rows"], 4)
        self.assertEqual(overall["blocked_sink_rows"], 12)
        self.assertEqual(overall["source_ref_compliance_pct"], 100.0)

    def test_writers_emit_source_ref_compliance_audit(self) -> None:
        rows = summarize_source_ref_compliance(read_runs(RUNS))
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "audit.csv"
            md_path = base / "audit.md"
            tex_path = base / "audit.tex"

            write_csv(rows, csv_path)
            write_markdown(rows, md_path)
            write_latex(rows, tex_path)

            self.assertIn("source_ref_compliance_pct", csv_path.read_text(encoding="utf-8"))
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("API Source-Reference Compliance Audit", md_text)
            self.assertIn("| Policy prompt | 24 | 20 | 20/20 | 100.0 |", md_text)
            tex_text = tex_path.read_text(encoding="utf-8")
            self.assertIn("\\label{tab:source-ref-compliance}", tex_text)
            self.assertIn("Overall & 96 & 92 & 92/92", tex_text)


if __name__ == "__main__":
    unittest.main()
