from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tracebreak.agents.openai_client import OpenAIChatClient, extract_message_text
from tracebreak.agents.prompts import build_messages
from tracebreak.env.schemas import Action, Decision
from tracebreak.env.tools import ToolRuntime
from tracebreak.env.world import World
from tracebreak.experiments.run_condition import (
    defense_for_condition,
    grade_trace,
    load_tasks,
    write_jsonl,
)
from tracebreak.policies.local_guards import check_local


def normalize_condition(condition: str) -> str:
    if condition.startswith("api_"):
        return condition.removeprefix("api_")
    return condition


def parse_model_action(content: str) -> Action:
    action_payload = json.loads(content)
    action_name = (
        action_payload.get("action")
        or action_payload.get("tool")
        or action_payload.get("name")
        or action_payload.get("tool_name")
    )
    if not action_name:
        raise ValueError(f"missing action field: {action_payload}")
    arguments = (
        action_payload.get("arguments")
        or action_payload.get("args")
        or action_payload.get("parameters")
        or {}
    )
    if not isinstance(arguments, dict):
        raise ValueError(f"arguments must be an object: {action_payload}")
    return Action(action=str(action_name), arguments=arguments, actor="api_agent")


def normalize_action(action: Action, world: World, runtime: ToolRuntime) -> Action:
    args = dict(action.arguments)

    if "arg" in args and "query" not in args and action.action in {
        "search_docs",
        "search_people",
        "search_approvals",
    }:
        args["query"] = args.pop("arg")

    if action.action == "read_doc" and args.get("doc_id") not in world.documents:
        replacement = _match_by_text(args.get("doc_id"), world.documents)
        if replacement:
            args["doc_id"] = replacement

    if action.action == "read_record" and args.get("record_id") not in world.records:
        replacement = _match_by_text(args.get("record_id"), world.records)
        if replacement:
            args["record_id"] = replacement

    if action.action == "get_approval" and args.get("approval_id") not in world.approvals:
        replacement = _match_by_text(args.get("approval_id"), world.approvals)
        if replacement:
            args["approval_id"] = replacement

    if action.action == "send_email":
        recipient_id = args.get("recipient_id")
        if recipient_id not in world.people:
            replacement = _match_person(recipient_id, world)
            if replacement:
                args["recipient_id"] = replacement

    if action.action == "post_ticket":
        customer_id = args.get("customer_id")
        if customer_id not in world.customers:
            replacement = _match_by_text(customer_id, world.customers)
            if replacement:
                args["customer_id"] = replacement

    if "source_refs" in args:
        args["source_refs"] = _normalize_source_refs(args["source_refs"], runtime)

    return Action(action=action.action, arguments=args, actor=action.actor)


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").lower().replace("_", " ").replace("-", " ").split())


def _match_by_text(value: Any, objects: dict[str, Any]) -> str | None:
    needle = _norm_text(value)
    if not needle:
        return None
    for object_id, obj in objects.items():
        fields = [object_id]
        for attr in ("name", "title", "email", "purpose"):
            if hasattr(obj, attr):
                fields.append(getattr(obj, attr))
        haystack = _norm_text(" ".join(str(field) for field in fields))
        if needle == _norm_text(object_id) or needle in haystack or haystack in needle:
            return object_id
    return None


def _match_person(value: Any, world: World) -> str | None:
    return _match_by_text(value, world.people)


def _normalize_source_refs(value: Any, runtime: ToolRuntime) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    refs: list[str] = []
    for item in values:
        if isinstance(item, str) and item in runtime.refs:
            refs.append(item)
            continue
        replacement = _ref_for_object_id(item, runtime)
        if replacement:
            refs.append(replacement)
    return refs


def _ref_for_object_id(value: Any, runtime: ToolRuntime) -> str | None:
    needle = str(value or "")
    if not needle:
        return None
    for ref, tool_value in reversed(list(runtime.refs.items())):
        payload = tool_value.value
        if isinstance(payload, dict) and payload.get("id") == needle:
            return ref
        if isinstance(payload, dict) and payload.get("key") == needle:
            return ref
        if isinstance(payload, dict) and payload.get("record_count") is not None:
            # Aggregates are only safe to infer from their explicit observation ref.
            continue
    return None


def run_api_task(
    task: dict[str, Any],
    *,
    condition: str,
    client: OpenAIChatClient,
    max_steps: int,
) -> dict[str, Any]:
    world = World.from_seed(task["world_seed"])
    runtime = ToolRuntime(world)
    defense_name = normalize_condition(condition)
    defense = defense_for_condition(defense_name)
    policy_prompt = defense_name in {"policy_prompt", "visible_policy"}
    visible_trace: list[dict[str, Any]] = []
    model_calls = 0
    parse_errors = 0

    for _ in range(max_steps):
        messages = build_messages(
            task=task,
            visible_trace=visible_trace,
            policy_prompt=policy_prompt,
        )
        response = client.chat_json(messages)
        model_calls += 1
        content = extract_message_text(response)
        try:
            action = normalize_action(parse_model_action(content), world, runtime)
        except Exception:
            parse_errors += 1
            action = Action(
                "final_answer",
                {"text": f"Could not parse model action: {content[:160]}"},
                actor="api_agent",
            )

        local_decision = check_local(action, world, runtime)
        if local_decision.decision != "allow":
            event = runtime.append_blocked(action, local_decision, local_decision)
        else:
            defense_decision = defense.before_action(action, world, runtime) if defense else Decision.allow()
            if defense_decision.decision != "allow":
                event = runtime.append_blocked(action, local_decision, defense_decision)
            else:
                event = runtime.execute(action, local_decision, defense_decision)

        visible_trace.append(
            {
                "step": event.step,
                "action": event.action,
                "arguments": event.arguments,
                "blocked": event.blocked,
                "observation": event.observation,
            }
        )
        if event.blocked or event.action in {"send_email", "post_ticket", "final_answer"}:
            break

    metrics = grade_trace(task, world, runtime.events)
    metrics["model_calls"] = model_calls
    metrics["parse_errors"] = parse_errors
    return {
        "run_id": f"{condition}_{client.model}_{task['task_id']}",
        "condition": condition,
        "model": client.model,
        "task_id": task["task_id"],
        "category": task["category"],
        "risk_label": task["risk_label"],
        "world_seed": task["world_seed"],
        "trace": [event.to_dict() for event in runtime.events],
        "visible_trace": visible_trace,
        "metrics": metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="data/tasks_tracebreak_120.jsonl")
    parser.add_argument("--condition", default="api_local")
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--api-key-path", default="../apikey.txt")
    parser.add_argument("--cache-dir", default="results/api_cache")
    parser.add_argument("--out", required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--max-steps", type=int, default=8)
    args = parser.parse_args()

    tasks = load_tasks(args.tasks)
    if args.offset:
        tasks = tasks[args.offset :]
    if args.limit is not None:
        tasks = tasks[: args.limit]
    client = OpenAIChatClient(
        api_key_path=args.api_key_path,
        model=args.model,
        cache_dir=args.cache_dir,
    )
    rows = [
        run_api_task(task, condition=args.condition, client=client, max_steps=args.max_steps)
        for task in tasks
    ]
    write_jsonl(rows, args.out)
    print(f"wrote {len(rows)} API runs to {args.out}")


if __name__ == "__main__":
    main()
