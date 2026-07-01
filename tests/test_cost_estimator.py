from __future__ import annotations

import unittest

from tracebreak.analysis.estimate_api_cost import (
    Price,
    estimate_rows,
    estimate_task,
    parse_prices,
)
from tracebreak.data.generate_tasks import generate


class ApiCostEstimatorTests(unittest.TestCase):
    def test_estimate_task_has_nominal_and_budget_tokens(self) -> None:
        task = next(iter(generate(num_seeds=1, first_seed=100)))
        estimate = estimate_task(
            task,
            condition="api_traceguard",
            max_steps=8,
            recovery_mode="stop",
            recovery_steps=3,
            source_ref_mode="cooperative",
            max_output_tokens=220,
            chars_per_token=3.5,
        )
        self.assertGreater(estimate["nominal_calls"], 0)
        self.assertEqual(estimate["budget_calls"], 8)
        self.assertGreater(estimate["nominal_prompt_tokens"], 0)
        self.assertGreaterEqual(
            estimate["budget_total_tokens"]
            if "budget_total_tokens" in estimate
            else estimate["budget_prompt_tokens"] + estimate["budget_completion_tokens"],
            estimate["nominal_prompt_tokens"] + estimate["nominal_completion_tokens"],
        )

    def test_estimate_rows_prices_models_and_conditions(self) -> None:
        tasks = list(generate(num_seeds=1, first_seed=100))[:4]
        rows = estimate_rows(
            tasks,
            conditions=["api_local", "api_traceguard"],
            models=["test-model"],
            max_steps=8,
            recovery_mode="stop",
            recovery_steps=3,
            source_ref_mode="cooperative",
            max_output_tokens=100,
            chars_per_token=3.5,
            prices={"test-model": Price(1.0, 2.0)},
        )
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["budget_cost_usd"] > 0 for row in rows))
        self.assertTrue(all(row["tasks"] == 4 for row in rows))

    def test_parse_price_override(self) -> None:
        prices = parse_prices(["custom:1.25:9.5"])
        self.assertEqual(prices["custom"].input_per_mtok, 1.25)
        self.assertEqual(prices["custom"].output_per_mtok, 9.5)


if __name__ == "__main__":
    unittest.main()
