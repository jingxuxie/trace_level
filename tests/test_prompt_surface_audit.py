from __future__ import annotations

import unittest

from tracebreak.analysis.prompt_surface_audit import audit_prompt_surface
from tracebreak.data.generate_tasks import generate


class PromptSurfaceAuditTests(unittest.TestCase):
    def test_prompt_surface_hides_metadata_and_task_labels(self) -> None:
        rows = audit_prompt_surface(
            generate(num_seeds=1, first_seed=100),
            conditions=[
                "api_local",
                "api_policy_prompt",
                "api_traceguard_inferred",
                "api_multi_traceguard",
            ],
        )

        self.assertTrue(rows)
        for row in rows:
            with self.subTest(condition=row["condition"]):
                self.assertEqual(row["hidden_metadata_prompt_hits"], 0, row)
                self.assertEqual(row["hidden_metadata_keys_found"], "", row)
                self.assertEqual(row["task_label_prompt_hits"], 0, row)
                self.assertEqual(row["task_label_keys_found"], "", row)
                self.assertTrue(row["pass"], row)

    def test_prompt_surface_instruction_boundaries(self) -> None:
        rows = {
            row["condition"]: row
            for row in audit_prompt_surface(
                generate(num_seeds=1, first_seed=100),
                conditions=["api_local", "api_policy_prompt", "api_multi_traceguard"],
            )
        }

        local = rows["api_local"]
        self.assertEqual(local["policy_prompt_hits"], 0, local)
        self.assertEqual(local["multi_agent_prompt_hits"], 0, local)
        self.assertEqual(
            local["source_ref_instruction_hits"],
            local["expected_source_ref_instruction_hits"],
            local,
        )

        policy = rows["api_policy_prompt"]
        self.assertEqual(policy["policy_prompt_hits"], policy["prompts"], policy)
        self.assertEqual(policy["multi_agent_prompt_hits"], 0, policy)

        multi = rows["api_multi_traceguard"]
        self.assertEqual(multi["multi_agent_prompt_hits"], multi["prompts"], multi)
        self.assertEqual(multi["policy_prompt_hits"], 0, multi)


if __name__ == "__main__":
    unittest.main()
