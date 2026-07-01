from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from tracebreak.experiments.run_api_condition import (
    check_budget_guard,
    dry_run_first_request,
)
from tracebreak.experiments.run_condition import load_tasks


def build_payload_snapshot(
    tasks: list[dict[str, Any]],
    *,
    condition: str,
    model: str,
    api_mode: str,
    source_ref_mode: str,
    recovery_mode: str,
    recovery_steps: int,
    max_steps: int,
    max_tokens: int,
) -> dict[str, Any]:
    return dry_run_first_request(
        tasks,
        condition=condition,
        source_ref_mode=source_ref_mode,
        recovery_mode=recovery_mode,
        recovery_steps=recovery_steps,
        model=model,
        api_mode=api_mode,
        max_steps=max_steps,
        max_tokens=max_tokens,
    )


def build_preflight_row(
    tasks: list[dict[str, Any]],
    *,
    condition: str,
    model: str,
    api_mode: str,
    source_ref_mode: str,
    recovery_mode: str,
    recovery_steps: int,
    max_steps: int,
    max_tokens: int,
    max_estimated_cost_usd: float,
    budget_mode: str,
) -> dict[str, Any]:
    dry_run = build_payload_snapshot(
        tasks,
        condition=condition,
        source_ref_mode=source_ref_mode,
        recovery_mode=recovery_mode,
        recovery_steps=recovery_steps,
        model=model,
        api_mode=api_mode,
        max_steps=max_steps,
        max_tokens=max_tokens,
    )
    budget = check_budget_guard(
        tasks,
        condition=condition,
        model=model,
        max_steps=max_steps,
        recovery_mode=recovery_mode,
        recovery_steps=recovery_steps,
        source_ref_mode=source_ref_mode,
        max_estimated_cost_usd=max_estimated_cost_usd,
        budget_mode=budget_mode,
        max_output_tokens=max_tokens,
    )
    if budget is None:
        raise ValueError("preflight requires a budget cap")

    payload = dry_run["request_payload"]
    text_format = (payload.get("text") or {}).get("format") or {}
    schema = text_format.get("schema") or {}
    arguments = (schema.get("properties") or {}).get("arguments") or {}
    argument_properties = arguments.get("properties") or {}
    source_refs = argument_properties.get("source_refs") or {}
    payload_text = json.dumps(payload, sort_keys=True)
    messages = payload.get("input", payload.get("messages", []))
    system_text = "\n".join(
        str(message.get("content", ""))
        for message in messages
        if isinstance(message, dict) and message.get("role") == "system"
    )
    source_instruction = (
        "include it in" in system_text and "source_refs" in system_text
    )
    policy_prompt = "Security policy:" in system_text

    cost_field = "nominal_cost_usd" if budget_mode == "nominal" else "budget_cost_usd"
    return {
        "model": model,
        "condition": dry_run["condition"],
        "api_mode": api_mode,
        "task_id": dry_run["task_id"],
        "category": dry_run["category"],
        "risk_label": dry_run["risk_label"],
        "max_steps": max_steps,
        "max_tokens": max_tokens,
        "response_format_type": text_format.get("type", ""),
        "response_format_name": text_format.get("name", ""),
        "strict_schema": bool(text_format.get("strict", False)),
        "top_level_required": ",".join(schema.get("required", [])),
        "arguments_required_n": len(arguments.get("required", [])),
        "source_refs_required": "source_refs" in arguments.get("required", []),
        "source_refs_nullable_array": source_refs.get("type") == ["array", "null"],
        "additional_properties_allowed": bool(schema.get("additionalProperties", True))
        or bool(arguments.get("additionalProperties", True)),
        "source_ref_instruction_present": source_instruction,
        "policy_prompt_present": policy_prompt,
        "authorization_in_payload": "Authorization" in payload_text,
        "input_message_count": len(payload.get("input", payload.get("messages", []))),
        "budget_mode": budget_mode,
        "estimated_cost_usd": float(budget[cost_field]),
        "budget_cap_usd": max_estimated_cost_usd,
        "budget_guard_pass": float(budget[cost_field]) <= max_estimated_cost_usd,
    }


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
        "# Paid API Smoke Preflight",
        "",
        "No API calls are made by this audit. It validates the first planned "
        "Responses API request payload and budget guard before the paid "
        "modern-model smoke is approved.",
        "",
    ]
    lines.extend(_md_table([_markdown_row(row) for row in rows]))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_payload_json(snapshot: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload_text = json.dumps(snapshot, sort_keys=True)
    if "Authorization" in payload_text:
        raise ValueError("dry-run payload snapshot unexpectedly contains Authorization")
    out_path.write_text(json.dumps(snapshot, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _markdown_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "Model": row["model"],
        "Condition": row["condition"],
        "Task": row["task_id"],
        "API": row["api_mode"],
        "Format": f"{row['response_format_type']}:{row['response_format_name']}",
        "Strict": _yes(row["strict_schema"]),
        "Refs required": _yes(row["source_refs_required"]),
        "Refs nullable array": _yes(row["source_refs_nullable_array"]),
        "No extra props": _yes(not row["additional_properties_allowed"]),
        "Source-ref prompt": _yes(row["source_ref_instruction_present"]),
        "Policy prompt": _yes(row["policy_prompt_present"]),
        "Auth header": _yes(row["authorization_in_payload"]),
        "Budget": f"${row['estimated_cost_usd']:.4f} <= ${row['budget_cap_usd']:.4f}",
        "Pass": _yes(row["budget_guard_pass"]),
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


def _yes(value: Any) -> str:
    return "yes" if bool(value) else "no"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument("--condition", default="api_local")
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--api-mode", choices=["chat", "responses"], default="responses")
    parser.add_argument(
        "--source-ref-mode",
        choices=["cooperative", "no_instruction", "drop_at_sink"],
        default="cooperative",
    )
    parser.add_argument("--recovery-mode", choices=["stop", "after_block"], default="stop")
    parser.add_argument("--recovery-steps", type=int, default=3)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=220)
    parser.add_argument("--max-estimated-cost-usd", type=float, default=0.02)
    parser.add_argument("--budget-mode", choices=["nominal", "budget"], default="budget")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-payload-json")
    args = parser.parse_args()

    tasks = load_tasks(args.tasks)
    if args.offset:
        tasks = tasks[args.offset :]
    tasks = tasks[: args.limit]
    rows = [
        build_preflight_row(
            tasks,
            condition=args.condition,
            model=args.model,
            api_mode=args.api_mode,
            source_ref_mode=args.source_ref_mode,
            recovery_mode=args.recovery_mode,
            recovery_steps=args.recovery_steps,
            max_steps=args.max_steps,
            max_tokens=args.max_tokens,
            max_estimated_cost_usd=args.max_estimated_cost_usd,
            budget_mode=args.budget_mode,
        )
    ]
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md)
    if args.out_payload_json:
        write_payload_json(
            build_payload_snapshot(
                tasks,
                condition=args.condition,
                model=args.model,
                api_mode=args.api_mode,
                source_ref_mode=args.source_ref_mode,
                recovery_mode=args.recovery_mode,
                recovery_steps=args.recovery_steps,
                max_steps=args.max_steps,
                max_tokens=args.max_tokens,
            ),
            args.out_payload_json,
        )
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")
    if args.out_payload_json:
        print(f"wrote {args.out_payload_json}")


if __name__ == "__main__":
    main()
