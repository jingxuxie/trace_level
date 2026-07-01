from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.research_readiness import (
    build_readiness_rows,
    write_csv,
    write_markdown,
)


class ResearchReadinessTest(unittest.TestCase):
    def test_minimum_package_readiness_marks_modern_sweeps_incomplete(self) -> None:
        rows = build_readiness_rows(Path("."))
        by_item = {row["item"]: row for row in rows}

        self.assertEqual(
            by_item["gpt-5.4-mini 120-task sweep"]["status"],
            "blocked_on_paid_api",
        )
        self.assertEqual(by_item["gpt-5.4-mini 120-task sweep"]["completed"], 0)
        self.assertEqual(by_item["gpt-5.4-mini 120-task sweep"]["expected"], 480)
        self.assertEqual(
            by_item["gpt-5.5 48-task sweep"]["status"],
            "blocked_on_paid_api",
        )
        self.assertEqual(by_item["gpt-5.5 48-task sweep"]["completed"], 0)
        self.assertEqual(by_item["gpt-5.5 48-task sweep"]["expected"], 192)

        for item in [
            "source-reference robustness",
            "category-level reporting",
            "paper and bundle validation",
        ]:
            self.assertEqual(by_item[item]["status"], "complete", by_item[item])
        self.assertIn(
            "scripts/run_release_checks.py",
            by_item["paper and bundle validation"]["next_action"],
        )
        self.assertEqual(by_item["paid smoke preflight"]["status"], "complete")
        self.assertEqual(by_item["paid smoke preflight"]["completed"], 4)
        self.assertEqual(by_item["paid smoke preflight"]["expected"], 4)
        self.assertEqual(
            by_item["multi-agent topology 24-task status"]["status"],
            "blocked_on_paid_api",
        )
        self.assertFalse(by_item["multi-agent topology 24-task status"]["minimum_package"])
        self.assertEqual(by_item["multi-agent topology 24-task status"]["completed"], 0)
        self.assertEqual(by_item["multi-agent topology 24-task status"]["expected"], 96)

        for item in [
            "prompt-surface and recovery audits",
            "critic and replay baselines",
            "deterministic stress tests",
            "bibliography integrity audit",
            "claim-boundary audit",
        ]:
            self.assertEqual(by_item[item]["status"], "complete", by_item[item])
            self.assertFalse(by_item[item]["minimum_package"])
            self.assertEqual(by_item[item]["completed"], by_item[item]["expected"])

        minimum_rows = [row for row in rows if row["minimum_package"]]
        self.assertEqual(sum(row["status"] == "complete" for row in minimum_rows), 3)
        self.assertEqual(len(minimum_rows), 5)

    def test_writers_emit_readiness_report(self) -> None:
        rows = build_readiness_rows(Path("."))
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "readiness.csv"
            md_path = base / "readiness.md"

            write_csv(rows, csv_path)
            write_markdown(rows, md_path)

            self.assertIn("blocked_on_paid_api", csv_path.read_text(encoding="utf-8"))
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Research Readiness Report", md_text)
            self.assertIn("Minimum package status: 3/5 items complete", md_text)
            self.assertIn("| gpt-5.4-mini 120-task sweep | yes | blocked_on_paid_api | 0/480 |", md_text)
            self.assertIn("| prompt-surface and recovery audits | no | complete | 4/4 |", md_text)
            self.assertIn("| bibliography integrity audit | no | complete | 2/2 |", md_text)
            self.assertIn("| claim-boundary audit | no | complete | 2/2 |", md_text)
            self.assertIn("| multi-agent topology 24-task status | no | blocked_on_paid_api | 0/96 |", md_text)

    def test_followup_plan_uses_guarded_paid_commands(self) -> None:
        plan = Path("additional_experiments_plan.md").read_text(encoding="utf-8")
        command_section = plan.split("#### Commands", maxsplit=1)[1].split(
            "#### What to report",
            maxsplit=1,
        )[0]

        self.assertIn("--max-estimated-cost-usd 0.02", plan)
        self.assertIn("--max-actual-cost-usd 0.02", plan)
        self.assertIn("results/tables/api_gpt54mini_120_sweep_status.md", plan)
        self.assertIn("results/tables/api_gpt55_48_sweep_status.md", plan)
        self.assertIn("results/api_cache", plan)
        self.assertIn("--resume", plan)
        self.assertNotIn("for condition in", command_section)
        self.assertNotIn("--model gpt-5.5", command_section)


if __name__ == "__main__":
    unittest.main()
