"""Factory for the first institutional document workflow."""
from __future__ import annotations

from pathlib import Path
from document_workflow import DocumentWorkflow
from offboarding_plan import apply_financial_acceptance


def build_black_gold_business_plan_workflow() -> DocumentWorkflow:
    workflow = DocumentWorkflow(document_name="black-gold-business-plan")
    outline = [
        "executive-summary",
        "market-analysis",
        "operating-plan",
        "financial-model",
        "legal-review",
        "editorial-review",
        "evidence-ledger",
        "confidentiality",
    ]
    workflow.set_outline(outline)
    workflow.assign_section("executive-summary", "Arthur/Marcus")
    workflow.assign_section("market-analysis", "Arthur/Julian")
    workflow.assign_section("operating-plan", "Arthur/Olivia")
    workflow.assign_section("financial-model", "Malcolm")
    workflow.assign_section("legal-review", "Evelyn")
    workflow.assign_section("editorial-review", "Sophia")
    workflow.assign_section("evidence-ledger", "Naomi")
    workflow.assign_section("confidentiality", "Victor")
    apply_financial_acceptance(workflow)
    return workflow
