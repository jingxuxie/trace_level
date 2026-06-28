from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_runs(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def find_run(rows: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    for row in rows:
        if row["task_id"] == task_id:
            return row
    raise KeyError(task_id)


def format_run(row: dict[str, Any]) -> list[str]:
    lines = [
        f"### `{row['condition']}` / `{row['task_id']}`",
        "",
        f"- category: `{row['category']}`",
        f"- risk label: `{row['risk_label']}`",
        f"- sink executed: `{row['metrics']['sink_executed']}`",
        f"- global violation: `{row['metrics']['global_violation']}`",
        f"- defense blocked: `{row['metrics'].get('defense_blocked', False)}`",
        "",
        "| step | action | local | defense | sources | tag summary |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for event in row["trace"]:
        tag = event.get("tag", {})
        tag_summary = {
            "sens": tag.get("sensitivity"),
            "tenant": tag.get("tenants"),
            "aud": tag.get("allowed_audience"),
            "ext": tag.get("external_share"),
            "records": tag.get("record_count"),
            "agg": tag.get("aggregate_only"),
        }
        action = event["action"]
        if event.get("blocked"):
            action += " (blocked)"
        lines.append(
            "| {step} | `{action}` | `{local}` | `{defense}` | `{sources}` | `{tag}` |".format(
                step=event["step"],
                action=action,
                local=event["local_decision"]["reason_code"],
                defense=event["defense_decision"]["reason_code"],
                sources=','.join(tag.get("source_ids", [])) or "-",
                tag=json.dumps(tag_summary, sort_keys=True),
            )
        )
    lines.append("")
    if row["metrics"].get("violations"):
        lines.append("Violation decisions:")
        for violation in row["metrics"]["violations"]:
            lines.append(f"- `{violation['reason_code']}` from sources `{violation['source_ids']}`")
        lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-run", default="results/raw_traces/api_local_gpt41mini_12.jsonl")
    parser.add_argument("--traceguard-run", default="results/raw_traces/api_traceguard_gpt41mini_12.jsonl")
    parser.add_argument("--task-id", default="sensitive_external_000_risky")
    parser.add_argument("--out", default="paper/tables/example_traces.md")
    args = parser.parse_args()

    local = find_run(read_runs(args.local_run), args.task_id)
    guarded = find_run(read_runs(args.traceguard_run), args.task_id)
    lines = [
        "# Example Trace Pair",
        "",
        "This example uses the same task under local guards and TraceGuard.",
        "",
    ]
    lines.extend(format_run(local))
    lines.extend(format_run(guarded))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
