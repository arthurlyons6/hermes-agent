"""Acceptance tests for launch document workflow."""
from __future__ import annotations

import sys
from pathlib import Path

_LAUNCH_ROOT = Path(__file__).resolve().parent.parent
if str(_LAUNCH_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAUNCH_ROOT))

import pytest

from document_workflow import DocumentWorkflow, SectionDraft
from evidence_ledger import EvidenceEntry, StatementClass


def test_document_workflow_outline_and_assignment() -> None:
    workflow = DocumentWorkflow(document_name="black-golf-doc")
    workflow.set_outline(["a", "b"])
    workflow.assign_section("a", "Miles")
    workflow.assign_section("b", "Naomi")
    package = workflow.to_package()
    assert package["document_name"] == "black-golf-doc"
    assert package["outline"] == ["a", "b"]
    assert package["assignments"]["a"] == "Miles"
    assert package["assignments"]["b"] == "Naomi"


def test_document_workflow_evidence_and_review() -> None:
    workflow = DocumentWorkflow(document_name="evidence-doc")
    workflow.set_outline(["section-1"])
    workflow.classify_statement(
        evidence_id="E1",
        source_uri="file://source.pdf",
        statement_class=StatementClass.MANAGEMENT_CLAIM,
        confidence=0.8,
        owner_slot="Arthur",
    )
    workflow.record_section_review("section-1", "factual", "passed")
    workflow.mark_section_promptfoo("section-1", True)
    workflow.record_render(Path("out/doc.pdf"), "inspected")
    workflow.record_rollback(False, [])
    package = workflow.to_package()
    assert package["ledger"]["count"] == 1
    assert package["sections"]["section-1"]["review"]["factual"] == "passed"
    assert package["sections"]["section-1"]["passed_promptfoo"] is True
    assert package["evaluation"]["render"]["output_path"] == "out/doc.pdf"
    assert package["evaluation"]["rollback"]["need_retry"] is False


def test_document_workflow_missing_section_raises() -> None:
    workflow = DocumentWorkflow(document_name="err-doc")
    with pytest.raises(KeyError):
        workflow.assign_section("missing", "Miles")
    with pytest.raises(KeyError):
        workflow.record_section_review("missing", "factual", "passed")
