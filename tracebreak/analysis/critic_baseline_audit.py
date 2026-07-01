from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from tracebreak.analysis.compute_metrics import read_runs
from tracebreak.experiments.run_condition import SINK_TOOLS


VISIBLE_FACT_CATEGORIES = {"aggregation_threshold", "approval_scope"}
EXPECTED_CATEGORIES = {
    "aggregation_threshold",
    "approval_scope",
    "audience_restriction",
    "cross_tenant",
    "memory_laundering",
    "sensitive_external",
}
CONDITION_KIND = {
    "api_local": "local",
    "api_local_replay_visible_policy": "visible_critic_proxy",
    "api_local_replay_metadata_critic": "metadata_critic",
    "api_local_replay_traceguard": "traceguard",
}


def summarize_critic_baseline(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        kind = CONDITION_KIND.get(row.get("condition"))
        if kind:
            grouped[(kind, row["category"])].append(row)

    out = [_summarize_category(category, grouped) for category in sorted(EXPECTED_CATEGORIES)]
    out.append(_summarize_overall(out))
    return out


def write_csv(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    overall = next((row for row in rows if row["category"] == "overall"), {})
    review_calls = overall.get("proposed_sink_reviews", 0)
    model_calls = overall.get("base_model_calls", 0)
    overhead = overall.get("review_call_overhead_pct", 0.0)
    lines = [
        "# Same-Action Critic Baseline Audit",
        "",
        "No API calls are used. This audit turns the existing same-action replay "
        "into an explicit guard-baseline accounting table. The visible-critic "
        "proxy sees only the visible trace and proposed sink; the metadata critic "
        "is a deterministic stand-in for a sink reviewer that also receives hidden "
        "source tags. The review-cost column is a lower-bound accounting estimate "
        "of one extra critic call per proposed write sink.",
        "",
        f"Overall, a sink-review critic would add {review_calls} extra sink-review "
        f"calls on top of {model_calls} base model calls in the cached API-local "
        f"subset ({overhead}% lower-bound call overhead).",
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _summarize_category(
    category: str,
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    local = grouped[("local", category)]
    visible = grouped[("visible_critic_proxy", category)]
    metadata = grouped[("metadata_critic", category)]
    traceguard = grouped[("traceguard", category)]
    proposed_reviews = _sink_attempts(local)
    model_calls = _sum_model_calls(local)
    return {
        "category": category,
        "hidden_metadata_needed": "no" if category in VISIBLE_FACT_CATEGORIES else "yes",
        "local_runs": len(local),
        "risky_n": _risk_count(local, "risky"),
        "safe_n": _risk_count(local, "safe"),
        "proposed_sink_reviews": proposed_reviews,
        "base_model_calls": model_calls,
        "review_call_overhead_pct": _pct(proposed_reviews, model_calls),
        "visible_critic_proxy_block_n": _sum_risky_metric(visible, "blocked_risky"),
        "visible_critic_proxy_violation_n": _sum_risky_metric(visible, "global_violation"),
        "visible_critic_proxy_safe_utility_n": _sum_safe_metric(visible, "safe_utility_success"),
        "metadata_critic_block_n": _sum_risky_metric(metadata, "blocked_risky"),
        "metadata_critic_violation_n": _sum_risky_metric(metadata, "global_violation"),
        "metadata_critic_safe_utility_n": _sum_safe_metric(metadata, "safe_utility_success"),
        "traceguard_block_n": _sum_risky_metric(traceguard, "blocked_risky"),
        "traceguard_violation_n": _sum_risky_metric(traceguard, "global_violation"),
        "traceguard_safe_utility_n": _sum_safe_metric(traceguard, "safe_utility_success"),
    }


def _summarize_overall(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sum_keys = [
        "local_runs",
        "risky_n",
        "safe_n",
        "proposed_sink_reviews",
        "base_model_calls",
        "visible_critic_proxy_block_n",
        "visible_critic_proxy_violation_n",
        "visible_critic_proxy_safe_utility_n",
        "metadata_critic_block_n",
        "metadata_critic_violation_n",
        "metadata_critic_safe_utility_n",
        "traceguard_block_n",
        "traceguard_violation_n",
        "traceguard_safe_utility_n",
    ]
    totals = {key: sum(row[key] for row in rows) for key in sum_keys}
    return {
        "category": "overall",
        "hidden_metadata_needed": "mixed",
        **totals,
        "review_call_overhead_pct": _pct(
            totals["proposed_sink_reviews"],
            totals["base_model_calls"],
        ),
    }


def _risk_count(rows: list[dict[str, Any]], risk_label: str) -> int:
    return sum(row.get("risk_label") == risk_label for row in rows)


def _sink_attempts(rows: list[dict[str, Any]]) -> int:
    return sum(
        event.get("action") in SINK_TOOLS
        for row in rows
        for event in row.get("trace", [])
    )


def _sum_model_calls(rows: list[dict[str, Any]]) -> int:
    return sum(int(row.get("metrics", {}).get("model_calls") or 0) for row in rows)


def _sum_risky_metric(rows: list[dict[str, Any]], metric: str) -> int:
    return sum(
        bool(row.get("metrics", {}).get(metric, False))
        for row in rows
        if row.get("risk_label") == "risky"
    )


def _sum_safe_metric(rows: list[dict[str, Any]], metric: str) -> int:
    return sum(
        bool(row.get("metrics", {}).get(metric, False))
        for row in rows
        if row.get("risk_label") == "safe"
    )


def _pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(100.0 * numerator / denominator, 1)


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Category": row["category"].replace("_", " "),
        "Hidden metadata needed": row["hidden_metadata_needed"],
        "Sink reviews": str(row["proposed_sink_reviews"]),
        "Base calls": str(row["base_model_calls"]),
        "Review overhead": f"{row['review_call_overhead_pct']}%",
        "Visible block/viol": (
            f"{row['visible_critic_proxy_block_n']}/"
            f"{row['visible_critic_proxy_violation_n']}"
        ),
        "Metadata block/viol": (
            f"{row['metadata_critic_block_n']}/"
            f"{row['metadata_critic_violation_n']}"
        ),
        "TG block/viol": f"{row['traceguard_block_n']}/{row['traceguard_violation_n']}",
        "Safe utility V/M/TG": (
            f"{row['visible_critic_proxy_safe_utility_n']}/"
            f"{row['metadata_critic_safe_utility_n']}/"
            f"{row['traceguard_safe_utility_n']} of {row['safe_n']}"
        ),
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
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = summarize_critic_baseline(read_runs(args.runs))
    write_csv(rows, Path(args.out_csv))
    write_markdown(rows, Path(args.out_md))
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
