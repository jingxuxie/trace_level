from __future__ import annotations

import argparse
import csv
import json
import math
import shlex
from pathlib import Path
from typing import Any

from tracebreak.analysis.estimate_api_cost import (
    Price,
    cost_usd,
    estimate_task,
    parse_prices,
)
from tracebreak.experiments.run_api_condition import condition_label, load_resume_rows
from tracebreak.experiments.run_condition import load_tasks


def model_slug(model: str) -> str:
    return model.replace("gpt-", "gpt").replace(".", "").replace("-", "")


def planned_result_path(
    results_dir: str | Path,
    *,
    condition: str,
    model: str,
    limit: int,
    offset: int,
    source_ref_mode: str,
    recovery_mode: str,
) -> Path:
    label = condition_label(condition, source_ref_mode, recovery_mode)
    suffix = f"offset{offset}_{limit}" if offset else str(limit)
    return Path(results_dir) / f"{label}_{model_slug(model)}_{suffix}.jsonl"


def summarize_sweep(
    tasks: list[dict[str, Any]],
    *,
    tasks_path: str,
    conditions: list[str],
    models: list[str],
    results_dir: str | Path,
    api_key_path: str,
    api_mode: str,
    cache_dir: str,
    max_steps: int,
    recovery_mode: str,
    recovery_steps: int,
    source_ref_mode: str,
    max_output_tokens: int,
    chars_per_token: float,
    prices: dict[str, Price],
    offset: int,
    limit: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    expected_task_ids = {task["task_id"] for task in tasks}
    for model in models:
        if model not in prices:
            raise ValueError(
                f"missing price for {model}; pass --price {model}:INPUT:OUTPUT"
            )
        price = prices[model]
        for condition in conditions:
            out_path = planned_result_path(
                results_dir,
                condition=condition,
                model=model,
                limit=limit,
                offset=offset,
                source_ref_mode=source_ref_mode,
                recovery_mode=recovery_mode,
            )
            completed = {
                task_id: row
                for task_id, row in load_resume_rows(
                    out_path,
                    condition=condition,
                    source_ref_mode=source_ref_mode,
                    recovery_mode=recovery_mode,
                    recovery_steps=recovery_steps,
                    model=model,
                    api_mode=api_mode,
                ).items()
                if task_id in expected_task_ids
            }
            missing_tasks = [task for task in tasks if task["task_id"] not in completed]
            actual_prompt = sum(
                row.get("metrics", {}).get("prompt_tokens", 0)
                for row in completed.values()
            )
            actual_completion = sum(
                row.get("metrics", {}).get("completion_tokens", 0)
                for row in completed.values()
            )
            remaining_estimates = [
                estimate_task(
                    task,
                    condition=condition,
                    max_steps=max_steps,
                    recovery_mode=recovery_mode,
                    recovery_steps=recovery_steps,
                    source_ref_mode=source_ref_mode,
                    max_output_tokens=max_output_tokens,
                    chars_per_token=chars_per_token,
                )
                for task in missing_tasks
            ]
            remaining_nominal_prompt = sum(
                item["nominal_prompt_tokens"] for item in remaining_estimates
            )
            remaining_nominal_completion = sum(
                item["nominal_completion_tokens"] for item in remaining_estimates
            )
            remaining_budget_prompt = sum(
                item["budget_prompt_tokens"] for item in remaining_estimates
            )
            remaining_budget_completion = sum(
                item["budget_completion_tokens"] for item in remaining_estimates
            )
            row = {
                "model": model,
                "condition": condition,
                "api_mode": api_mode,
                "out_path": str(out_path),
                "expected": len(tasks),
                "completed": len(completed),
                "missing": len(missing_tasks),
                "parse_errors": sum(
                    row.get("metrics", {}).get("parse_errors", 0)
                    for row in completed.values()
                ),
                "prompt_tokens": actual_prompt,
                "completion_tokens": actual_completion,
                "total_tokens": sum(
                    row.get("metrics", {}).get("total_tokens", 0)
                    for row in completed.values()
                ),
                "actual_cost_usd": cost_usd(actual_prompt, actual_completion, price),
                "remaining_nominal_cost_usd": cost_usd(
                    remaining_nominal_prompt,
                    remaining_nominal_completion,
                    price,
                ),
                "remaining_budget_cost_usd": cost_usd(
                    remaining_budget_prompt,
                    remaining_budget_completion,
                    price,
                ),
                "run_command": build_run_command(
                    tasks_path=tasks_path,
                    condition=condition,
                    model=model,
                    api_mode=api_mode,
                    api_key_path=api_key_path,
                    cache_dir=cache_dir,
                    out_path=out_path,
                    offset=offset,
                    limit=limit,
                    max_steps=max_steps,
                    recovery_mode=recovery_mode,
                    recovery_steps=recovery_steps,
                    source_ref_mode=source_ref_mode,
                    max_estimated_cost_usd=cost_usd(
                        remaining_budget_prompt,
                        remaining_budget_completion,
                        price,
                    ),
                ),
            }
            rows.append(row)
    return rows


def build_run_command(
    *,
    tasks_path: str,
    condition: str,
    model: str,
    api_mode: str,
    api_key_path: str,
    cache_dir: str,
    out_path: str | Path,
    offset: int,
    limit: int,
    max_steps: int,
    recovery_mode: str,
    recovery_steps: int,
    source_ref_mode: str,
    max_estimated_cost_usd: float | None = None,
) -> str:
    parts = [
        "conda",
        "run",
        "-n",
        "trace_level",
        "python",
        "-m",
        "tracebreak.experiments.run_api_condition",
        "--tasks",
        tasks_path,
        "--condition",
        condition,
        "--model",
        model,
        "--api-mode",
        api_mode,
        "--offset",
        str(offset),
        "--limit",
        str(limit),
        "--max-steps",
        str(max_steps),
        "--source-ref-mode",
        source_ref_mode,
        "--recovery-mode",
        recovery_mode,
        "--recovery-steps",
        str(recovery_steps),
        "--api-key-path",
        api_key_path,
        "--cache-dir",
        cache_dir,
        "--resume",
        "--out",
        str(out_path),
    ]
    if max_estimated_cost_usd is not None:
        parts.extend(
            [
                "--max-estimated-cost-usd",
                _format_cost_cap(max_estimated_cost_usd),
            ]
        )
    return " ".join(shlex.quote(part) for part in parts)


def _format_cost_cap(value: float) -> str:
    if value <= 0:
        return "0"
    # Round upward so a copied command cannot fail from decimal formatting drift.
    return f"{math.ceil((value + 1e-12) * 1_000_000) / 1_000_000:.6f}"


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total_expected = sum(row["expected"] for row in rows)
    total_completed = sum(row["completed"] for row in rows)
    total_missing = sum(row["missing"] for row in rows)
    total_actual_cost = sum(row["actual_cost_usd"] for row in rows)
    total_remaining_nominal = sum(row["remaining_nominal_cost_usd"] for row in rows)
    total_remaining_budget = sum(row["remaining_budget_cost_usd"] for row in rows)
    lines = [
        "# API Sweep Status",
        "",
        "| expected | completed | missing | actual cost | remaining nominal | remaining budget |",
        "|---:|---:|---:|---:|---:|---:|",
        (
            f"| {total_expected} | {total_completed} | {total_missing} | "
            f"${total_actual_cost:.4f} | ${total_remaining_nominal:.4f} | "
            f"${total_remaining_budget:.4f} |"
        ),
        "",
        "| model | condition | API | expected | completed | missing | parse errors | actual cost | remaining nominal | remaining budget | out path |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {model} | {condition} | {api_mode} | {expected} | {completed} | {missing} | "
            "{parse_errors} | ${actual:.4f} | ${nominal:.4f} | ${budget:.4f} | "
            "`{out_path}` |".format(
                model=row["model"],
                condition=row["condition"],
                api_mode=row["api_mode"],
                expected=row["expected"],
                completed=row["completed"],
                missing=row["missing"],
                parse_errors=row["parse_errors"],
                actual=row["actual_cost_usd"],
                nominal=row["remaining_nominal_cost_usd"],
                budget=row["remaining_budget_cost_usd"],
                out_path=row["out_path"],
            )
        )
    commands = [row["run_command"] for row in rows if row["missing"]]
    if commands:
        lines.extend(["", "## Resume Commands", ""])
        for command in commands:
            lines.extend(["```bash", command, "```", ""])
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=["api_local", "api_dlp", "api_policy_prompt", "api_traceguard"],
    )
    parser.add_argument("--models", nargs="+", default=["gpt-5.4-mini"])
    parser.add_argument("--results-dir", default="results/raw_traces")
    parser.add_argument("--api-key-path", default="../apikey.txt")
    parser.add_argument(
        "--api-mode",
        choices=["chat", "responses"],
        default="responses",
        help="Endpoint to include in generated resume commands.",
    )
    parser.add_argument("--cache-dir", default="results/api_cache")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--recovery-mode", choices=["stop", "after_block"], default="stop")
    parser.add_argument("--recovery-steps", type=int, default=3)
    parser.add_argument(
        "--source-ref-mode",
        choices=["cooperative", "no_instruction", "drop_at_sink"],
        default="cooperative",
    )
    parser.add_argument("--max-output-tokens", type=int, default=220)
    parser.add_argument("--chars-per-token", type=float, default=3.5)
    parser.add_argument(
        "--price",
        action="append",
        default=[],
        help="Override price as model:input_per_mtok:output_per_mtok.",
    )
    parser.add_argument("--out-csv")
    parser.add_argument("--out-md")
    args = parser.parse_args()

    tasks = load_tasks(args.tasks)
    if args.offset:
        tasks = tasks[args.offset :]
    if args.limit is not None:
        tasks = tasks[: args.limit]
    rows = summarize_sweep(
        tasks,
        tasks_path=args.tasks,
        conditions=args.conditions,
        models=args.models,
        results_dir=args.results_dir,
        api_key_path=args.api_key_path,
        api_mode=args.api_mode,
        cache_dir=args.cache_dir,
        max_steps=args.max_steps,
        recovery_mode=args.recovery_mode,
        recovery_steps=args.recovery_steps,
        source_ref_mode=args.source_ref_mode,
        max_output_tokens=args.max_output_tokens,
        chars_per_token=args.chars_per_token,
        prices=parse_prices(args.price),
        offset=args.offset,
        limit=args.limit,
    )
    if args.out_csv:
        write_csv(rows, args.out_csv)
    if args.out_md:
        write_md(rows, args.out_md)
    if not args.out_csv and not args.out_md:
        print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
