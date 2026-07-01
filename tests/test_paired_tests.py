from __future__ import annotations

import unittest

from tracebreak.analysis.compute_metrics import read_runs
from tracebreak.analysis.paired_tests import (
    Comparison,
    exact_binomial_improvement_p,
    exact_binomial_two_sided,
    summarize_pairs,
)


class PairedTests(unittest.TestCase):
    def test_exact_binomial_handles_all_improvements(self) -> None:
        self.assertAlmostEqual(exact_binomial_two_sided(12, 0), 0.00048828125)
        self.assertAlmostEqual(exact_binomial_improvement_p(12, 0), 0.000244140625)

    def test_api_local_to_traceguard_matched_risky_violations(self) -> None:
        rows = read_runs(
            [
                "results/raw_traces/api_local_gpt41mini_12.jsonl",
                "results/raw_traces/api_local_gpt41mini_seed1_12.jsonl",
                "results/raw_traces/api_traceguard_gpt41mini_12.jsonl",
                "results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl",
            ]
        )
        summary = summarize_pairs(
            rows,
            [Comparison("api_local", "api_traceguard", "local vs TraceGuard")],
        )
        violation = _find(summary, "Risky violation")
        self.assertEqual(violation["n_matched"], 12)
        self.assertEqual(violation["baseline_rate_pct"], 100.0)
        self.assertEqual(violation["comparator_rate_pct"], 0.0)
        self.assertEqual(violation["improvements"], 12)
        self.assertEqual(violation["regressions"], 0)
        self.assertEqual(violation["ties"], 0)
        self.assertEqual(violation["exact_p_two_sided"], "0.000488")

        safe_utility = _find(summary, "Safe utility")
        self.assertEqual(safe_utility["n_matched"], 12)
        self.assertEqual(safe_utility["baseline_rate_pct"], 100.0)
        self.assertEqual(safe_utility["comparator_rate_pct"], 100.0)
        self.assertEqual(safe_utility["improvements"], 0)
        self.assertEqual(safe_utility["regressions"], 0)
        self.assertEqual(safe_utility["ties"], 12)
        self.assertEqual(safe_utility["exact_p_two_sided"], "1")

    def test_visible_policy_to_metadata_critic_matched_risky_violations(self) -> None:
        rows = read_runs(
            [
                "results/raw_traces/api_local_replay_visible_policy_gpt41mini_24.jsonl",
                "results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl",
            ]
        )
        summary = summarize_pairs(
            rows,
            [
                Comparison(
                    "api_local_replay_visible_policy",
                    "api_local_replay_metadata_critic",
                    "visible vs metadata",
                )
            ],
        )
        violation = _find(summary, "Risky violation")
        self.assertEqual(violation["n_matched"], 12)
        self.assertEqual(violation["baseline_rate_pct"], 66.667)
        self.assertEqual(violation["comparator_rate_pct"], 0.0)
        self.assertEqual(violation["improvements"], 8)
        self.assertEqual(violation["regressions"], 0)
        self.assertEqual(violation["ties"], 4)
        self.assertEqual(violation["exact_p_two_sided"], "0.0078")

    def test_metadata_critic_ties_traceguard_on_same_actions(self) -> None:
        rows = read_runs(
            [
                "results/raw_traces/api_local_replay_metadata_critic_gpt41mini_24.jsonl",
                "results/raw_traces/api_local_replay_traceguard_gpt41mini_24.jsonl",
            ]
        )
        summary = summarize_pairs(
            rows,
            [
                Comparison(
                    "api_local_replay_metadata_critic",
                    "api_local_replay_traceguard",
                    "metadata vs TraceGuard",
                )
            ],
        )
        violation = _find(summary, "Risky violation")
        self.assertEqual(violation["baseline_rate_pct"], 0.0)
        self.assertEqual(violation["comparator_rate_pct"], 0.0)
        self.assertEqual(violation["ties"], 12)
        self.assertEqual(violation["exact_p_two_sided"], "1")


def _find(rows: list[dict], metric: str) -> dict:
    for row in rows:
        if row["metric"] == metric:
            return row
    raise AssertionError(f"missing metric {metric}")


if __name__ == "__main__":
    unittest.main()
