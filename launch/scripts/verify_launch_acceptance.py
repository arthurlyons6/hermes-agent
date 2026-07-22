#!/usr/bin/env python3
"""Direct verification harness for launch acceptance tests."""
from __future__ import annotations

import sys
from pathlib import Path

_LAUNCH_ROOT = Path(__file__).resolve().parent.parent
if str(_LAUNCH_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAUNCH_ROOT))

from evidence_ledger import EvidenceLedger, EvidenceEntry, StatementClass
from document_workflow import DocumentWorkflow, SectionDraft


def run() -> int:
    errors = 0

    # Evidence ledger checks
    ledger = EvidenceLedger()
    entry = EvidenceEntry(
        evidence_id="E1",
        source_uri="file://approved/source.pdf",
        page_or_section="page 12",
        statement_class=StatementClass.VERIFIED_FACT,
        confidence=0.95,
        owner_slot="Miles",
        linked_claims=["C1"],
    )
    ledger.add(entry)
    if ledger.get("E1") is not entry:
        print("evidence_ledger: add/get mismatch")
        errors += 1
    if ledger.get("MISSING") is not None:
        print("evidence_ledger: missing entry should be None")
        errors += 1
    pkg = ledger.to_package()
    if pkg["count"] != 1 or pkg["items"][0]["statement_class"] != "verified_fact":
        print("evidence_ledger: package shape unexpected")
        errors += 1

    # Document workflow checks
    workflow = DocumentWorkflow(document_name="black-golf-doc")
    workflow.set_outline(["a", "b"])
    workflow.assign_section("a", "Miles")
    workflow.assign_section("b", "Naomi")
    package = workflow.to_package()
    if package["document_name"] != "black-golf-doc" or package["outline"] != ["a", "b"]:
        print("document_workflow: outline mismatch")
        errors += 1
    if package["assignments"].get("a") != "Miles":
        print("document_workflow: assignment mismatch")
        errors += 1
    workflow.record_section_review("a", "factual", "passed")
    workflow.record_render(Path("out/doc.pdf"), "inspected")
    workflow.record_rollback(False, [])
    package = workflow.to_package()
    if package["sections"]["a"]["review"]["factual"] != "passed":
        print("document_workflow: review mismatch")
        errors += 1
    if package["evaluation"]["render"]["output_path"] != str(Path("out/doc.pdf")):
        print("document_workflow: render path mismatch")
        errors += 1
    if package["evaluation"]["rollback"]["need_retry"] is not False:
        print("document_workflow: rollback mismatch")
        errors += 1
    try:
        workflow.assign_section("missing", "X")
    except KeyError:
        pass
    else:
        print("document_workflow: missing assign_section should raise")
        errors += 1
    try:
        workflow.record_section_review("missing", "factual", "passed")
    except KeyError:
        pass
    else:
        print("document_workflow: missing record_section_review should raise")
        errors += 1

    if errors == 0:
        print("launch acceptance passed")
        return 0
    print(f"launch acceptance failed with {errors} error(s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
