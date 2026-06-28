from __future__ import annotations

from tracebreak.env.schemas import Action, Decision
from tracebreak.env.tools import ToolRuntime
from tracebreak.env.world import World


KNOWN_TOOLS = {
    "search_docs",
    "read_doc",
    "summarize",
    "search_people",
    "send_email",
    "post_ticket",
    "write_memory",
    "read_memory",
    "get_approval",
    "search_approvals",
    "search_records",
    "read_record",
    "aggregate_records",
    "final_answer",
}


def check_local(action: Action, world: World, runtime: ToolRuntime) -> Decision:
    name = action.action
    args = action.arguments
    if name not in KNOWN_TOOLS:
        return Decision.block("unknown_tool", f"Unknown tool: {name}")
    if name == "read_doc" and args.get("doc_id") not in world.documents:
        return Decision.block("missing_document")
    if name == "send_email" and args.get("recipient_id") not in world.people:
        return Decision.block("missing_recipient")
    if name == "post_ticket" and args.get("customer_id") not in world.customers:
        return Decision.block("missing_customer")
    if name == "read_memory" and args.get("key") not in world.memory:
        return Decision.block("missing_memory")
    if name == "get_approval" and args.get("approval_id") not in world.approvals:
        return Decision.block("missing_approval")
    if args.get("approval_id") and args.get("approval_id") not in world.approvals:
        return Decision.block("missing_approval")
    if name == "read_record" and args.get("record_id") not in world.records:
        return Decision.block("missing_record")
    for ref in args.get("source_refs", []) or []:
        if ref not in runtime.refs:
            return Decision.block("missing_source_ref", f"Missing source ref: {ref}")
    return Decision.allow()
