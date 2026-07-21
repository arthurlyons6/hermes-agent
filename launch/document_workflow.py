"""Document worker base: ingestion, evidence ledger, outline, assignment, render package."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence_ledger import EvidenceEntry, EvidenceLedger, StatementClass


@dataclass
class SourceMaterial:
    name: str
    uri: str
    content_type: str = "application/octet-stream"
    bytes_: int | None = None
    checksum_sha256: str | None = None
    approved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SectionDraft:
    section_name: str
    title: str
    content_path: Path
    statement_classes: dict[StatementClass, int] = field(default_factory=dict)
    passed_promptfoo: bool = False
    review: dict[str, str] = field(default_factory=lambda: {
        "factual": "pending",
        "financial": "pending",
        "legal": "pending",
        "editorial": "pending",
    })


class DocumentWorkflow:
    def __init__(self, document_name: str) -> None:
        self.document_name = document_name
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.sources: list[SourceMaterial] = []
        self.ledger = EvidenceLedger()
        self.outline: list[str] = []
        self.drafts: dict[str, SectionDraft] = {}
        self.assignments: dict[str, str] = {}
        self.evaluation: dict[str, Any] = {
            "promptfoo": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "failed_sections": [],
            },
            "render": {
                "format": "pdf",
                "status": "pending",
                "output_path": None,
                "inspection_status": "pending",
            },
            "rollback": {
                "need_retry": False,
                "failure_points": [],
            },
        }

    def ingest_source(self, source: SourceMaterial) -> None:
        if not source.approved:
            raise ValueError("source material must be approved before ingestion")
        self.sources.append(source)

    def set_outline(self, outline: list[str]) -> None:
        self.outline = list(outline)
        for section in outline:
            if section not in self.drafts:
                self.drafts[section] = SectionDraft(
                    section_name=section,
                    title=section.replace("-", " ").title(),
                    content_path=Path("out") / f"{section}.md",
                )

    def assign_section(self, section_name: str, specialist: str) -> None:
        if section_name not in self.drafts:
            raise KeyError(f"section not in outline: {section_name}")
        self.assignments[section_name] = specialist

    def classify_statement(
        self,
        *,
        evidence_id: str,
        source_uri: str,
        statement_class: StatementClass,
        confidence: float = 1.0,
        owner_slot: str | None = None,
        linked_claims: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceEntry:
        entry = EvidenceEntry(
            evidence_id=evidence_id,
            source_uri=source_uri,
            statement_class=statement_class,
            confidence=confidence,
            owner_slot=owner_slot,
            linked_claims=linked_claims or [],
            metadata=metadata or {},
        )
        self.ledger.add(entry)
        return entry

    def record_section_review(self, section_name: str, review_type: str, status: str) -> None:
        section = self.drafts.get(section_name)
        if not section:
            raise KeyError(f"section not found: {section_name}")
        if review_type not in section.review:
            raise KeyError(f"unknown review type: {review_type}")
        section.review[review_type] = status

    def mark_section_promptfoo(self, section_name: str, passed: bool) -> None:
        section = self.drafts.get(section_name)
        if not section:
            raise KeyError(f"section not found: {section_name}")
        section.passed_promptfoo = passed
        self.evaluation["promptfoo"]["total_checks"] += 1
        if passed:
            self.evaluation["promptfoo"]["passed"] += 1
        else:
            self.evaluation["promptfoo"]["failed"] += 1
            self.evaluation["promptfoo"]["failed_sections"].append(section_name)

    def record_render(self, output_path: Path | str | None, inspection_status: str) -> None:
        self.evaluation["render"]["output_path"] = str(output_path) if output_path else None
        self.evaluation["render"]["status"] = "rendered" if output_path else "failed"
        self.evaluation["render"]["inspection_status"] = inspection_status

    def record_rollback(self, need_retry: bool, failure_points: list[str]) -> None:
        self.evaluation["rollback"]["need_retry"] = need_retry
        self.evaluation["rollback"]["failure_points"] = failure_points

    def to_package(self) -> dict[str, Any]:
        return {
            "document_name": self.document_name,
            "created_at": self.created_at,
            "sources": [
                {
                    "name": s.name,
                    "uri": s.uri,
                    "content_type": s.content_type,
                    "bytes": s.bytes_,
                    "checksum_sha256": s.checksum_sha256,
                    "approved": s.approved,
                    "metadata": s.metadata,
                }
                for s in self.sources
            ],
            "outline": self.outline,
            "assignments": self.assignments,
            "sections": {
                section: {
                    "title": draft.title,
                    "content_path": str(draft.content_path),
                    "statement_classes": {k.value: v for k, v in draft.statement_classes.items()},
                    "passed_promptfoo": draft.passed_promptfoo,
                    "review": draft.review,
                }
                for section, draft in self.drafts.items()
            },
            "ledger": self.ledger.to_package(),
            "evaluation": self.evaluation,
        }
