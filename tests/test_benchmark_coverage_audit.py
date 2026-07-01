from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.benchmark_coverage_audit import (
    build_coverage_rows,
    write_csv,
    write_markdown,
)
from tracebreak.experiments.run_condition import load_tasks


class BenchmarkCoverageAuditTests(unittest.TestCase):
    def test_coverage_rows_capture_benchmark_structure(self) -> None:
        rows = build_coverage_rows(load_tasks("data/tasks_tracebreak_120.jsonl"))
        by_category = {row["category"]: row for row in rows}

        self.assertEqual(len(rows), 7)
        overall = by_category["overall"]
        self.assertEqual(overall["task_n"], 120)
        self.assertEqual(overall["risky_n"], 60)
        self.assertEqual(overall["safe_n"], 60)
        self.assertEqual(overall["complete_pair_n"], 60)
        self.assertEqual(overall["world_seed_n"], 10)
        self.assertEqual(overall["sink_tool_counts"], "post_ticket=20; send_email=100")
        self.assertEqual(overall["visible_fact_task_n"], 40)
        self.assertEqual(overall["hidden_fact_task_n"], 80)
        self.assertEqual(overall["scripted_step_min"], 2)
        self.assertEqual(overall["scripted_step_max"], 11)

        for category in [
            "aggregation_threshold",
            "approval_scope",
            "audience_restriction",
            "cross_tenant",
            "memory_laundering",
            "sensitive_external",
        ]:
            row = by_category[category]
            self.assertEqual(row["task_n"], 20)
            self.assertEqual(row["risky_n"], 10)
            self.assertEqual(row["safe_n"], 10)
            self.assertEqual(row["complete_pair_n"], 10)
            self.assertEqual(row["world_seed_n"], 10)

        self.assertEqual(by_category["cross_tenant"]["sink_tool_counts"], "post_ticket=20")
        self.assertEqual(by_category["cross_tenant"]["fact_visibility"], "hidden")
        self.assertEqual(by_category["aggregation_threshold"]["fact_visibility"], "visible")
        self.assertEqual(by_category["aggregation_threshold"]["source_object_min"], 8)
        self.assertEqual(by_category["aggregation_threshold"]["source_object_max"], 8)
        self.assertEqual(by_category["aggregation_threshold"]["scripted_step_min"], 10)
        self.assertEqual(by_category["aggregation_threshold"]["scripted_step_max"], 11)
        self.assertEqual(by_category["approval_scope"]["source_object_min"], 2)
        self.assertEqual(by_category["approval_scope"]["source_object_max"], 2)

    def test_writers_emit_coverage_artifacts(self) -> None:
        rows = build_coverage_rows(load_tasks("data/tasks_tracebreak_120.jsonl"))
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "coverage.csv"
            md_path = Path(tmpdir) / "coverage.md"
            write_csv(rows, csv_path)
            write_markdown(rows, md_path)

            csv_text = csv_path.read_text(encoding="utf-8")
            md_text = md_path.read_text(encoding="utf-8")

        self.assertIn("hidden_fact_task_n", csv_text)
        self.assertIn("Benchmark Coverage Audit", md_text)
        self.assertIn("120 tasks over 10 seeds", md_text)
        self.assertIn("post_ticket=20; send_email=100", md_text)


if __name__ == "__main__":
    unittest.main()
