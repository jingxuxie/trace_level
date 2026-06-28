from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SENSITIVITY_ORDER = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "restricted": 3,
}


def max_sensitivity(values: list[str]) -> str:
    if not values:
        return "public"
    return max(values, key=lambda item: SENSITIVITY_ORDER.get(item, 0))


@dataclass
class DataTag:
    source_ids: set[str] = field(default_factory=set)
    derived_from: set[str] = field(default_factory=set)
    sensitivity: str = "public"
    tenants: set[str] = field(default_factory=set)
    allowed_audience: set[str] = field(default_factory=set)
    external_share: bool = True
    purpose: str | None = None
    expires_at: str | None = None
    record_count: int = 0
    aggregate_only: bool = False

    @classmethod
    def public(cls) -> "DataTag":
        return cls()

    @classmethod
    def merge(cls, tags: list["DataTag"]) -> "DataTag":
        if not tags:
            return cls.public()

        source_ids: set[str] = set()
        derived_from: set[str] = set()
        tenants: set[str] = set()
        audience_sets: list[set[str]] = []
        sensitivities: list[str] = []
        record_count = 0

        for tag in tags:
            source_ids.update(tag.source_ids)
            derived_from.update(tag.derived_from)
            derived_from.update(tag.source_ids)
            tenants.update(tag.tenants)
            sensitivities.append(tag.sensitivity)
            record_count += tag.record_count
            if tag.allowed_audience:
                audience_sets.append(set(tag.allowed_audience))

        if audience_sets:
            allowed_audience = set.intersection(*audience_sets)
        else:
            allowed_audience = set()

        return cls(
            source_ids=source_ids,
            derived_from=derived_from,
            sensitivity=max_sensitivity(sensitivities),
            tenants=tenants,
            allowed_audience=allowed_audience,
            external_share=all(tag.external_share for tag in tags),
            record_count=record_count,
            aggregate_only=all(tag.aggregate_only for tag in tags),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_ids": sorted(self.source_ids),
            "derived_from": sorted(self.derived_from),
            "sensitivity": self.sensitivity,
            "tenants": sorted(self.tenants),
            "allowed_audience": sorted(self.allowed_audience),
            "external_share": self.external_share,
            "purpose": self.purpose,
            "expires_at": self.expires_at,
            "record_count": self.record_count,
            "aggregate_only": self.aggregate_only,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DataTag":
        return cls(
            source_ids=set(payload.get("source_ids", [])),
            derived_from=set(payload.get("derived_from", [])),
            sensitivity=payload.get("sensitivity", "public"),
            tenants=set(payload.get("tenants", [])),
            allowed_audience=set(payload.get("allowed_audience", [])),
            external_share=payload.get("external_share", True),
            purpose=payload.get("purpose"),
            expires_at=payload.get("expires_at"),
            record_count=int(payload.get("record_count", 0)),
            aggregate_only=bool(payload.get("aggregate_only", False)),
        )


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    body: str
    sensitivity: str
    tenants: tuple[str, ...] = ()
    allowed_audience: tuple[str, ...] = ()
    external_share: bool = True
    tags: tuple[str, ...] = ()

    def data_tag(self) -> DataTag:
        return DataTag(
            source_ids={self.id},
            derived_from={self.id},
            sensitivity=self.sensitivity,
            tenants=set(self.tenants),
            allowed_audience=set(self.allowed_audience),
            external_share=self.external_share,
        )


@dataclass(frozen=True)
class Person:
    id: str
    name: str
    email: str
    role: str
    org: str
    is_external: bool
    tenant: str | None = None

    def visible_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "org": self.org,
            "is_external": self.is_external,
            "tenant": self.tenant,
        }


@dataclass(frozen=True)
class Customer:
    id: str
    name: str


@dataclass(frozen=True)
class Record:
    id: str
    body: str
    customer_id: str | None
    region: str
    sensitivity: str = "internal"
    external_share: bool = True

    def data_tag(self) -> DataTag:
        tenants = {self.customer_id} if self.customer_id else set()
        return DataTag(
            source_ids={self.id},
            derived_from={self.id},
            sensitivity=self.sensitivity,
            tenants=tenants,
            external_share=self.external_share,
            record_count=1,
        )


@dataclass(frozen=True)
class Approval:
    id: str
    object_id: str
    recipient_id: str
    purpose: str
    expires_at: str

    def visible_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "object_id": self.object_id,
            "recipient_id": self.recipient_id,
            "purpose": self.purpose,
            "expires_at": self.expires_at,
        }


@dataclass
class MemoryEntry:
    key: str
    value: str
    tag: DataTag


@dataclass
class ToolValue:
    value: Any
    tag: DataTag = field(default_factory=DataTag.public)
    ref: str | None = None

    def visible(self) -> Any:
        return self.value


@dataclass
class Action:
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    actor: str = "agent"

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor": self.actor,
            "action": self.action,
            "arguments": self.arguments,
        }


@dataclass
class Decision:
    decision: str
    reason_code: str = "allow"
    detail: str = ""
    source_ids: list[str] = field(default_factory=list)

    @classmethod
    def allow(cls) -> "Decision":
        return cls("allow", "allow")

    @classmethod
    def block(
        cls, reason_code: str, detail: str = "", source_ids: list[str] | None = None
    ) -> "Decision":
        return cls("block", reason_code, detail, source_ids or [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reason_code": self.reason_code,
            "detail": self.detail,
            "source_ids": self.source_ids,
        }


@dataclass
class Event:
    step: int
    actor: str
    action: str
    arguments: dict[str, Any]
    local_decision: Decision
    defense_decision: Decision
    blocked: bool = False
    output_ref: str | None = None
    observation: Any = None
    tag: DataTag = field(default_factory=DataTag.public)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "actor": self.actor,
            "action": self.action,
            "arguments": self.arguments,
            "local_decision": self.local_decision.to_dict(),
            "defense_decision": self.defense_decision.to_dict(),
            "blocked": self.blocked,
            "output_ref": self.output_ref,
            "observation": self.observation,
            "tag": self.tag.to_dict(),
        }
