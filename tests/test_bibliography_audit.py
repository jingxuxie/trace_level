from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.bibliography_audit import (
    build_bibliography_audit_rows,
    write_csv,
    write_markdown,
)


class BibliographyAuditTests(unittest.TestCase):
    def test_current_paper_bibliography_is_consistent(self) -> None:
        rows = build_bibliography_audit_rows("paper")
        self.assertEqual(len(rows), 1)
        row = rows[0]

        self.assertTrue(row["pass"], row)
        self.assertEqual(row["undefined_keys"], "")
        self.assertEqual(row["duplicate_bib_keys"], "")
        self.assertEqual(row["stale_bbl_keys"], "")
        self.assertEqual(row["missing_bbl_keys"], "")
        self.assertEqual(row["stale_denied_keys"], "")
        self.assertEqual(row["invalid_arxiv_entries"], "")
        self.assertEqual(row["undefined_warning_sources"], "")
        self.assertEqual(row["cited_keys"], row["bbl_entries"])
        self.assertGreaterEqual(row["cited_keys"], 15)

    def test_audit_catches_missing_stale_and_invalid_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper = Path(tmpdir)
            (paper / "main.tex").write_text(
                "\\citep{missingkey,okkey,wang2026safeskillscollide}\n",
                encoding="utf-8",
            )
            (paper / "supplement.tex").write_text("", encoding="utf-8")
            (paper / "references.bib").write_text(
                """
@misc{okkey,
  title = {Okay},
  author = {A. Author},
  year = {2026},
  eprint = {bad-id},
  archivePrefix = {arXiv}
}
""",
                encoding="utf-8",
            )
            (paper / "main.bbl").write_text(
                "\\bibitem[]{okkey} x\n\\bibitem[]{staleonly} y\n",
                encoding="utf-8",
            )
            (paper / "main.log").write_text(
                "Package natbib Warning: Citation `missingkey' on page 1 undefined.\n",
                encoding="utf-8",
            )
            (paper / "main.blg").write_text(
                "Warning--I didn't find a database entry for \"missingkey\"\n",
                encoding="utf-8",
            )

            row = build_bibliography_audit_rows(paper)[0]

        self.assertFalse(row["pass"], row)
        self.assertIn("missingkey", row["undefined_keys"])
        self.assertIn("staleonly", row["stale_bbl_keys"])
        self.assertIn("missingkey", row["missing_bbl_keys"])
        self.assertIn("wang2026safeskillscollide", row["stale_denied_keys"])
        self.assertIn("okkey", row["invalid_arxiv_entries"])
        self.assertIn("main.log", row["undefined_warning_sources"])
        self.assertIn("main.blg", row["undefined_warning_sources"])

    def test_writers_emit_reviewable_artifacts(self) -> None:
        rows = build_bibliography_audit_rows("paper")
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "audit.csv"
            md_path = Path(tmpdir) / "audit.md"
            write_csv(rows, csv_path)
            write_markdown(rows, md_path)

            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            md_text = md_path.read_text(encoding="utf-8")

        self.assertEqual(len(csv_rows), 1)
        self.assertEqual(csv_rows[0]["pass"], "True")
        self.assertIn("Bibliography Integrity Audit", md_text)
        self.assertIn("malformed arXiv identifiers", md_text)
        self.assertIn("| 17 | 19 | 17 |", md_text)


if __name__ == "__main__":
    unittest.main()
