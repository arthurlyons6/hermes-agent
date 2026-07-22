"""Local acceptance harness for launch document workflow."""
from __future__ import annotations

import sys
from pathlib import Path

from document_workflow import DocumentWorkflow, SourceMaterial
from document_workflow_factory import build_black_gold_business_plan_workflow


def main() -> int:
    workflow = build_black_gold_business_plan_workflow()
    workflow.ingest_source(
        SourceMaterial(
            name="approved-brief",
            uri="file://approved/black-gold-brief.pdf",
            content_type="application/pdf",
            bytes_=1234,
            checksum_sha256="abcd",
            approved=True,
        )
    )
    workflow.classify_statement(
        evidence_id="E1",
        source_uri="file://approved/black-gold-brief.pdf",
        statement_class="verified_fact",
        confidence=0.95,
        owner_slot="Miles",
    )
    for section, specialist in workflow.assignments.items():
        workflow.record_section_review(section, "editorial", "passed")
    workflow.record_render(
        Path("launch/rendered/black-gold-business-plan.pdf"), "visual-inspection-passed"
    )
    pkg = workflow.to_package()
    print(__import__("json").dumps(pkg, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
