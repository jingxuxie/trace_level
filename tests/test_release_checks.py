from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.run_release_checks import (
    REQUIRED_BUNDLE_ENTRIES,
    find_latex_log_problems,
    inspect_bundle,
)


class ReleaseChecksTests(unittest.TestCase):
    def test_latex_log_scanner_accepts_clean_warning_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "main.log"
            log_path.write_text(
                "LaTeX Warning: `h' float specifier changed to `ht'.\n"
                "Underfull \\hbox (badness 10000) in paragraph.\n",
                encoding="utf-8",
            )
            self.assertEqual(find_latex_log_problems([log_path]), [])

    def test_latex_log_scanner_flags_hard_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "main.log"
            log_path.write_text(
                "! Undefined control sequence.\n"
                "LaTeX Warning: Citation `missing' on page 1 undefined.\n",
                encoding="utf-8",
            )
            problems = find_latex_log_problems([log_path])
        self.assertEqual(len(problems), 2)
        self.assertIn("Undefined control sequence", problems[0])
        self.assertIn("Citation", problems[1])

    def test_bundle_inspection_reports_missing_and_forbidden_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir) / "bundle.zip"
            with zipfile.ZipFile(bundle, mode="w") as zf:
                for name in sorted(
                    REQUIRED_BUNDLE_ENTRIES - {"paper/main.pdf", "paper/related_work_notes.md"}
                ):
                    zf.writestr(name, "")
                zf.writestr("results/api_cache/cached.json", "{}")

            missing, forbidden = inspect_bundle(bundle)

        self.assertEqual(missing, ["paper/main.pdf", "paper/related_work_notes.md"])
        self.assertEqual(forbidden, ["results/api_cache/cached.json"])


if __name__ == "__main__":
    unittest.main()
