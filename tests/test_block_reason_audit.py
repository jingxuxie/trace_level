from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.block_reason_audit import (
    EXPECTED_REASON_BY_CATEGORY,
    summarize_reason_audit,
    write_csv,
    write_latex,
    write_markdown,
)
from tracebreak.analysis.compute_metrics import read_runs


DET_RUNS = ["results/raw_traces/traceguard.jsonl"]
API_RUNS = [
    "results/raw_traces/api_traceguard_gpt41mini_12.jsonl",
    "results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl",
]


class BlockReasonAuditTest(unittest.TestCase):
    def test_traceguard_block_reasons_align_by_category(self) -> None:
        rows = summarize_reason_audit(
            [
                ("deterministic 120", read_runs(DET_RUNS)),
                ("API gpt-4.1-mini 24", read_runs(API_RUNS)),
            ]
        )
        by_key = {(row["evaluation"], row["category"]): row for row in rows}

        self.assertEqual(len(rows), 14)
        for category, reason in EXPECTED_REASON_BY_CATEGORY.items():
            det = by_key[("deterministic 120", category)]
            self.assertEqual(det["risky_n"], 10)
            self.assertEqual(det["safe_n"], 10)
            self.assertEqual(det["expected_reason"], reason)
            self.assertEqual(det["risky_blocks_n"], 10)
            self.assertEqual(det["expected_reason_blocks_n"], 10)
            self.assertEqual(det["unexpected_reason_blocks_n"], 0)
            self.assertEqual(det["safe_blocks_n"], 0)

            api = by_key[("API gpt-4.1-mini 24", category)]
            self.assertEqual(api["risky_n"], 2)
            self.assertEqual(api["safe_n"], 2)
            self.assertEqual(api["expected_reason"], reason)
            self.assertEqual(api["risky_blocks_n"], 2)
            self.assertEqual(api["expected_reason_blocks_n"], 2)
            self.assertEqual(api["unexpected_reason_blocks_n"], 0)
            self.assertEqual(api["safe_blocks_n"], 0)

        det_overall = by_key[("deterministic 120", "overall")]
        self.assertEqual(det_overall["risky_blocks_n"], 60)
        self.assertEqual(det_overall["expected_reason_blocks_n"], 60)
        self.assertEqual(det_overall["unexpected_reason_blocks_n"], 0)
        self.assertEqual(det_overall["safe_blocks_n"], 0)

        api_overall = by_key[("API gpt-4.1-mini 24", "overall")]
        self.assertEqual(api_overall["risky_blocks_n"], 12)
        self.assertEqual(api_overall["expected_reason_blocks_n"], 12)
        self.assertEqual(api_overall["unexpected_reason_blocks_n"], 0)
        self.assertEqual(api_overall["safe_blocks_n"], 0)

    def test_writers_emit_block_reason_audit(self) -> None:
        rows = summarize_reason_audit(
            [
                ("deterministic 120", read_runs(DET_RUNS)),
                ("API gpt-4.1-mini 24", read_runs(API_RUNS)),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "audit.csv"
            md_path = base / "audit.md"
            tex_path = base / "audit.tex"

            write_csv(rows, csv_path)
            write_markdown(rows, md_path)
            write_latex(rows, tex_path)

            self.assertIn("expected_reason_blocks_n", csv_path.read_text(encoding="utf-8"))
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("TraceGuard Block-Reason Audit", md_text)
            self.assertIn("external recipient", md_text)
            tex_text = tex_path.read_text(encoding="utf-8")
            self.assertIn("\\label{tab:block-reason-audit}", tex_text)
            self.assertIn("sensitive external & external recipient & 10/10 & 2/2", tex_text)


if __name__ == "__main__":
    unittest.main()
