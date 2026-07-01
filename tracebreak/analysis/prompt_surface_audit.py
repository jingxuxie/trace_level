from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from tracebreak.agents.prompts import build_messages
from tracebreak.experiments.run_api_condition import infer_agent_topology, normalize_condition
from tracebreak.experiments.run_condition import (
    SINK_TOOLS,
    defense_for_condition,
    execute_step,
    load_tasks,
)
from tracebreak.experiments.scripted import build_scripted_plan
from tracebreak.env.tools import ToolRuntime
from tracebreak.env.world import World


HIDDEN_METADATA_KEYS = [
    "tag",
    "source_ids",
    "derived_from",
    "sensitivity",
    "tenants",
    "allowed_audience",
    "external_share",
    "aggregate_only",
]

TASK_LABEL_KEYS = [
    "task_id",
    "category",
    "risk_label",
    "world_seed",
    "params",
    "expected_sink",
    "safe_control_pair",
]


def audit_prompt_surface(
    tasks: list[dict[str, Any]],
    *,
    conditions: list[str],
    max_steps: int = 8,
    include_source_ref_instruction: bool = True,
) -> list[dict[str, Any]]:
    return [
        audit_condition(
            tasks,
            condition=condition,
            max_steps=max_steps,
            include_source_ref_instruction=include_source_ref_instruction,
        )
        for condition in conditions
    ]


def audit_condition(
    tasks: list[dict[str, Any]],
    *,
    condition: str,
    max_steps: int,
    include_source_ref_instruction: bool,
) -> dict[str, Any]:
    defense_name = normalize_condition(condition)
    defense = defense_for_condition(defense_name)
    policy_prompt = defense_name in {"policy_prompt", "visible_policy"}
    agent_topology = infer_agent_topology(condition)
    scaffold = "multi" if agent_topology == "multi" else "single"

    prompts = 0
    hidden_prompt_hits = 0
    label_prompt_hits = 0
    source_ref_prompt_hits = 0
    policy_prompt_hits = 0
    multi_agent_prompt_hits = 0
    hidden_keys_found: set[str] = set()
    label_keys_found: set[str] = set()

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
            prompt_text = json.dumps(messages, sort_keys=True)
            prompts += 1

            hidden_hits = _present_json_keys(prompt_text, HIDDEN_METADATA_KEYS)
            label_hits = _present_json_keys(prompt_text, TASK_LABEL_KEYS)
            if hidden_hits:
                hidden_prompt_hits += 1
                hidden_keys_found.update(hidden_hits)
            if label_hits:
                label_prompt_hits += 1
                label_keys_found.update(label_hits)
            if 'include it in \\"source_refs\\"' in prompt_text:
                source_ref_prompt_hits += 1
            if "Security policy:" in prompt_text:
                policy_prompt_hits += 1
            if "Multi-agent topology:" in prompt_text:
                multi_agent_prompt_hits += 1

            event = execute_step(step, aliases, world, runtime, defense)
            if step.save_as and event.output_ref:
                aliases[step.save_as] = event.output_ref
            visible_trace.append(_visible_event(event))
            if event.blocked or event.action in SINK_TOOLS or event.action == "final_answer":
                break

    expected_source_ref_prompts = prompts if include_source_ref_instruction else 0
    expected_policy_prompts = prompts if policy_prompt else 0
    expected_multi_agent_prompts = prompts if agent_topology == "multi" else 0
    passed = (
        hidden_prompt_hits == 0
        and label_prompt_hits == 0
        and source_ref_prompt_hits == expected_source_ref_prompts
        and policy_prompt_hits == expected_policy_prompts
        and multi_agent_prompt_hits == expected_multi_agent_prompts
    )
    return {
        "condition": condition,
        "normalized_condition": defense_name,
        "agent_topology": agent_topology,
        "tasks": len(tasks),
        "prompts": prompts,
        "hidden_metadata_prompt_hits": hidden_prompt_hits,
        "hidden_metadata_keys_found": ";".join(sorted(hidden_keys_found)),
        "task_label_prompt_hits": label_prompt_hits,
        "task_label_keys_found": ";".join(sorted(label_keys_found)),
        "source_ref_instruction_hits": source_ref_prompt_hits,
        "expected_source_ref_instruction_hits": expected_source_ref_prompts,
        "policy_prompt_hits": policy_prompt_hits,
        "expected_policy_prompt_hits": expected_policy_prompts,
        "multi_agent_prompt_hits": multi_agent_prompt_hits,
        "expected_multi_agent_prompt_hits": expected_multi_agent_prompts,
        "pass": passed,
    }


def _visible_event(event) -> dict[str, Any]:
    return {
        "step": event.step,
        "actor": event.actor,
        "action": event.action,
        "arguments": event.arguments,
        "blocked": event.blocked,
        "observation": event.observation,
    }


def _present_json_keys(text: str, keys: list[str]) -> list[str]:
    return [key for key in keys if f'\"{key}\"' in text]


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
        "# API Prompt-Surface Audit",
        "",
        "This no-spend audit builds the model-visible API messages along scripted "
        "traces and checks that hidden provenance-tag keys and benchmark labels "
        "are not serialized into prompts. It also verifies that policy-prompt "
        "and multi-agent topology instructions appear only in the expected "
        "conditions.",
        "",
        "| condition | topology | prompts | hidden metadata hits | task label hits | source-ref instruction | policy prompt | multi-agent prompt | pass |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {condition} | {topology} | {prompts} | {hidden} | {labels} | "
            "{source_refs}/{source_ref_expected} | {policy}/{policy_expected} | "
            "{multi}/{multi_expected} | {passed} |".format(
                condition=row["condition"],
                topology=row["agent_topology"],
                prompts=row["prompts"],
                hidden=row["hidden_metadata_prompt_hits"],
                labels=row["task_label_prompt_hits"],
                source_refs=row["source_ref_instruction_hits"],
                source_ref_expected=row["expected_source_ref_instruction_hits"],
                policy=row["policy_prompt_hits"],
                policy_expected=row["expected_policy_prompt_hits"],
                multi=row["multi_agent_prompt_hits"],
                multi_expected=row["expected_multi_agent_prompt_hits"],
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
            "api_policy_prompt",
            "api_visible_policy",
            "api_traceguard",
            "api_traceguard_inferred",
            "api_multi_traceguard",
        ],
    )
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = audit_prompt_surface(
        load_tasks(args.tasks),
        conditions=args.conditions,
        max_steps=args.max_steps,
    )
    write_csv(rows, args.out_csv)
    write_md(rows, args.out_md)
    print(f"wrote {args.out_csv}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
