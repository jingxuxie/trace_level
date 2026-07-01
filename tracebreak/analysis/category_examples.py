from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tracebreak.analysis.compute_metrics import read_runs


EXPECTED_CATEGORIES = (
    "aggregation_threshold",
    "approval_scope",
    "audience_restriction",
    "cross_tenant",
    "memory_laundering",
    "sensitive_external",
)


def build_category_examples(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_condition_task = _index_by_condition_task(rows)
    local_rows = by_condition_task.get("api_local", {})
    traceguard_rows = by_condition_task.get("api_traceguard", {})
    examples: dict[str, dict[str, str]] = {}
    for task_id, local in sorted(local_rows.items()):
        category = local["category"]
        if category in examples or local["risk_label"] != "risky":
            continue
        if not local["metrics"].get("global_violation", False):
            continue
        guarded = traceguard_rows.get(task_id)
        if not guarded:
            continue
        examples[category] = summarize_pair(local, guarded)
    missing = sorted(set(EXPECTED_CATEGORIES) - set(examples))
    if missing:
        raise ValueError(f"missing category examples: {missing}")
    return [examples[category] for category in EXPECTED_CATEGORIES]


def summarize_pair(local: dict[str, Any], guarded: dict[str, Any]) -> dict[str, str]:
    local_sink = _sink_event(local)
    guarded_sink = _sink_event(guarded)
    violation = (local["metrics"].get("violations") or [{}])[0]
    return {
        "category": local["category"],
        "task_id": local["task_id"],
        "local_trace": _action_path(local),
        "local_result": _local_result(local_sink, violation),
        "traceguard_result": _traceguard_result(guarded_sink),
        "hidden_policy_fact": _tag_summary(local_sink.get("tag", {})),
    }


def _index_by_condition_task(
    rows: list[dict[str, Any]]
) -> dict[str, dict[str, dict[str, Any]]]:
    indexed: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        indexed.setdefault(row["condition"], {})[row["task_id"]] = row
    return indexed


def _sink_event(row: dict[str, Any]) -> dict[str, Any]:
    for event in reversed(row["trace"]):
        if event["action"] in {"send_email", "post_ticket", "final_answer"}:
            return event
    return row["trace"][-1]


def _action_path(row: dict[str, Any]) -> str:
    parts = []
    for event in row["trace"]:
        action = event["action"]
        if event.get("blocked"):
            action = f"{action} blocked"
        parts.append(action)
    return " -> ".join(parts)


def _local_result(event: dict[str, Any], violation: dict[str, Any]) -> str:
    reason = violation.get("reason_code", "unknown_violation")
    sources = ",".join(violation.get("source_ids", [])) or "-"
    return f"{event['action']} executed; global violation `{reason}`; sources `{sources}`"


def _traceguard_result(event: dict[str, Any]) -> str:
    decision = event.get("defense_decision", {})
    reason = decision.get("reason_code", "allow")
    if event.get("blocked"):
        return f"{event['action']} blocked; reason `{reason}`"
    return f"{event['action']} allowed; reason `{reason}`"


def _tag_summary(tag: dict[str, Any]) -> str:
    parts = [
        f"sensitivity={tag.get('sensitivity', 'public')}",
        f"external_share={tag.get('external_share', True)}",
    ]
    if tag.get("tenants"):
        parts.append("tenants=" + ",".join(tag["tenants"]))
    if tag.get("allowed_audience"):
        parts.append("audience=" + ",".join(tag["allowed_audience"]))
    if tag.get("record_count"):
        parts.append(f"record_count={tag['record_count']}")
    if tag.get("aggregate_only"):
        parts.append("aggregate_only=true")
    if tag.get("source_ids"):
        parts.append("sources=" + ",".join(tag["source_ids"]))
    return "; ".join(parts)


def write_markdown(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# API Category Example Gallery",
        "",
        "One risky `gpt-4.1-mini` API-local trace per policy category, aligned with the matching TraceGuard trace.",
        "",
        "| category | task | local action path | local result | TraceGuard result | hidden policy fact |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {category} | `{task_id}` | {local_trace} | {local_result} | {traceguard_result} | {hidden_policy_fact} |".format(
                **{key: _escape_md(value) for key, value in row.items()}
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _escape_md(value: str) -> str:
    return str(value).replace("|", "\\|")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument(
        "--out",
        default="paper/tables/api_gpt41mini_category_examples.md",
    )
    args = parser.parse_args()

    rows = build_category_examples(read_runs(args.runs))
    write_markdown(rows, Path(args.out))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
