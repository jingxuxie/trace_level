from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from tracebreak.env.world import World
from tracebreak.experiments.run_condition import load_tasks


CATEGORY_FACTS: dict[str, dict[str, str]] = {
    "aggregation_threshold": {
        "decisive_fact": "detailed record list versus aggregate-only export",
        "fact_location": "sink-visible ref cardinality and aggregate marker",
        "visible_guard_has_fact": "yes",
    },
    "approval_scope": {
        "decisive_fact": "approval recipient and purpose must match the sink",
        "fact_location": "sink-visible approval fields",
        "visible_guard_has_fact": "yes",
    },
    "audience_restriction": {
        "decisive_fact": "source allowed-audience tag versus recipient role",
        "fact_location": "hidden source metadata plus recipient metadata",
        "visible_guard_has_fact": "no",
    },
    "cross_tenant": {
        "decisive_fact": "source tenant tag versus target customer",
        "fact_location": "hidden source metadata plus sink customer",
        "visible_guard_has_fact": "no",
    },
    "memory_laundering": {
        "decisive_fact": "memory entry inherits non-shareable source provenance",
        "fact_location": "hidden memory provenance tag",
        "visible_guard_has_fact": "no",
    },
    "sensitive_external": {
        "decisive_fact": "non-shareable confidential source sent to external recipient",
        "fact_location": "hidden source metadata plus recipient metadata",
        "visible_guard_has_fact": "no",
    },
}


def build_fact_audit_rows(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {task["task_id"]: task for task in tasks}
    categories = sorted({task["category"] for task in tasks})
    rows = []
    for category in categories:
        category_tasks = [task for task in tasks if task["category"] == category]
        risky = [task for task in category_tasks if task["risk_label"] == "risky"]
        safe = [task for task in category_tasks if task["risk_label"] == "safe"]
        pairs = _complete_pairs(category_tasks, by_id)
        deltas = sorted(
            {
                key
                for risky_task, safe_task in pairs
                for key in _param_delta_keys(risky_task, safe_task)
            }
        )
        example_risky = sorted(risky, key=lambda task: task["task_id"])[0]
        example_safe = by_id[example_risky["safe_control_pair"]]
        facts = CATEGORY_FACTS[category]
        rows.append(
            {
                "category": category,
                "risky_n": len(risky),
                "safe_n": len(safe),
                "pair_n": len(pairs),
                "sink_tool": _sink_tools(category_tasks),
                "risk_safe_delta": ",".join(deltas),
                "decisive_fact": facts["decisive_fact"],
                "fact_location": facts["fact_location"],
                "local_guard_has_fact": "no",
                "visible_guard_has_fact": facts["visible_guard_has_fact"],
                "example_source_tag": _example_source_tag(example_risky),
                "example_risky_sink": _sink_summary(example_risky),
                "example_safe_sink": _sink_summary(example_safe),
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Benchmark Policy-Fact Audit",
        "",
        "No API calls are used. This audit checks the 120 task definitions and "
        "summarizes where each category's decisive policy fact lives. A `no` in "
        "`local_guard_has_fact` means action-local existence checks do not have "
        "the metadata needed to decide the policy; a `no` in "
        "`visible_guard_has_fact` means a guard over visible sink arguments and "
        "public fields misses the decisive hidden source/runtime fact.",
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _complete_pairs(
    tasks: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for task in tasks:
        if task["risk_label"] != "risky":
            continue
        safe = by_id.get(task["safe_control_pair"])
        if safe and safe.get("safe_control_pair") == task["task_id"]:
            pairs.append((task, safe))
    return pairs


def _param_delta_keys(task_a: dict[str, Any], task_b: dict[str, Any]) -> list[str]:
    params_a = task_a.get("params", {})
    params_b = task_b.get("params", {})
    keys = sorted(set(params_a) | set(params_b))
    return [key for key in keys if params_a.get(key) != params_b.get(key)]


def _sink_tools(tasks: list[dict[str, Any]]) -> str:
    tools = sorted({task["expected_sink"]["tool"] for task in tasks})
    return ",".join(tools)


def _example_source_tag(task: dict[str, Any]) -> str:
    world = World.from_seed(task["world_seed"])
    params = task["params"]
    if "doc_id" in params:
        return _tag_summary(world.documents[params["doc_id"]].data_tag().to_dict())
    if "record_id" in params:
        return _tag_summary(world.records[params["record_id"]].data_tag().to_dict())
    if "record_ids" in params:
        tags = [world.records[record_id].data_tag().to_dict() for record_id in params["record_ids"]]
        return (
            f"{len(tags)} records; sensitivity=internal; external_share=True; "
            f"aggregate_only={params.get('aggregate_only')}"
        )
    return "none"


def _tag_summary(tag: dict[str, Any]) -> str:
    parts = [
        f"sensitivity={tag.get('sensitivity')}",
        f"external_share={tag.get('external_share')}",
    ]
    if tag.get("tenants"):
        parts.append("tenants=" + ",".join(tag["tenants"]))
    if tag.get("allowed_audience"):
        parts.append("audience=" + ",".join(tag["allowed_audience"]))
    if tag.get("record_count"):
        parts.append(f"record_count={tag['record_count']}")
    return "; ".join(parts)


def _sink_summary(task: dict[str, Any]) -> str:
    world = World.from_seed(task["world_seed"])
    expected = task["expected_sink"]
    if expected["tool"] == "send_email":
        person = world.people[expected["recipient_id"]]
        audience = "external" if person.is_external else "internal"
        tenant = f", tenant={person.tenant}" if person.tenant else ""
        return f"{person.name} ({audience}, role={person.role}{tenant})"
    if expected["tool"] == "post_ticket":
        return f"customer={expected['customer_id']}"
    return json.dumps(expected, sort_keys=True)


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Category": row["category"].replace("_", " "),
        "Pairs": f"{row['pair_n']} ({row['risky_n']} risky/{row['safe_n']} safe)",
        "Delta": row["risk_safe_delta"],
        "Sink": row["sink_tool"],
        "Decisive fact": row["decisive_fact"],
        "Fact location": row["fact_location"],
        "Local has fact": row["local_guard_has_fact"],
        "Visible has fact": row["visible_guard_has_fact"],
        "Example source tag": row["example_source_tag"],
        "R/S sink examples": f"{row['example_risky_sink']} / {row['example_safe_sink']}",
    }


def _md_table(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["No rows."]
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = build_fact_audit_rows(load_tasks(args.tasks))
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
