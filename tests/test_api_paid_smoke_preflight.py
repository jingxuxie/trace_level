from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tracebreak.analysis.api_paid_smoke_preflight import (
    build_payload_snapshot,
    build_preflight_row,
    write_csv,
    write_markdown,
    write_payload_json,
)
from tracebreak.experiments.run_condition import load_tasks


class ApiPaidSmokePreflightTest(unittest.TestCase):
    def test_preflight_validates_responses_schema_and_budget_guard(self) -> None:
        tasks = load_tasks("data/tasks_tracebreak_120.jsonl")[:1]
        row = build_preflight_row(
            tasks,
            condition="api_local",
            model="gpt-5.4-mini",
            api_mode="responses",
            source_ref_mode="cooperative",
            recovery_mode="stop",
            recovery_steps=3,
            max_steps=8,
            max_tokens=220,
            max_estimated_cost_usd=0.02,
            budget_mode="budget",
        )

        self.assertEqual(row["model"], "gpt-5.4-mini")
        self.assertEqual(row["condition"], "api_local")
        self.assertEqual(row["task_id"], "sensitive_external_000_risky")
        self.assertEqual(row["response_format_type"], "json_schema")
        self.assertEqual(row["response_format_name"], "tracebreak_action")
        self.assertTrue(row["strict_schema"])
        self.assertEqual(row["top_level_required"], "action,arguments")
        self.assertTrue(row["source_refs_required"])
        self.assertTrue(row["source_refs_nullable_array"])
        self.assertFalse(row["additional_properties_allowed"])
        self.assertTrue(row["source_ref_instruction_present"])
        self.assertFalse(row["policy_prompt_present"])
        self.assertFalse(row["authorization_in_payload"])
        self.assertLessEqual(row["estimated_cost_usd"], 0.02)
        self.assertTrue(row["budget_guard_pass"])

    def test_no_instruction_preflight_keeps_schema_refs_without_prompt(self) -> None:
        tasks = load_tasks("data/tasks_tracebreak_120.jsonl")[:1]
        row = build_preflight_row(
            tasks,
            condition="api_traceguard",
            model="gpt-5.4-mini",
            api_mode="responses",
            source_ref_mode="no_instruction",
            recovery_mode="stop",
            recovery_steps=3,
            max_steps=8,
            max_tokens=220,
            max_estimated_cost_usd=0.02,
            budget_mode="budget",
        )

        self.assertEqual(row["condition"], "api_traceguard_no_instruction")
        self.assertTrue(row["strict_schema"])
        self.assertTrue(row["source_refs_required"])
        self.assertTrue(row["source_refs_nullable_array"])
        self.assertFalse(row["source_ref_instruction_present"])
        self.assertFalse(row["authorization_in_payload"])
        self.assertTrue(row["budget_guard_pass"])

    def test_writers_emit_preflight_report(self) -> None:
        row = build_preflight_row(
            load_tasks("data/tasks_tracebreak_120.jsonl")[:1],
            condition="api_local",
            model="gpt-5.4-mini",
            api_mode="responses",
            source_ref_mode="cooperative",
            recovery_mode="stop",
            recovery_steps=3,
            max_steps=8,
            max_tokens=220,
            max_estimated_cost_usd=0.02,
            budget_mode="budget",
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            csv_path = base / "preflight.csv"
            md_path = base / "preflight.md"

            write_csv([row], csv_path)
            write_markdown([row], md_path)

            self.assertIn("source_refs_required", csv_path.read_text(encoding="utf-8"))
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Paid API Smoke Preflight", md_text)
            self.assertIn("| gpt-5.4-mini | api_local |", md_text)
            self.assertIn("| yes | yes | yes | yes | yes | no | no |", md_text)

    def test_payload_snapshot_writer_persists_redacted_request(self) -> None:
        snapshot = build_payload_snapshot(
            load_tasks("data/tasks_tracebreak_120.jsonl")[:1],
            condition="api_local",
            model="gpt-5.4-mini",
            api_mode="responses",
            source_ref_mode="cooperative",
            recovery_mode="stop",
            recovery_steps=3,
            max_steps=8,
            max_tokens=220,
        )
        with tempfile.TemporaryDirectory() as tmp:
            payload_path = Path(tmp) / "payload.json"
            write_payload_json(snapshot, payload_path)
            text = payload_path.read_text(encoding="utf-8")

        self.assertIn('"api_mode": "responses"', text)
        self.assertIn('"name": "tracebreak_action"', text)
        self.assertIn('"strict": true', text)
        self.assertIn('"source_refs"', text)
        self.assertNotIn("Authorization", text)


if __name__ == "__main__":
    unittest.main()
