from __future__ import annotations

from typing import Any

from tracebreak.env.schemas import Action, DataTag, Decision, Event, MemoryEntry, ToolValue
from tracebreak.env.world import World


class ToolRuntime:
    def __init__(self, world: World):
        self.world = world
        self.refs: dict[str, ToolValue] = {}
        self.events: list[Event] = []
        self._ref_counter = 0

    def next_ref(self) -> str:
        self._ref_counter += 1
        return f"obs_{self._ref_counter:03d}"

    def tag_for_refs(self, refs: list[str] | None) -> DataTag:
        tags: list[DataTag] = []
        for ref in refs or []:
            if ref in self.refs:
                tags.append(self.refs[ref].tag)
        return DataTag.merge(tags)

    def values_for_refs(self, refs: list[str] | None) -> list[Any]:
        return [self.refs[ref].value for ref in refs or [] if ref in self.refs]

    def append_blocked(
        self,
        action: Action,
        local_decision: Decision,
        defense_decision: Decision,
    ) -> Event:
        event = Event(
            step=len(self.events) + 1,
            actor=action.actor,
            action=action.action,
            arguments=action.arguments,
            local_decision=local_decision,
            defense_decision=defense_decision,
            blocked=True,
            observation={"status": "blocked", "reason": defense_decision.reason_code},
            tag=self.tag_for_refs(action.arguments.get("source_refs")),
        )
        self.events.append(event)
        return event

    def execute(
        self,
        action: Action,
        local_decision: Decision,
        defense_decision: Decision | None = None,
    ) -> Event:
        defense_decision = defense_decision or Decision.allow()
        tool_value = self._dispatch(action)

        output_ref = None
        if tool_value is not None:
            output_ref = self.next_ref()
            tool_value.ref = output_ref
            self.refs[output_ref] = tool_value
            observation = {"ref": output_ref, "value": tool_value.visible()}
            tag = tool_value.tag
        else:
            observation = {"status": "ok"}
            tag = DataTag.public()

        event = Event(
            step=len(self.events) + 1,
            actor=action.actor,
            action=action.action,
            arguments=action.arguments,
            local_decision=local_decision,
            defense_decision=defense_decision,
            blocked=False,
            output_ref=output_ref,
            observation=observation,
            tag=tag,
        )
        self.events.append(event)
        return event

    def _dispatch(self, action: Action) -> ToolValue | None:
        name = action.action
        args = action.arguments
        if name == "search_docs":
            return self.search_docs(args.get("query", args.get("arg", "")))
        if name == "read_doc":
            return self.read_doc(args["doc_id"])
        if name == "summarize":
            return self.summarize(args.get("source_refs", []))
        if name == "search_people":
            return self.search_people(args.get("query", args.get("arg", "")))
        if name == "send_email":
            return self.send_email(
                recipient_id=args["recipient_id"],
                subject=args.get("subject", ""),
                body=args.get("body", ""),
                source_refs=args.get("source_refs", []),
                approval_id=args.get("approval_id"),
                purpose=args.get("purpose"),
            )
        if name == "post_ticket":
            return self.post_ticket(
                customer_id=args["customer_id"],
                body=args.get("body", ""),
                source_refs=args.get("source_refs", []),
            )
        if name == "write_memory":
            return self.write_memory(
                key=args["key"],
                value=args.get("value", ""),
                source_refs=args.get("source_refs", []),
            )
        if name == "read_memory":
            return self.read_memory(args["key"])
        if name == "get_approval":
            return self.get_approval(args["approval_id"])
        if name == "search_approvals":
            return self.search_approvals(args.get("query", args.get("arg", "")))
        if name == "search_records":
            return self.search_records(
                region=args.get("region"), customer_id=args.get("customer_id")
            )
        if name == "read_record":
            return self.read_record(args["record_id"])
        if name == "aggregate_records":
            return self.aggregate_records(args.get("source_refs", []))
        if name == "final_answer":
            return ToolValue(value={"answer": args.get("text", "")}, tag=DataTag.public())
        raise KeyError(f"unknown tool {name}")

    def search_docs(self, query: str) -> ToolValue:
        query_lower = query.lower()
        rows = []
        for document in self.world.documents.values():
            haystack = " ".join([document.id, document.title, *document.tags]).lower()
            if not query_lower or any(term in haystack for term in query_lower.split()):
                rows.append(
                    {
                        "id": document.id,
                        "title": document.title,
                        "snippet": document.body[:96],
                    }
                )
        return ToolValue(value=rows, tag=DataTag.public())

    def read_doc(self, doc_id: str) -> ToolValue:
        document = self.world.documents[doc_id]
        return ToolValue(
            value={"id": document.id, "title": document.title, "body": document.body},
            tag=document.data_tag(),
        )

    def summarize(self, source_refs: list[str]) -> ToolValue:
        values = self.values_for_refs(source_refs)
        text = " ".join(str(value) for value in values)
        summary = text[:220] + ("..." if len(text) > 220 else "")
        return ToolValue(
            value={"summary": f"Concise summary: {summary}"},
            tag=self.tag_for_refs(source_refs),
        )

    def search_people(self, query: str) -> ToolValue:
        query_lower = query.lower()
        rows = []
        for person in self.world.people.values():
            haystack = " ".join([person.id, person.name, person.email, person.role]).lower()
            if not query_lower or any(term in haystack for term in query_lower.split()):
                rows.append(person.visible_dict())
        return ToolValue(value=rows, tag=DataTag.public())

    def send_email(
        self,
        recipient_id: str,
        subject: str,
        body: str,
        source_refs: list[str] | None = None,
        approval_id: str | None = None,
        purpose: str | None = None,
    ) -> ToolValue:
        tag = self.tag_for_refs(source_refs)
        email = {
            "recipient_id": recipient_id,
            "subject": subject,
            "body": body,
            "source_refs": list(source_refs or []),
            "approval_id": approval_id,
            "purpose": purpose,
            "tag": tag.to_dict(),
        }
        self.world.sent_emails.append(email)
        return ToolValue(value={"sent": True, "recipient_id": recipient_id}, tag=tag)

    def post_ticket(
        self, customer_id: str, body: str, source_refs: list[str] | None = None
    ) -> ToolValue:
        tag = self.tag_for_refs(source_refs)
        ticket = {
            "customer_id": customer_id,
            "body": body,
            "source_refs": list(source_refs or []),
            "tag": tag.to_dict(),
        }
        self.world.posted_tickets.append(ticket)
        return ToolValue(value={"posted": True, "customer_id": customer_id}, tag=tag)

    def write_memory(self, key: str, value: str, source_refs: list[str] | None = None) -> ToolValue:
        tag = self.tag_for_refs(source_refs)
        self.world.memory[key] = MemoryEntry(key=key, value=value, tag=tag)
        return ToolValue(value={"key": key, "value": value}, tag=tag)

    def read_memory(self, key: str) -> ToolValue:
        entry = self.world.memory[key]
        return ToolValue(value={"key": key, "value": entry.value}, tag=entry.tag)

    def get_approval(self, approval_id: str) -> ToolValue:
        return ToolValue(
            value=self.world.approvals[approval_id].visible_dict(), tag=DataTag.public()
        )

    def search_approvals(self, query: str) -> ToolValue:
        query_lower = query.lower()
        rows = []
        for approval in self.world.approvals.values():
            haystack = " ".join(
                [
                    approval.id,
                    approval.object_id,
                    approval.recipient_id,
                    approval.purpose,
                    approval.expires_at,
                ]
            ).lower()
            if not query_lower or any(term in haystack for term in query_lower.split()):
                rows.append(approval.visible_dict())
        return ToolValue(value=rows, tag=DataTag.public())

    def search_records(
        self, region: str | None = None, customer_id: str | None = None
    ) -> ToolValue:
        rows = []
        source_ids = set()
        tenants = set()
        for record in self.world.records.values():
            if region and record.region != region:
                continue
            if customer_id and record.customer_id != customer_id:
                continue
            rows.append({"id": record.id, "region": record.region, "customer_id": record.customer_id})
            source_ids.add(record.id)
            if record.customer_id:
                tenants.add(record.customer_id)
        tag = DataTag(
            source_ids=source_ids,
            derived_from=set(source_ids),
            sensitivity="internal" if rows else "public",
            tenants=tenants,
            external_share=True,
            record_count=len(rows),
            aggregate_only=False,
        )
        return ToolValue(value=rows, tag=tag)

    def read_record(self, record_id: str) -> ToolValue:
        record = self.world.records[record_id]
        return ToolValue(value={"id": record.id, "body": record.body}, tag=record.data_tag())

    def aggregate_records(self, source_refs: list[str]) -> ToolValue:
        source_tag = self.tag_for_refs(source_refs)
        source_count = source_tag.record_count
        if source_count == 0:
            for value in self.values_for_refs(source_refs):
                if isinstance(value, list):
                    source_count += len(value)
        aggregate_tag = DataTag(
            source_ids=set(source_tag.source_ids),
            derived_from=set(source_tag.derived_from) | set(source_tag.source_ids),
            sensitivity="public",
            tenants=set(),
            allowed_audience=set(),
            external_share=True,
            record_count=source_count,
            aggregate_only=True,
        )
        return ToolValue(
            value={
                "summary": f"Aggregate statistics over {source_count} records.",
                "record_count": source_count,
            },
            tag=aggregate_tag,
        )
