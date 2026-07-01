from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.compute_metrics import read_runs
from tracebreak.analysis.make_figures import (
    security_utility_points,
    write_security_utility_svg,
    write_security_utility_tikz,
)


class MakeFiguresTests(unittest.TestCase):
    def test_security_utility_frontier_uses_safe_utility_axis(self) -> None:
        rows = read_runs(
            [
                "results/raw_traces/api_local_gpt41mini_12.jsonl",
                "results/raw_traces/api_local_gpt41mini_seed1_12.jsonl",
                "results/raw_traces/api_dlp_gpt41mini_12.jsonl",
                "results/raw_traces/api_dlp_gpt41mini_seed1_12.jsonl",
                "results/raw_traces/api_policy_prompt_gpt41mini_12.jsonl",
                "results/raw_traces/api_policy_prompt_gpt41mini_seed1_12.jsonl",
                "results/raw_traces/api_traceguard_gpt41mini_12.jsonl",
                "results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl",
            ]
        )

        points = {row["condition"]: row for row in security_utility_points(rows)}
        self.assertEqual(points["api_traceguard"]["safe_utility_pct"], 100.0)
        self.assertEqual(points["api_traceguard"]["risky_violation_pct"], 0.0)
        self.assertEqual(points["api_local"]["safe_utility_pct"], 100.0)
        self.assertEqual(points["api_local"]["risky_violation_pct"], 100.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = Path(tmpdir) / "frontier.svg"
            tex_path = Path(tmpdir) / "frontier.tex"
            write_security_utility_svg(rows, svg_path)
            write_security_utility_tikz(rows, tex_path)

            svg = svg_path.read_text(encoding="utf-8")
            tex = tex_path.read_text(encoding="utf-8")

        self.assertIn("Safe utility (%)", svg)
        self.assertNotIn("Safe false-block rate", svg)
        self.assertIn("Security-utility frontier", tex)
        self.assertIn("\\label{fig:api-security-utility}", tex)


if __name__ == "__main__":
    unittest.main()
