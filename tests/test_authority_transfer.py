from __future__ import annotations

import json
import unittest
from pathlib import Path

from tracebreak.analysis.authority_transfer import (
    has_authority_transfer,
    summarize_authority_transfer,
)


class AuthorityTransferTests(unittest.TestCase):
    def test_single_agent_trace_has_no_authority_transfer(self) -> None:
        row = _row_by_id("results/raw_traces/single_local.jsonl", "sensitive_external_000_risky")
        self.assertFalse(has_authority_transfer(row))

    def test_multi_agent_trace_has_cross_actor_transfer(self) -> None:
        row = _row_by_id("results/raw_traces/multi_local.jsonl", "sensitive_external_000_risky")
        self.assertTrue(has_authority_transfer(row))

    def test_memory_handoff_counts_as_transfer(self) -> None:
        row = _row_by_id("results/raw_traces/multi_local.jsonl", "memory_laundering_000_risky")
        self.assertTrue(has_authority_transfer(row))

    def test_traceguard_blocks_all_risky_transfer_sinks(self) -> None:
        rows = _rows("results/raw_traces/traceguard.jsonl")
        summary = summarize_authority_transfer(rows)[0]
        self.assertEqual(summary["condition"], "traceguard")
        self.assertEqual(summary["risky_transfer_attempt_pct"], 100.0)
        self.assertEqual(summary["risky_transfer_violation_pct"], 0.0)
        self.assertEqual(summary["risky_transfer_block_pct"], 100.0)


def _rows(path: str) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _row_by_id(path: str, task_id: str) -> dict:
    for row in _rows(path):
        if row["task_id"] == task_id:
            return row
    raise KeyError(task_id)


if __name__ == "__main__":
    unittest.main()
