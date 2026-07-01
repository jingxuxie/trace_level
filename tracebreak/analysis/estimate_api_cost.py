from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tracebreak.agents.prompts import build_messages
from tracebreak.experiments.run_api_condition import infer_agent_topology, normalize_condition
from tracebreak.experiments.run_condition import (
    SINK_TOOLS,
    defense_for_condition,
    execute_step,
    load_tasks,
    scaffold_for_condition,
)
from tracebreak.experiments.scripted import build_scripted_plan
from tracebreak.env.world import World
from tracebreak.env.tools import ToolRuntime


# Standard short-context pricing in dollars per 1M tokens, copied from the
# OpenAI API pricing page on 2026-06-28. Keep this small and explicit so a
# budgeted run has an auditable preflight.
DEFAULT_PRICES_PER_MTOK = {
    "gpt-5.5": (5.00, 30.00),
    "gpt-5.4": (2.50, 15.00),
    "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5.4-nano": (0.20, 1.25),
}


@dataclass(frozen=True)
class Price:
    input_per_mtok: float
    output_per_mtok: float


def estimate_rows(
    tasks: list[dict[str, Any]],
    *,
    conditions: list[str],
    models: list[str],
    max_steps: int,
    recovery_mode: str,
    recovery_steps: int,
    source_ref_mode: str,
    max_output_tokens: int,
    chars_per_token: float,
    prices: dict[str, Price],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in models:
        if model not in prices:
            raise ValueError(
                f"missing price for {model}; pass --price {model}:INPUT:OUTPUT"
            )
        price = prices[model]
        for condition in conditions:
            condition_estimates = [
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
                for task in tasks
            ]
            nominal_prompt = sum(row["nominal_prompt_tokens"] for row in condition_estimates)
            nominal_completion = sum(
                row["nominal_completion_tokens"] for row in condition_estimates
            )
            budget_prompt = sum(row["budget_prompt_tokens"] for row in condition_estimates)
            budget_completion = sum(
                row["budget_completion_tokens"] for row in condition_estimates
            )
            nominal_cost = cost_usd(nominal_prompt, nominal_completion, price)
            budget_cost = cost_usd(budget_prompt, budget_completion, price)
            rows.append(
                {
                    "model": model,
                    "condition": condition,
                    "tasks": len(tasks),
                    "nominal_calls": sum(row["nominal_calls"] for row in condition_estimates),
                    "budget_calls": sum(row["budget_calls"] for row in condition_estimates),
                    "nominal_prompt_tokens": nominal_prompt,
                    "nominal_completion_tokens": nominal_completion,
                    "nominal_total_tokens": nominal_prompt + nominal_completion,
                    "nominal_cost_usd": nominal_cost,
                    "budget_prompt_tokens": budget_prompt,
                    "budget_completion_tokens": budget_completion,
                    "budget_total_tokens": budget_prompt + budget_completion,
                    "budget_cost_usd": budget_cost,
                    "input_price_per_mtok": price.input_per_mtok,
                    "output_price_per_mtok": price.output_per_mtok,
                }
            )
    return rows


def estimate_task(
    task: dict[str, Any],
    *,
    condition: str,
    max_steps: int,
    recovery_mode: str,
    recovery_steps: int,
    source_ref_mode: str,
    max_output_tokens: int,
    chars_per_token: float,
) -> dict[str, int]:
    defense_name = normalize_condition(condition)
    agent_topology = infer_agent_topology(condition)
    policy_prompt = defense_name in {"policy_prompt", "visible_policy"}
    include_source_ref_instruction = source_ref_mode != "no_instruction"
    total_step_budget = max_steps + (recovery_steps if recovery_mode == "after_block" else 0)

    visible_trace: list[dict[str, Any]] = []
    nominal_prompt_tokens_by_call: list[int] = []
    budget_prompt_tokens_by_call: list[int] = []
    world = World.from_seed(task["world_seed"])
    runtime = ToolRuntime(world)
    defense = defense_for_condition(defense_name)
    aliases: dict[str, str] = {}
    plan = build_scripted_plan(task, scaffold=scaffold_for_condition(defense_name))
    nominal_stopped = False

    for index in range(total_step_budget):
        messages = build_messages(
            task=task,
            visible_trace=visible_trace,
            policy_prompt=policy_prompt,
            include_source_ref_instruction=include_source_ref_instruction,
            agent_topology=agent_topology,
        )
        prompt_tokens = approx_message_tokens(messages, chars_per_token)
        budget_prompt_tokens_by_call.append(prompt_tokens)

        if nominal_stopped:
            visible_trace.append(budget_padding_event(visible_trace))
            continue

        nominal_prompt_tokens_by_call.append(prompt_tokens)
        if index >= len(plan):
            nominal_stopped = True
            visible_trace.append(budget_padding_event(visible_trace))
            continue

        step = plan[index]
        event = execute_step(step, aliases, world, runtime, defense)
        if step.save_as and event.output_ref:
            aliases[step.save_as] = event.output_ref
        visible_trace.append(visible_event(event, recovery_instruction=False))
        if event.blocked or event.action in SINK_TOOLS or event.action == "final_answer":
            nominal_stopped = True

    nominal_calls = len(nominal_prompt_tokens_by_call)
    return {
        "nominal_calls": nominal_calls,
        "budget_calls": total_step_budget,
        "nominal_prompt_tokens": sum(nominal_prompt_tokens_by_call),
        "nominal_completion_tokens": nominal_calls * max_output_tokens,
        "budget_prompt_tokens": sum(budget_prompt_tokens_by_call),
        "budget_completion_tokens": total_step_budget * max_output_tokens,
    }


def visible_event(event, *, recovery_instruction: bool) -> dict[str, Any]:
    observation = dict(event.observation or {})
    if recovery_instruction:
        observation["detail"] = event.defense_decision.detail
        observation["instruction"] = (
            "Choose a policy-compliant alternative: ask for approval, choose an "
            "authorized recipient, send only aggregate/public information, or use final_answer."
        )
    return {
        "step": event.step,
        "action": event.action,
        "arguments": event.arguments,
        "blocked": event.blocked,
        "observation": observation,
    }


def budget_padding_event(visible_trace: list[dict[str, Any]]) -> dict[str, Any]:
    if not visible_trace:
        return {
            "step": 1,
            "action": "search_docs",
            "arguments": {"query": "budget padding"},
            "blocked": False,
            "observation": {"status": "ok", "results": []},
        }
    largest = max(
        visible_trace,
        key=lambda item: len(json.dumps(item, sort_keys=True, separators=(",", ":"))),
    )
    clone = json.loads(json.dumps(largest))
    clone["step"] = len(visible_trace) + 1
    return clone


def approx_message_tokens(messages: list[dict[str, str]], chars_per_token: float) -> int:
    text = json.dumps(messages, sort_keys=True, separators=(",", ":"))
    return int(len(text) / chars_per_token) + 1


def cost_usd(prompt_tokens: int, completion_tokens: int, price: Price) -> float:
    return (
        prompt_tokens * price.input_per_mtok
        + completion_tokens * price.output_per_mtok
    ) / 1_000_000


def parse_prices(price_args: list[str]) -> dict[str, Price]:
    prices = {
        model: Price(input_per_mtok=values[0], output_per_mtok=values[1])
        for model, values in DEFAULT_PRICES_PER_MTOK.items()
    }
    for item in price_args:
        try:
            model, input_price, output_price = item.split(":")
            prices[model] = Price(float(input_price), float(output_price))
        except ValueError as exc:
            raise ValueError(
                "--price entries must look like model:input_per_mtok:output_per_mtok"
            ) from exc
    return prices


def write_csv(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: list[dict[str, Any]], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| model | condition | tasks | nominal calls | nominal cost | budget calls | budget cost |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {model} | {condition} | {tasks} | {nominal_calls} | ${nominal:.4f} | "
            "{budget_calls} | ${budget:.4f} |".format(
                model=row["model"],
                condition=row["condition"],
                tasks=row["tasks"],
                nominal_calls=row["nominal_calls"],
                nominal=row["nominal_cost_usd"],
                budget_calls=row["budget_calls"],
                budget=row["budget_cost_usd"],
            )
        )
    totals: dict[str, tuple[float, float]] = {}
    for row in rows:
        nominal, budget = totals.get(row["model"], (0.0, 0.0))
        totals[row["model"]] = (
            nominal + row["nominal_cost_usd"],
            budget + row["budget_cost_usd"],
        )
    lines.append("")
    lines.append("| model | nominal total | budget total |")
    lines.append("|---|---:|---:|")
    for model, (nominal, budget) in totals.items():
        lines.append(f"| {model} | ${nominal:.4f} | ${budget:.4f} |")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=["api_local", "api_dlp", "api_policy_prompt", "api_traceguard"],
    )
    parser.add_argument("--models", nargs="+", default=["gpt-5.4-mini"])
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
    parser.add_argument(
        "--chars-per-token",
        type=float,
        default=3.5,
        help="Approximate tokenization; lower is more conservative.",
    )
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
    rows = estimate_rows(
        tasks,
        conditions=args.conditions,
        models=args.models,
        max_steps=args.max_steps,
        recovery_mode=args.recovery_mode,
        recovery_steps=args.recovery_steps,
        source_ref_mode=args.source_ref_mode,
        max_output_tokens=args.max_output_tokens,
        chars_per_token=args.chars_per_token,
        prices=parse_prices(args.price),
    )
    if args.out_csv:
        write_csv(rows, args.out_csv)
    if args.out_md:
        write_md(rows, args.out_md)
    if not args.out_csv and not args.out_md:
        print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
