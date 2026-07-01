from __future__ import annotations

import unittest

from tracebreak.analysis.recovery_prompt_audit import audit_recovery_prompts
from tracebreak.data.generate_tasks import generate


class RecoveryPromptAuditTests(unittest.TestCase):
    def test_recovery_prompt_only_appears_after_recoverable_blocks(self) -> None:
        rows = {
            row["condition"]: row
            for row in audit_recovery_prompts(
                generate(num_seeds=1, first_seed=100),
                conditions=[
                    "api_local",
                    "api_visible_policy",
                    "api_traceguard",
                    "api_traceguard_inferred",
                ],
            )
        }

        self.assertEqual(rows["api_local"]["recovery_prompt_hits"], 0)
        self.assertEqual(rows["api_visible_policy"]["recovery_prompt_hits"], 1)
        self.assertEqual(rows["api_traceguard"]["recovery_prompt_hits"], 5)
        self.assertEqual(rows["api_traceguard_inferred"]["recovery_prompt_hits"], 5)
        for row in rows.values():
            with self.subTest(condition=row["condition"]):
                self.assertEqual(row["pre_block_recovery_prompt_hits"], 0, row)
                self.assertEqual(row["safe_control_recovery_prompt_hits"], 0, row)
                self.assertEqual(
                    row["recovery_prompt_hits"],
                    row["expected_recovery_prompt_hits"],
                    row,
                )
                self.assertTrue(row["pass"], row)

    def test_stop_mode_has_no_recovery_prompts(self) -> None:
        rows = audit_recovery_prompts(
            generate(num_seeds=1, first_seed=100),
            conditions=["api_traceguard"],
            recovery_mode="stop",
        )
        self.assertEqual(rows[0]["recoverable_sink_blocks"], 0, rows[0])
        self.assertEqual(rows[0]["recovery_prompt_hits"], 0, rows[0])
        self.assertTrue(rows[0]["pass"], rows[0])


if __name__ == "__main__":
    unittest.main()
