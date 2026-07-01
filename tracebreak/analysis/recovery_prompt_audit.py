from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from tracebreak.agents.prompts import build_messages
from tracebreak.experiments.run_api_condition import (
    RECOVERY_INSTRUCTION_TEXT,
    _is_recoverable_sink_block,
    _visible_event,
    infer_agent_topology,
    normalize_condition,
)
from tracebreak.experiments.run_condition import (
    SINK_TOOLS,
    defense_for_condition,
    execute_step,
    load_tasks,
)
from tracebreak.experiments.scripted import build_scripted_plan
from tracebreak.env.tools import ToolRuntime
from tracebreak.env.world import World


def audit_recovery_prompts(
    tasks: list[dict[str, Any]],
    *,
    conditions: list[str],
    max_steps: int = 8,
    source_ref_mode: str = "cooperative",
    recovery_mode: str = "after_block",
) -> list[dict[str, Any]]:
    return [
        audit_condition(
            tasks,
            condition=condition,
            max_steps=max_steps,
            source_ref_mode=source_ref_mode,
            recovery_mode=recovery_mode,
        )
        for condition in conditions
    ]


def audit_condition(
    tasks: list[dict[str, Any]],
    *,
    condition: str,
    max_steps: int,
    source_ref_mode: str,
    recovery_mode: str,
) -> dict[str, Any]:
    defense_name = normalize_condition(condition)
    defense = defense_for_condition(defense_name)
    policy_prompt = defense_name in {"policy_prompt", "visible_policy"}
    agent_topology = infer_agent_topology(condition)
    scaffold = "multi" if agent_topology == "multi" else "single"
    include_source_ref_instruction = source_ref_mode != "no_instruction"
    recovery_enabled = recovery_mode == "after_block"

    prompts = 0
    recovery_prompt_hits = 0
    pre_block_recovery_prompt_hits = 0
    post_block_recovery_prompts = 0
    safe_control_recovery_prompt_hits = 0
    blocked_sinks = 0
    recoverable_sink_blocks = 0

    for task in tasks:
        world = World.from_seed(task["world_seed"])
        runtime = ToolRuntime(world)
        visible_trace: list[dict[str, Any]] = []
        aliases: dict[str, str] = {}
        plan = build_scripted_plan(task, scaffold=scaffold)

        for step in plan[:max_steps]:
            messages = build_messages(
                task=task,
                visible_trace=visible_trace,
                policy_prompt=policy_prompt,
                include_source_ref_instruction=include_source_ref_instruction,
                agent_topology=agent_topology,
            )
            prompts += 1
            if _has_recovery_instruction(messages):
                recovery_prompt_hits += 1
                pre_block_recovery_prompt_hits += 1
                if task["risk_label"] == "safe_control":
                    safe_control_recovery_prompt_hits += 1

            event = execute_step(step, aliases, world, runtime, defense)
            if step.save_as and event.output_ref:
                aliases[step.save_as] = event.output_ref
            recoverable_block = recovery_enabled and _is_recoverable_sink_block(event)
            if event.blocked and event.action in SINK_TOOLS:
                blocked_sinks += 1
            if recoverable_block:
                recoverable_sink_blocks += 1
            visible_trace.append(
                _visible_event(event, recovery_instruction=recoverable_block)
            )

            if recoverable_block:
                recovery_messages = build_messages(
                    task=task,
                    visible_trace=visible_trace,
                    policy_prompt=policy_prompt,
                    include_source_ref_instruction=include_source_ref_instruction,
                    agent_topology=agent_topology,
                )
                prompts += 1
                post_block_recovery_prompts += 1
                if _has_recovery_instruction(recovery_messages):
                    recovery_prompt_hits += 1
                    if task["risk_label"] == "safe_control":
                        safe_control_recovery_prompt_hits += 1

            if event.blocked or event.action in SINK_TOOLS or event.action == "final_answer":
                break

    expected_recovery_prompt_hits = recoverable_sink_blocks if recovery_enabled else 0
    passed = (
        recovery_prompt_hits == expected_recovery_prompt_hits
        and post_block_recovery_prompts == expected_recovery_prompt_hits
        and pre_block_recovery_prompt_hits == 0
        and safe_control_recovery_prompt_hits == 0
    )
    risky_tasks = sum(1 for task in tasks if task["risk_label"] == "risky")
    safe_tasks = len(tasks) - risky_tasks
    return {
        "condition": condition,
        "normalized_condition": defense_name,
        "agent_topology": agent_topology,
        "recovery_mode": recovery_mode,
        "max_steps": max_steps,
        "tasks": len(tasks),
        "risky_tasks": risky_tasks,
        "safe_control_tasks": safe_tasks,
        "prompts": prompts,
        "blocked_sinks": blocked_sinks,
        "recoverable_sink_blocks": recoverable_sink_blocks,
        "post_block_recovery_prompts": post_block_recovery_prompts,
        "recovery_prompt_hits": recovery_prompt_hits,
        "expected_recovery_prompt_hits": expected_recovery_prompt_hits,
        "pre_block_recovery_prompt_hits": pre_block_recovery_prompt_hits,
        "safe_control_recovery_prompt_hits": safe_control_recovery_prompt_hits,
        "pass": passed,
    }


def _has_recovery_instruction(messages: list[dict[str, str]]) -> bool:
    return RECOVERY_INSTRUCTION_TEXT in json.dumps(messages, sort_keys=True)


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
        "# API Recovery Prompt Audit",
        "",
        "This no-spend audit simulates scripted traces, builds the model-visible "
        "API messages, and verifies that the policy-compliant recovery instruction "
        "is serialized only in the first prompt after a defense-blocked write sink.",
        "",
        "| condition | max steps | prompts | blocked sinks | recovery prompts | pre-block hits | safe-control hits | pass |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {condition} | {max_steps} | {prompts} | {blocked} | {hits}/{expected} | "
            "{pre_block} | {safe_hits} | {passed} |".format(
                condition=row["condition"],
                max_steps=row["max_steps"],
                prompts=row["prompts"],
                blocked=row["blocked_sinks"],
                hits=row["recovery_prompt_hits"],
                expected=row["expected_recovery_prompt_hits"],
                pre_block=row["pre_block_recovery_prompt_hits"],
                safe_hits=row["safe_control_recovery_prompt_hits"],
                passed="yes" if row["pass"] else "no",
            )
        )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=[
            "api_local",
            "api_dlp",
            "api_visible_policy",
            "api_traceguard",
            "api_traceguard_inferred",
        ],
    )
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument(
        "--source-ref-mode",
        choices=["cooperative", "no_instruction", "drop_at_sink"],
        default="cooperative",
    )
    parser.add_argument(
        "--recovery-mode",
        choices=["stop", "after_block"],
        default="after_block",
    )
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = audit_recovery_prompts(
        load_tasks(args.tasks),
        conditions=args.conditions,
        max_steps=args.max_steps,
        source_ref_mode=args.source_ref_mode,
        recovery_mode=args.recovery_mode,
    )
    write_csv(rows, args.out_csv)
    write_md(rows, args.out_md)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
