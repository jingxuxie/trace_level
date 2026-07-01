from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.modern_sweep_launch_audit import (
    audit_launch_rows,
    read_status_rows,
    write_csv,
    write_markdown,
)


STATUS_FILES = [
    "results/api_gpt54mini_120_sweep_status.csv",
    "results/api_gpt55_48_sweep_status.csv",
    "results/api_gpt54mini_120_plus_visible_sweep_status.csv",
    "results/api_gpt55_48_plus_visible_sweep_status.csv",
]


class ModernSweepLaunchAuditTests(unittest.TestCase):
    def test_generated_sweep_commands_are_launch_ready(self) -> None:
        rows = audit_launch_rows(read_status_rows(STATUS_FILES))
        self.assertEqual(len(rows), 18)
        self.assertTrue(all(row["launch_ready"] == "yes" for row in rows))
        self.assertTrue(all(row["api_mode_ok"] == "yes" for row in rows))
        self.assertTrue(all(row["resume_ok"] == "yes" for row in rows))
        self.assertTrue(all(row["cache_dir_ok"] == "yes" for row in rows))
        self.assertTrue(all(row["api_key_path_ok"] == "yes" for row in rows))
        self.assertTrue(all(row["source_ref_mode_ok"] == "yes" for row in rows))
        self.assertTrue(all(row["budget_cap_ok"] == "yes" for row in rows))
        self.assertIn(
            "api_visible_policy",
            {row["condition"] for row in rows if "plus_visible" in row["sweep_file"]},
        )

    def test_writers_emit_launch_audit(self) -> None:
        rows = audit_launch_rows(read_status_rows(STATUS_FILES))
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "launch.csv"
            md_path = Path(tmpdir) / "launch.md"
            write_csv(rows, csv_path)
            write_markdown(rows, md_path)

            csv_text = csv_path.read_text(encoding="utf-8")
            md_text = md_path.read_text(encoding="utf-8")

        self.assertIn("launch_ready", csv_text)
        self.assertIn("Modern Sweep Launch Audit", md_text)
        self.assertIn("Launch-ready commands: 18/18", md_text)


if __name__ == "__main__":
    unittest.main()
