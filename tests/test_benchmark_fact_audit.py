from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.benchmark_fact_audit import (
    build_fact_audit_rows,
    write_csv,
    write_markdown,
)
from tracebreak.experiments.run_condition import load_tasks


class BenchmarkFactAuditTests(unittest.TestCase):
    def test_audit_rows_cover_pairs_and_fact_visibility(self) -> None:
        rows = build_fact_audit_rows(load_tasks("data/tasks_tracebreak_120.jsonl"))
        by_category = {row["category"]: row for row in rows}
        self.assertEqual(
            set(by_category),
            {
                "aggregation_threshold",
                "approval_scope",
                "audience_restriction",
                "cross_tenant",
                "memory_laundering",
                "sensitive_external",
            },
        )

        for row in rows:
            self.assertEqual(row["risky_n"], 10)
            self.assertEqual(row["safe_n"], 10)
            self.assertEqual(row["pair_n"], 10)
            self.assertEqual(row["local_guard_has_fact"], "no")

        hidden_categories = {
            "audience_restriction",
            "cross_tenant",
            "memory_laundering",
            "sensitive_external",
        }
        for category in hidden_categories:
            row = by_category[category]
            self.assertEqual(row["visible_guard_has_fact"], "no")
            self.assertIn("hidden", row["fact_location"])

        for category in {"aggregation_threshold", "approval_scope"}:
            self.assertEqual(by_category[category]["visible_guard_has_fact"], "yes")

        self.assertEqual(by_category["aggregation_threshold"]["risk_safe_delta"], "aggregate_only")
        self.assertEqual(by_category["approval_scope"]["risk_safe_delta"], "recipient_id")
        self.assertEqual(by_category["audience_restriction"]["risk_safe_delta"], "recipient_id")
        self.assertEqual(by_category["cross_tenant"]["risk_safe_delta"], "customer_id")
        self.assertEqual(by_category["memory_laundering"]["risk_safe_delta"], "recipient_id")
        self.assertEqual(by_category["sensitive_external"]["risk_safe_delta"], "recipient_id")

    def test_writers_emit_reviewable_artifacts(self) -> None:
        rows = build_fact_audit_rows(load_tasks("data/tasks_tracebreak_120.jsonl"))
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "audit.csv"
            md_path = Path(tmpdir) / "audit.md"
            write_csv(rows, csv_path)
            write_markdown(rows, md_path)

            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            md_text = md_path.read_text(encoding="utf-8")

        self.assertEqual(len(csv_rows), 6)
        self.assertIn("visible_guard_has_fact", csv_rows[0])
        self.assertIn("Benchmark Policy-Fact Audit", md_text)
        self.assertIn("hidden source metadata", md_text)
        self.assertIn("10 risky/10 safe", md_text)


if __name__ == "__main__":
    unittest.main()
