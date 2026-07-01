from __future__ import annotations

import unittest

from tracebreak.analysis.injection_overlay import (
    DEFAULT_INJECTION,
    apply_injection_overlay,
    run_injection_task,
)
from tracebreak.data.generate_tasks import generate
from tracebreak.env.world import World


class InjectionOverlayTests(unittest.TestCase):
    def test_overlay_appends_visible_text_without_changing_tags(self) -> None:
        world = World.from_seed(100)
        original_tag = world.documents["doc_pricing_100"].data_tag().to_dict()
        apply_injection_overlay(world)

        self.assertIn(DEFAULT_INJECTION.strip(), world.documents["doc_pricing_100"].body)
        self.assertEqual(world.documents["doc_pricing_100"].data_tag().to_dict(), original_tag)
        self.assertIn(DEFAULT_INJECTION.strip(), world.records["custrec_atlas_100"].body)

    def test_traceguard_still_blocks_risky_overlay_trace(self) -> None:
        task = _task_by_id("sensitive_external_000_risky")
        result = run_injection_task(task, condition="traceguard")

        self.assertEqual(result["condition"], "traceguard_injection_overlay")
        self.assertTrue(result["metrics"]["blocked_risky"], result)
        self.assertFalse(result["metrics"]["global_violation"], result)

    def test_inferred_traceguard_blocks_risky_overlay_trace(self) -> None:
        task = _task_by_id("sensitive_external_000_risky")
        result = run_injection_task(task, condition="traceguard_inferred")

        self.assertEqual(result["condition"], "traceguard_inferred_injection_overlay")
        self.assertTrue(result["metrics"]["blocked_risky"], result)
        self.assertFalse(result["metrics"]["global_violation"], result)

    def test_dlp_still_misses_hidden_overlay_violation(self) -> None:
        task = _task_by_id("sensitive_external_000_risky")
        result = run_injection_task(task, condition="dlp")

        self.assertEqual(result["condition"], "dlp_injection_overlay")
        self.assertFalse(result["metrics"]["blocked_risky"], result)
        self.assertTrue(result["metrics"]["global_violation"], result)


def _task_by_id(task_id: str) -> dict:
    for task in generate(num_seeds=1, first_seed=100):
        if task["task_id"] == task_id:
            return task
    raise KeyError(task_id)


if __name__ == "__main__":
    unittest.main()
