from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.claim_boundary_audit import (
    build_claim_boundary_rows,
    write_csv,
    write_markdown,
)


class ClaimBoundaryAuditTests(unittest.TestCase):
    def test_current_paper_boundaries_are_explicit(self) -> None:
        rows = build_claim_boundary_rows(".")
        by_boundary = {row["boundary"]: row for row in rows}
        self.assertEqual(
            set(by_boundary),
            {
                "api_subset_scope",
                "api_preliminary_not_leaderboard",
                "synthetic_no_real_services",
                "provenance_dependency",
                "live_recovery_future_work",
                "modern_model_rows_missing",
            },
        )
        for row in rows:
            self.assertTrue(row["pass"], row)
            self.assertEqual(row["missing_phrases"], 0, row)
            self.assertEqual(row["missing"], "")

    def test_audit_catches_missing_boundary_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "paper").mkdir()
            (root / "results/tables").mkdir(parents=True)
            (root / "paper/main.tex").write_text(
                "API results are preliminary evidence, not a model leaderboard\n",
                encoding="utf-8",
            )
            (root / "results/tables/research_readiness_report.md").write_text(
                "Modern-model evidence remains incomplete until paid API rows exist\n",
                encoding="utf-8",
            )
            rows = build_claim_boundary_rows(root)

        failing = [row for row in rows if not row["pass"]]
        self.assertGreaterEqual(len(failing), 5)
        by_boundary = {row["boundary"]: row for row in rows}
        self.assertIn("24-task API subset", by_boundary["api_subset_scope"]["missing"])
        self.assertIn("gpt-5.4-mini 120-task sweep", by_boundary["modern_model_rows_missing"]["missing"])

    def test_writers_emit_reviewable_artifacts(self) -> None:
        rows = build_claim_boundary_rows(".")
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "audit.csv"
            md_path = Path(tmpdir) / "audit.md"
            write_csv(rows, csv_path)
            write_markdown(rows, md_path)

            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            md_text = md_path.read_text(encoding="utf-8")

        self.assertEqual(len(csv_rows), 6)
        self.assertEqual({row["pass"] for row in csv_rows}, {"True"})
        self.assertIn("Claim Boundary Audit", md_text)
        self.assertIn("preliminary-model scope", md_text)
        self.assertIn("| modern_model_rows_missing |", md_text)


if __name__ == "__main__":
    unittest.main()
