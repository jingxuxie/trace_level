from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tracebreak.env.schemas import Action, DataTag, Decision, Event
from tracebreak.env.world import World
from tracebreak.policies.traceguard import RuntimeInferredTraceGuard, TraceGuard
from tracebreak.experiments.run_condition import SINK_TOOLS, grade_trace, load_tasks, write_jsonl


DERIVED_TOOLS = {"summarize", "write_memory", "aggregate_records"}


def read_rows(paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def replay_drop_at_sink(
    row: dict[str, Any],
    *,
    task: dict[str, Any],
    defense: str,
) -> dict[str, Any]:
    return replay_sink_source_ref_stress(
        row,
        task=task,
        defense=defense,
        stress_mode="drop_at_sink",
    )


def replay_sink_source_ref_stress(
    row: dict[str, Any],
    *,
    task: dict[str, Any],
    defense: str,
    stress_mode: str,
) -> dict[str, Any]:
    if defense not in {"traceguard", "traceguard_strict", "traceguard_inferred"}:
        raise ValueError(f"unsupported defense: {defense}")
    if stress_mode not in {"drop_at_sink", "corrupt_at_sink", "drop_intermediate"}:
        raise ValueError(f"unsupported stress mode: {stress_mode}")

    events: list[Event] = []
    missing_source_blocks = 0
    inferred_source_sinks = 0
    corrupted_source_sinks = 0
    erased_intermediate_sources = 0
    traceguard = TraceGuard()
    world = World.from_seed(row["world_seed"])
    for event_payload in row["trace"]:
        event = event_from_dict(event_payload)
        if (
            stress_mode == "drop_intermediate"
            and event.action in DERIVED_TOOLS
            and event.arguments.get("source_refs")
        ):
            erased_intermediate_sources += 1
            event.arguments = _without_source_refs(event.arguments)
            event.tag = DataTag.public()

        if event.action in SINK_TOOLS:
            if stress_mode == "drop_at_sink":
                event.arguments = _without_source_refs(event.arguments)
                event.tag = DataTag.public()
            elif stress_mode == "corrupt_at_sink":
                corrupted_source_sinks += 1
                refs = _benign_public_refs(events)
                event.arguments = _with_source_refs(event.arguments, refs)
                event.tag = _tag_for_refs(refs, events)
            else:
                event.tag = _tag_for_refs(event.arguments.get("source_refs", []), events)
            event.defense_decision = Decision.allow()
            event.blocked = False
            event.observation = {"status": "ok"}
            event.output_ref = None

            if (
                stress_mode == "drop_at_sink"
                and defense == "traceguard_strict"
                and _has_prior_policy_relevant_observation(events)
            ):
                missing_source_blocks += 1
                event.blocked = True
                event.defense_decision = Decision.block(
                    "missing_provenance_at_sink",
                    "Write sink has no source_refs after prior policy-relevant observations.",
                )
                event.observation = {
                    "status": "blocked",
                    "reason": "missing_provenance_at_sink",
                }
            elif defense == "traceguard_inferred":
                inferred_source_sinks += 1
                inferred_tag = infer_sink_tag(event, events)
                event.tag = inferred_tag
                decision = traceguard.evaluate(
                    Action(event.action, event.arguments, actor=event.actor),
                    world,
                    inferred_tag,
                )
                event.defense_decision = decision
                if decision.decision != "allow":
                    event.blocked = True
                    event.observation = {
                        "status": "blocked",
                        "reason": decision.reason_code,
                    }
            elif stress_mode in {"corrupt_at_sink", "drop_intermediate"}:
                decision = traceguard.evaluate(
                    Action(event.action, event.arguments, actor=event.actor),
                    world,
                    event.tag,
                )
                event.defense_decision = decision
                if decision.decision != "allow":
                    event.blocked = True
                    event.observation = {
                        "status": "blocked",
                        "reason": decision.reason_code,
                    }

        events.append(event)
        if event.blocked or event.action in SINK_TOOLS or event.action == "final_answer":
            break

    metrics = grade_trace(task, world, events)
    metrics["model_calls"] = row["metrics"].get("model_calls", "")
    metrics["parse_errors"] = row["metrics"].get("parse_errors", "")
    metrics["missing_source_blocks"] = missing_source_blocks
    metrics["inferred_source_sinks"] = inferred_source_sinks
    metrics["corrupted_source_sinks"] = corrupted_source_sinks
    metrics["erased_intermediate_sources"] = erased_intermediate_sources

    condition = f"{row['condition']}_{defense}_{stress_mode}_replay"
    # Keep labels concise for the common API TraceGuard source file.
    condition = condition.replace("api_traceguard_traceguard_", "api_traceguard_")
    condition = condition.replace(
        "api_traceguard_traceguard_strict_",
        "api_traceguard_strict_",
    )
    condition = condition.replace(
        "api_traceguard_traceguard_inferred_",
        "api_traceguard_inferred_",
    )
    return {
        **row,
        "run_id": f"{condition}_{row['model']}_{row['task_id']}",
        "condition": condition,
        "base_condition": row["condition"],
        "source_ref_mode": f"{stress_mode}_replay",
        "trace": [event.to_dict() for event in events],
        "visible_trace": [
            {
                "step": event.step,
                "action": event.action,
                "arguments": event.arguments,
                "blocked": event.blocked,
                "observation": event.observation,
            }
            for event in events
        ],
        "metrics": metrics,
    }


def event_from_dict(payload: dict[str, Any]) -> Event:
    return Event(
        step=payload["step"],
        actor=payload["actor"],
        action=payload["action"],
        arguments=dict(payload.get("arguments", {})),
        local_decision=Decision(**payload["local_decision"]),
        defense_decision=Decision(**payload["defense_decision"]),
        blocked=payload.get("blocked", False),
        output_ref=payload.get("output_ref"),
        observation=payload.get("observation"),
        tag=DataTag.from_dict(payload.get("tag", {})),
    )


def _without_source_refs(arguments: dict[str, Any]) -> dict[str, Any]:
    out = dict(arguments)
    out.pop("source_refs", None)
    return out


def _with_source_refs(arguments: dict[str, Any], refs: list[str]) -> dict[str, Any]:
    out = dict(arguments)
    out["source_refs"] = refs
    return out


def _benign_public_refs(events: list[Event]) -> list[str]:
    for event in reversed(events):
        if (
            not event.blocked
            and event.output_ref
            and not _policy_relevant_tag(event.tag)
        ):
            return [event.output_ref]
    return []


def _tag_for_refs(refs: list[str], events: list[Event]) -> DataTag:
    by_ref = {
        event.output_ref: event.tag
        for event in events
        if not event.blocked and event.output_ref
    }
    return DataTag.merge([by_ref[ref] for ref in refs if ref in by_ref])


def _has_prior_policy_relevant_observation(events: list[Event]) -> bool:
    return any(
        not event.blocked and _policy_relevant_tag(event.tag)
        for event in events
    )


def _policy_relevant_tag(tag: DataTag) -> bool:
    return (
        tag.sensitivity != "public"
        or bool(tag.tenants)
        or bool(tag.allowed_audience)
        or not tag.external_share
        or (tag.record_count > 0 and not tag.aggregate_only)
    )


def infer_sink_tag(sink_event: Event, prior_events: list[Event]) -> DataTag:
    """Infer a missing sink tag from runtime-owned prior event tags.

    This is intentionally simple and auditable. It is not a semantic dependency
    detector; it models a scaffold that can fall back to runtime provenance when
    the model omits sink source_refs.
    """

    action = Action(sink_event.action, sink_event.arguments, actor=sink_event.actor)
    return RuntimeInferredTraceGuard().infer_sink_tag(action, prior_events)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument(
        "--defense",
        choices=["traceguard", "traceguard_strict", "traceguard_inferred"],
        required=True,
    )
    parser.add_argument(
        "--stress-mode",
        choices=["drop_at_sink", "corrupt_at_sink", "drop_intermediate"],
        default="drop_at_sink",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    task_by_id = {task["task_id"]: task for task in load_tasks(args.tasks)}
    rows = []
    for row in read_rows(args.runs):
        rows.append(
            replay_sink_source_ref_stress(
                row,
                task=task_by_id[row["task_id"]],
                defense=args.defense,
                stress_mode=args.stress_mode,
            )
        )
    write_jsonl(rows, args.out)
    print(f"wrote {len(rows)} replayed runs to {args.out}")


if __name__ == "__main__":
    main()
