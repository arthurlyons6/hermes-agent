"""Offboarding/financial plan test scenarios and acceptance gates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from document_workflow import DocumentWorkflow


@dataclass
class FinancialGate:
    name: str
    required_fields: list[str]
    denominator_note: str = "All financial gates require explicit source or approved assumption."


FACTUAL_GATES: Sequence[str] = (
    "verified_fact",
    "management_claim",
    "assumption",
    "estimate",
    "projection",
)

FINANCIAL_GATES: Sequence[FinancialGate] = (
    FinancialGate(
        name="revenue_model_validation",
        required_fields=[
            "revenue_source",
            "volume_or_price_driver",
            "time_horizon",
            "assumption_class",
        ],
        denominator_note="Do not accept gross margin expansion without underlying unit behavior.",
    ),
    FinancialGate(
        name="cost_stack_discipline",
        required_fields=[
            "fixed_cost_total",
            "variable_cost_per_unit",
            "break_even_inputs",
            "sensitivity_range",
        ],
        denominator_note="Use approved estimates only when every driver is explicit.",
    ),
    FinancialGate(
        name="capital_structure_guardrails",
        required_fields=[
            "debt_instrument",
            "interest_terms",
            "priority_and_covenants",
            "source",
        ],
        denominator_note="Do not present undrawn facilities as cash or equity.",
    ),
    FinancialGate(
        name="liquidity_and_coverage",
        required_fields=[
            "minimum_liquidity_balance",
            "coverage_ratio_formula",
            "source_period",
        ],
        denominator_note="Coverage must reference the same period as the source.",
    ),
)


def apply_financial_acceptance(workflow: DocumentWorkflow) -> None:
    workflow.evaluation.setdefault("financial", {})
    workflow.evaluation["financial"]["gates"] = [
        {
            "name": gate.name,
            "required_fields": gate.required_fields,
            "denominator_note": gate.denominator_note,
            "status": "pending_evidence",
        }
        for gate in FINANCIAL_GATES
    ]
    workflow.evaluation["promptfoo"]["expected_sections"] = [
        "Executive Summary",
        "Evidence Ledger",
        "Financial Review",
        "Legal Review",
        "Editorial Review",
        "Confidentiality Notice",
    ]
