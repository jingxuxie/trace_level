from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from tracebreak.analysis.benchmark_fact_audit import CATEGORY_FACTS
from tracebreak.experiments.run_condition import load_tasks
from tracebreak.experiments.scripted import build_scripted_plan


VISIBLE_FACT_CATEGORIES = {
    category
    for category, facts in CATEGORY_FACTS.items()
    if facts["visible_guard_has_fact"] == "yes"
}


FLOW_ARCHETYPES = {
    "aggregation_threshold": "multi_record_email",
    "approval_scope": "approval_doc_email",
    "audience_restriction": "audience_doc_email",
    "cross_tenant": "record_ticket",
    "memory_laundering": "memory_handoff_email",
    "sensitive_external": "confidential_doc_email",
}


def build_coverage_rows(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {task["task_id"]: task for task in tasks}
    categories = sorted({task["category"] for task in tasks})
    rows = [_category_row(category, [task for task in tasks if task["category"] == category], by_id) for category in categories]
    rows.append(_overall_row(tasks, rows))
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
    overall = rows[-1] if rows else {}
    lines = [
        "# Benchmark Coverage Audit",
        "",
        "No API calls are used. This audit summarizes benchmark structure from "
        "the generated task definitions and scripted plans.",
        "",
        (
            f"Overall coverage: {overall.get('task_n', 0)} tasks over "
            f"{overall.get('world_seed_n', 0)} seeds, "
            f"{overall.get('complete_pair_n', 0)} risky/safe pairs, "
            f"{overall.get('visible_fact_task_n', 0)} visible-fact tasks, and "
            f"{overall.get('hidden_fact_task_n', 0)} hidden-metadata tasks."
        ),
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _category_row(
    category: str,
    tasks: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pairs = _complete_pairs(tasks, by_id)
    sink_counts = Counter(task["expected_sink"]["tool"] for task in tasks)
    step_counts = [len(build_scripted_plan(task, scaffold="multi")) for task in tasks]
    source_counts = [_source_object_count(task) for task in tasks]
    deltas = sorted(
        {
            delta
            for risky, safe in pairs
            for delta in _param_delta_keys(risky, safe)
        }
    )
    return {
        "category": category,
        "task_n": len(tasks),
        "risky_n": _risk_count(tasks, "risky"),
        "safe_n": _risk_count(tasks, "safe"),
        "complete_pair_n": len(pairs),
        "world_seed_n": len({task["world_seed"] for task in tasks}),
        "fact_visibility": "visible" if category in VISIBLE_FACT_CATEGORIES else "hidden",
        "flow_archetype": FLOW_ARCHETYPES[category],
        "sink_tool_counts": _format_counts(sink_counts),
        "unique_sink_targets": len({_sink_target(task) for task in tasks}),
        "unique_source_ids": len({source_id for task in tasks for source_id in _source_ids(task)}),
        "source_object_min": min(source_counts),
        "source_object_max": max(source_counts),
        "scripted_step_min": min(step_counts),
        "scripted_step_max": max(step_counts),
        "risk_safe_delta": ",".join(deltas),
        "visible_fact_task_n": len(tasks) if category in VISIBLE_FACT_CATEGORIES else 0,
        "hidden_fact_task_n": 0 if category in VISIBLE_FACT_CATEGORIES else len(tasks),
    }


def _overall_row(tasks: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = _complete_pairs(tasks, {task["task_id"]: task for task in tasks})
    sink_counts = Counter(task["expected_sink"]["tool"] for task in tasks)
    source_counts = [_source_object_count(task) for task in tasks]
    step_counts = [len(build_scripted_plan(task, scaffold="multi")) for task in tasks]
    return {
        "category": "overall",
        "task_n": len(tasks),
        "risky_n": _risk_count(tasks, "risky"),
        "safe_n": _risk_count(tasks, "safe"),
        "complete_pair_n": len(pairs),
        "world_seed_n": len({task["world_seed"] for task in tasks}),
        "fact_visibility": "mixed",
        "flow_archetype": f"{len({row['flow_archetype'] for row in rows})} archetypes",
        "sink_tool_counts": _format_counts(sink_counts),
        "unique_sink_targets": len({_sink_target(task) for task in tasks}),
        "unique_source_ids": len({source_id for task in tasks for source_id in _source_ids(task)}),
        "source_object_min": min(source_counts),
        "source_object_max": max(source_counts),
        "scripted_step_min": min(step_counts),
        "scripted_step_max": max(step_counts),
        "risk_safe_delta": ",".join(sorted({delta for row in rows for delta in row["risk_safe_delta"].split(",") if delta})),
        "visible_fact_task_n": sum(row["visible_fact_task_n"] for row in rows),
        "hidden_fact_task_n": sum(row["hidden_fact_task_n"] for row in rows),
    }


def _complete_pairs(
    tasks: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pairs = []
    for task in tasks:
        if task["risk_label"] != "risky":
            continue
        safe = by_id.get(task["safe_control_pair"])
        if safe and safe.get("safe_control_pair") == task["task_id"]:
            pairs.append((task, safe))
    return pairs


def _risk_count(tasks: list[dict[str, Any]], risk_label: str) -> int:
    return sum(task["risk_label"] == risk_label for task in tasks)


def _source_object_count(task: dict[str, Any]) -> int:
    return len(_source_ids(task))


def _source_ids(task: dict[str, Any]) -> list[str]:
    params = task.get("params", {})
    ids: list[str] = []
    if params.get("doc_id"):
        ids.append(params["doc_id"])
    if params.get("record_id"):
        ids.append(params["record_id"])
    ids.extend(params.get("record_ids") or [])
    if params.get("approval_id"):
        ids.append(params["approval_id"])
    return ids


def _sink_target(task: dict[str, Any]) -> str:
    sink = task["expected_sink"]
    if sink["tool"] == "send_email":
        return f"send_email:{sink['recipient_id']}"
    if sink["tool"] == "post_ticket":
        return f"post_ticket:{sink['customer_id']}"
    return sink["tool"]


def _param_delta_keys(task_a: dict[str, Any], task_b: dict[str, Any]) -> list[str]:
    params_a = task_a.get("params", {})
    params_b = task_b.get("params", {})
    keys = sorted(set(params_a) | set(params_b))
    return [key for key in keys if params_a.get(key) != params_b.get(key)]


def _format_counts(counts: Counter[str]) -> str:
    return "; ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Category": row["category"].replace("_", " "),
        "Tasks": f"{row['task_n']} ({row['risky_n']} risky/{row['safe_n']} safe)",
        "Pairs": str(row["complete_pair_n"]),
        "Seeds": str(row["world_seed_n"]),
        "Fact": row["fact_visibility"],
        "Flow": row["flow_archetype"],
        "Sinks": row["sink_tool_counts"],
        "Targets": str(row["unique_sink_targets"]),
        "Sources": f"{row['unique_source_ids']} unique; {row['source_object_min']}-{row['source_object_max']} per task",
        "Steps": f"{row['scripted_step_min']}-{row['scripted_step_max']}",
        "Pair delta": row["risk_safe_delta"],
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
        lines.append("| " + " | ".join(row.get(header, "") for header in headers) + " |")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = build_coverage_rows(load_tasks(args.tasks))
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
