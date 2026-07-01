from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tracebreak.env.schemas import Action, Decision
from tracebreak.env.tools import ToolRuntime
from tracebreak.env.world import World
from tracebreak.experiments.run_condition import (
    SINK_TOOLS,
    defense_for_condition,
    grade_trace,
    load_tasks,
    write_jsonl,
)
from tracebreak.policies.local_guards import check_local


REPLAY_DEFENSES = {
    "dlp",
    "visible_policy",
    "metadata_critic",
    "traceguard",
    "traceguard_strict",
}
TOKEN_FIELDS = (
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "cached_prompt_tokens",
    "reasoning_tokens",
)


def read_rows(paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def replay_row(
    row: dict[str, Any],
    *,
    task: dict[str, Any],
    defense_name: str,
) -> dict[str, Any]:
    if defense_name not in REPLAY_DEFENSES:
        raise ValueError(f"unsupported replay defense: {defense_name}")

    world = World.from_seed(row["world_seed"])
    runtime = ToolRuntime(world)
    defense = defense_for_condition(defense_name)

    for event_payload in row["trace"]:
        action = Action(
            action=event_payload["action"],
            arguments=dict(event_payload.get("arguments", {})),
            actor=event_payload.get("actor", "api_agent"),
        )
        local_decision = check_local(action, world, runtime)
        if local_decision.decision != "allow":
            event = runtime.append_blocked(action, local_decision, local_decision)
        else:
            defense_decision = defense.before_action(action, world, runtime)
            if defense_decision.decision != "allow":
                event = runtime.append_blocked(action, local_decision, defense_decision)
            else:
                event = runtime.execute(action, local_decision, defense_decision)

        if event.blocked or event.action in SINK_TOOLS or event.action == "final_answer":
            break

    metrics = grade_trace(task, world, runtime.events)
    metrics["model_calls"] = row["metrics"].get("model_calls", "")
    metrics["parse_errors"] = row["metrics"].get("parse_errors", "")
    for field in TOKEN_FIELDS:
        if field in row["metrics"]:
            metrics[field] = row["metrics"].get(field, 0)

    condition = f"{row['condition']}_replay_{defense_name}"
    return {
        **row,
        "run_id": f"{condition}_{row['model']}_{row['task_id']}",
        "condition": condition,
        "base_condition": row["condition"],
        "replay_defense": defense_name,
        "counterfactual_replay": True,
        "trace": [event.to_dict() for event in runtime.events],
        "visible_trace": [
            {
                "step": event.step,
                "action": event.action,
                "arguments": event.arguments,
                "blocked": event.blocked,
                "observation": event.observation,
            }
            for event in runtime.events
        ],
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument("--defense", choices=sorted(REPLAY_DEFENSES), required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    task_by_id = {task["task_id"]: task for task in load_tasks(args.tasks)}
    rows = [
        replay_row(row, task=task_by_id[row["task_id"]], defense_name=args.defense)
        for row in read_rows(args.runs)
    ]
    write_jsonl(rows, args.out)
    print(f"wrote {len(rows)} replayed runs to {args.out}")


if __name__ == "__main__":
    main()
