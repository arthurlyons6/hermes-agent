"""Evidence ledger data model."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StatementClass(str, Enum):
    VERIFIED_FACT = "verified_fact"
    MANAGEMENT_CLAIM = "management_claim"
    ASSUMPTION = "assumption"
    ESTIMATE = "estimate"
    PROJECTION = "projection"


@dataclass
class EvidenceEntry:
    evidence_id: str
    source_uri: str
    page_or_section: str | None = None
    extracted_text: str | None = None
    statement_class: StatementClass = StatementClass.VERIFIED_FACT
    confidence: float = 1.0
    owner_slot: str | None = None
    linked_claims: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class EvidenceLedger:
    def __init__(self) -> None:
        self.entries: dict[str, EvidenceEntry] = {}

    def add(self, entry: EvidenceEntry) -> None:
        self.entries[entry.evidence_id] = entry

    def get(self, evidence_id: str) -> EvidenceEntry | None:
        return self.entries.get(evidence_id)

    def to_package(self) -> dict[str, Any]:
        return {
            "count": len(self.entries),
            "items": [
                {
                    "evidence_id": entry.evidence_id,
                    "source_uri": entry.source_uri,
                    "page_or_section": entry.page_or_section,
                    "statement_class": entry.statement_class.value,
                    "confidence": entry.confidence,
                    "owner_slot": entry.owner_slot,
                    "linked_claims": entry.linked_claims,
                    "metadata": entry.metadata,
                }
                for entry in self.entries.values()
            ],
        }
