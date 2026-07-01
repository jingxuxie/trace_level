from __future__ import annotations

import unittest

from tracebreak.analysis.decoy_stress import (
    apply_decoy_stress,
    build_table_rows,
    run_decoy_task,
)
from tracebreak.data.generate_tasks import generate
from tracebreak.env.world import World


class DecoyStressTests(unittest.TestCase):
    def test_decoy_world_exposes_plausible_search_hits(self) -> None:
        world = apply_decoy_stress(World.from_seed(100))
        pricing_hits = [
            document.id
            for document in world.documents.values()
            if "renewal" in " ".join(document.tags).lower()
        ]
        self.assertIn("doc_pricing_public_decoy_100", pricing_hits)
        self.assertIn("doc_pricing_beacon_decoy_100", pricing_hits)
        self.assertIn("person_maya_internal_decoy", world.people)
        self.assertIn("approval_contract_samir_expired_decoy_100", world.approvals)

    def test_traceguard_blocks_risky_with_decoy_clutter(self) -> None:
        task = _task_by_id("sensitive_external_000_risky")
        result = run_decoy_task(task, condition="traceguard")
        self.assertEqual(result["condition"], "traceguard_decoy_stress")
        self.assertGreater(result["metrics"]["search_decoy_rows"], 0)
        self.assertTrue(result["metrics"]["blocked_risky"], result)
        self.assertFalse(result["metrics"]["global_violation"], result)

    def test_inferred_traceguard_blocks_risky_with_decoy_clutter(self) -> None:
        task = _task_by_id("sensitive_external_000_risky")
        result = run_decoy_task(task, condition="traceguard_inferred")
        self.assertEqual(result["condition"], "traceguard_inferred_decoy_stress")
        self.assertGreater(result["metrics"]["search_decoy_rows"], 0)
        self.assertTrue(result["metrics"]["blocked_risky"], result)
        self.assertFalse(result["metrics"]["global_violation"], result)

    def test_traceguard_preserves_safe_with_decoy_clutter(self) -> None:
        task = _task_by_id("sensitive_external_000_safe")
        result = run_decoy_task(task, condition="traceguard")
        self.assertGreater(result["metrics"]["search_decoy_rows"], 0)
        self.assertTrue(result["metrics"]["safe_utility_success"], result)
        self.assertFalse(result["metrics"]["blocked_safe_control"], result)

    def test_table_rows_include_decoy_hits(self) -> None:
        tasks = [
            _task_by_id("sensitive_external_000_risky"),
            _task_by_id("sensitive_external_000_safe"),
        ]
        rows = [run_decoy_task(task, condition="traceguard") for task in tasks]
        table_rows = build_table_rows(rows)
        traceguard = table_rows[-1]
        self.assertEqual(traceguard["Condition"], "TraceGuard")
        self.assertGreater(traceguard["Decoy hits"], 0)


def _task_by_id(task_id: str) -> dict:
    for task in generate(num_seeds=1, first_seed=100):
        if task["task_id"] == task_id:
            return task
    raise KeyError(task_id)


if __name__ == "__main__":
    unittest.main()
