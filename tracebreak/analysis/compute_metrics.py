from __future__ import annotations

import argparse
import csv
import glob
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def read_runs(paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pattern in paths:
        for path in sorted(glob.glob(pattern)):
            with Path(path).open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        rows.append(json.loads(line))
    return rows


def pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return 100.0 * numerator / denominator


TOKEN_FIELDS = (
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "cached_prompt_tokens",
    "reasoning_tokens",
)


def _has_token_usage(row: dict[str, Any]) -> bool:
    metrics = row.get("metrics", {})
    return any(field in metrics for field in TOKEN_FIELDS)


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["condition"]].append(row)

    global_has_recovery = any(
        row["metrics"].get("recovery_enabled", False) for row in rows
    )
    global_has_oracle_repair = any(
        "oracle_repair_success" in row["metrics"] for row in rows
    )
    global_has_inferred_sources = any(
        "inferred_source_sinks" in row["metrics"] for row in rows
    )
    global_has_corrupted_sources = any(
        "corrupted_source_sinks" in row["metrics"] for row in rows
    )
    global_has_erased_intermediate_sources = any(
        "erased_intermediate_sources" in row["metrics"] for row in rows
    )
    global_has_token_usage = any(_has_token_usage(row) for row in rows)
    summaries = []
    for condition, condition_rows in sorted(grouped.items()):
        risky = [row for row in condition_rows if row["risk_label"] == "risky"]
        safe = [row for row in condition_rows if row["risk_label"] == "safe"]
        has_model_calls = any("model_calls" in row["metrics"] for row in condition_rows)
        has_missing_source_blocks = any(
            "missing_source_blocks" in row["metrics"] for row in condition_rows
        )
        has_recovery = any(
            row["metrics"].get("recovery_enabled", False) for row in condition_rows
        )
        has_oracle_repair = any(
            "oracle_repair_success" in row["metrics"] for row in condition_rows
        )
        has_inferred_sources = any(
            "inferred_source_sinks" in row["metrics"] for row in condition_rows
        )
        has_corrupted_sources = any(
            "corrupted_source_sinks" in row["metrics"] for row in condition_rows
        )
        has_erased_intermediate_sources = any(
            "erased_intermediate_sources" in row["metrics"] for row in condition_rows
        )
        has_token_usage = any(_has_token_usage(row) for row in condition_rows)
        risky_recovery_attempts = sum(
            row["metrics"].get("recovery_attempted", False) for row in risky
        )
        summary = {
            "condition": condition,
            "n": len(condition_rows),
            "safe_n": len(safe),
            "risky_n": len(risky),
            "sink_rate_pct": pct(
                sum(row["metrics"]["sink_executed"] for row in condition_rows),
                len(condition_rows),
            ),
            "safe_utility_pct": pct(
                sum(row["metrics"]["safe_utility_success"] for row in safe), len(safe)
            ),
            "risky_global_violation_pct": pct(
                sum(row["metrics"]["global_violation"] for row in risky), len(risky)
            ),
            "risky_lpvr_pct": pct(
                sum(row["metrics"]["local_pass_violation"] for row in risky), len(risky)
            ),
            "safe_false_block_pct": pct(
                sum(row["metrics"]["blocked_safe_control"] for row in safe), len(safe)
            ),
            "risky_block_pct": pct(
                sum(row["metrics"]["blocked_risky"] for row in risky), len(risky)
            ),
            "local_block_pct": pct(
                sum(row["metrics"].get("local_blocked", False) for row in condition_rows),
                len(condition_rows),
            ),
            "defense_block_pct": pct(
                sum(row["metrics"].get("defense_blocked", False) for row in condition_rows),
                len(condition_rows),
            ),
            "avg_tool_calls": round(
                sum(row["metrics"]["tool_calls_executed"] for row in condition_rows)
                / max(len(condition_rows), 1),
                2,
            ),
            "avg_model_calls": (
                round(
                    sum(row["metrics"].get("model_calls", 0) for row in condition_rows)
                    / max(len(condition_rows), 1),
                    2,
                )
                if has_model_calls
                else ""
            ),
            "parse_errors": (
                sum(row["metrics"].get("parse_errors", 0) for row in condition_rows)
                if has_model_calls
                else ""
            ),
            "missing_source_blocks": (
                sum(
                    row["metrics"].get("missing_source_blocks", 0)
                    for row in condition_rows
                )
                if has_missing_source_blocks
                else ""
            ),
        }
        if global_has_token_usage:
            if has_token_usage:
                for field in TOKEN_FIELDS:
                    summary[field] = sum(
                        row["metrics"].get(field, 0) for row in condition_rows
                    )
                summary["avg_total_tokens"] = round(
                    summary["total_tokens"] / max(len(condition_rows), 1), 2
                )
            else:
                for field in TOKEN_FIELDS:
                    summary[field] = ""
                summary["avg_total_tokens"] = ""
        if global_has_recovery:
            summary.update(
                {
                    "risky_repair_pct": (
                        pct(
                            sum(
                                row["metrics"].get("risky_repair_success", False)
                                for row in risky
                            ),
                            len(risky),
                        )
                        if has_recovery
                        else ""
                    ),
                    "unsafe_retry_after_block_pct": (
                        pct(
                            sum(
                                row["metrics"].get("unsafe_retry_after_block", False)
                                for row in risky
                            ),
                            risky_recovery_attempts,
                        )
                        if has_recovery
                        else ""
                    ),
                    "clarification_after_block_pct": (
                        pct(
                            sum(
                                row["metrics"].get("recovery_final_answer", False)
                                for row in risky
                            ),
                            len(risky),
                        )
                        if has_recovery
                        else ""
                    ),
                    "avg_recovery_steps": (
                        round(
                            sum(
                                row["metrics"].get("recovery_steps_used", 0)
                                for row in condition_rows
                            )
                            / max(len(condition_rows), 1),
                            2,
                        )
                        if has_recovery
                        else ""
                    ),
                }
            )
        if global_has_oracle_repair:
            summary.update(
                {
                    "oracle_repair_success_pct": (
                        pct(
                            sum(
                                row["metrics"].get("oracle_repair_success", False)
                                for row in condition_rows
                            ),
                            len(condition_rows),
                        )
                        if has_oracle_repair
                        else ""
                    ),
                    "oracle_repair_block_pct": (
                        pct(
                            sum(
                                row["metrics"].get("oracle_repair_blocked", False)
                                for row in condition_rows
                            ),
                            len(condition_rows),
                        )
                        if has_oracle_repair
                        else ""
                    ),
                }
            )
        if global_has_inferred_sources:
            summary["inferred_source_sinks"] = (
                sum(
                    row["metrics"].get("inferred_source_sinks", 0)
                    for row in condition_rows
                )
                if has_inferred_sources
                else ""
            )
        if global_has_corrupted_sources:
            summary["corrupted_source_sinks"] = (
                sum(
                    row["metrics"].get("corrupted_source_sinks", 0)
                    for row in condition_rows
                )
                if has_corrupted_sources
                else ""
            )
        if global_has_erased_intermediate_sources:
            summary["erased_intermediate_sources"] = (
                sum(
                    row["metrics"].get("erased_intermediate_sources", 0)
                    for row in condition_rows
                )
                if has_erased_intermediate_sources
                else ""
            )
        summaries.append(summary)
    return summaries


def category_breakdown(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["condition"], row["category"])].append(row)
    out = []
    for (condition, category), group in sorted(grouped.items()):
        risky = [row for row in group if row["risk_label"] == "risky"]
        safe = [row for row in group if row["risk_label"] == "safe"]
        has_model_calls = any("model_calls" in row["metrics"] for row in group)
        out.append(
            {
                "condition": condition,
                "category": category,
                "n": len(group),
                "safe_n": len(safe),
                "risky_n": len(risky),
                "safe_utility_pct": pct(
                    sum(row["metrics"]["safe_utility_success"] for row in safe),
                    len(safe),
                ),
                "risky_global_violation_pct": pct(
                    sum(row["metrics"]["global_violation"] for row in risky),
                    len(risky),
                ),
                "risky_lpvr_pct": pct(
                    sum(row["metrics"]["local_pass_violation"] for row in risky),
                    len(risky),
                ),
                "risky_block_pct": pct(
                    sum(row["metrics"]["blocked_risky"] for row in risky),
                    len(risky),
                ),
                "safe_false_block_pct": pct(
                    sum(row["metrics"]["blocked_safe_control"] for row in safe),
                    len(safe),
                ),
                "avg_tool_calls": round(
                    sum(row["metrics"]["tool_calls_executed"] for row in group)
                    / max(len(group), 1),
                    2,
                ),
                "avg_model_calls": (
                    round(
                        sum(row["metrics"].get("model_calls", 0) for row in group)
                        / max(len(group), 1),
                        2,
                    )
                    if has_model_calls
                    else ""
                ),
            }
        )
    return out


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary_rows: list[dict[str, Any]], category_rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# TraceBreak Results", "", "## Main Conditions", ""]
    lines.extend(_md_table(summary_rows))
    lines.extend(["", "## Category Breakdown", ""])
    lines.extend(_md_table(category_rows))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _md_table(rows: list[dict[str, Any]]) -> list[str]:
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
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out-csv", default="results/metrics.csv")
    parser.add_argument("--out-md", default="results/tables/main_results.md")
    args = parser.parse_args()

    runs = read_runs(args.runs)
    summary_rows = summarize(runs)
    category_rows = category_breakdown(runs)
    write_csv(summary_rows, args.out_csv)
    write_markdown(summary_rows, category_rows, args.out_md)
    print(f"read {len(runs)} runs")
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
