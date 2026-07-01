from __future__ import annotations

import unittest

from tracebreak.analysis.category_examples import (
    EXPECTED_CATEGORIES,
    build_category_examples,
)
from tracebreak.analysis.compute_metrics import read_runs


class CategoryExampleTests(unittest.TestCase):
    def test_examples_cover_all_categories_with_guarded_blocks(self) -> None:
        rows = build_category_examples(
            read_runs(
                [
                    "results/raw_traces/api_local_gpt41mini_12.jsonl",
                    "results/raw_traces/api_local_gpt41mini_seed1_12.jsonl",
                    "results/raw_traces/api_traceguard_gpt41mini_12.jsonl",
                    "results/raw_traces/api_traceguard_gpt41mini_seed1_12.jsonl",
                ]
            )
        )

        self.assertEqual([row["category"] for row in rows], list(EXPECTED_CATEGORIES))
        self.assertTrue(
            all("global violation" in row["local_result"] for row in rows),
            rows,
        )
        self.assertTrue(
            all("blocked" in row["traceguard_result"] for row in rows),
            rows,
        )
        self.assertTrue(
            all("source" in row["hidden_policy_fact"] for row in rows),
            rows,
        )


if __name__ == "__main__":
    unittest.main()
