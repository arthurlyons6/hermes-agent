"""Business Workflow Library for Lyons Command Center.

Standardized workflows for private equity, banking, and GCI operations.
Each workflow is a reusable sequence of steps with inputs, outputs, and owners.
"""
from __future__ import annotations

WORKFLOWS: dict[str, dict] = {}


def register_workflow(name: str, spec: dict) -> None:
    WORKFLOWS[name] = spec


# ---------------------------------------------------------------------------
# Private Equity Workflows
# ---------------------------------------------------------------------------

def deal_sourcing_pipeline() -> dict:
    return {
        "name": "deal_sourcing",
        "steps": [
            ("screen", "Initial deal screening"),
            ("financial_model", "Build financial model"),
            ("comps", "Market comparables analysis"),
            ("ic_presentation", "Investment committee deck"),
            ("qoe", "Quality of earnings review"),
            ("legal_review", "Legal and compliance review"),
            ("term_sheet", "Term sheet negotiation"),
            ("closing", "Close and portfolio onboarding"),
        ],
        "owner": "Grant",
        "status": "defined",
    }


def credit_committee_pipeline() -> dict:
    return {
        "name": "credit_committee",
        "steps": [
            ("deal_review", "Deal merits review"),
            ("credit_analysis", "Credit risk analysis"),
            ("covenant_check", "Covenant compliance check"),
            ("committee_vote", "Committee vote"),
            ("conditions", "Conditions precedent"),
            ("closing", "Close"),
        ],
        "owner": "Grant",
        "status": "defined",
    }


# ---------------------------------------------------------------------------
# Banking Workflows
# ---------------------------------------------------------------------------

def bank_onboarding_pipeline() -> dict:
    return {
        "name": "bank_onboarding",
        "steps": [
            ("kyc", "KYC documentation"),
            ("aml_check", "AML compliance screening"),
            ("account_setup", "Account configuration"),
            ("deposit_analysis", "Deposit pattern analysis"),
            ("risk_review", "Risk assessment"),
            ("go_live", "Go live"),
        ],
        "owner": "Julian",
        "status": "defined",
    }


def treasury_planning_pipeline() -> dict:
    return {
        "name": "treasury_planning",
        "steps": [
            ("cash_flow_forecast", "Cash flow forecast"),
            ("liquidity_analysis", "Liquidity analysis"),
            ("rate_strategy", "Interest rate strategy"),
            ("covenant_monitoring", "Covenant monitoring"),
            ("reporting", "Board treasury report"),
        ],
        "owner": "Julian",
        "status": "defined",
    }


# ---------------------------------------------------------------------------
# GCI Workflows
# ---------------------------------------------------------------------------

def church_onboarding_pipeline() -> dict:
    return {
        "name": "church_onboarding",
        "steps": [
            ("sponsor_bank_identification", "Identify sponsor bank"),
            ("deposit_forecast", "Deposit forecasting"),
            ("risk_review", "Risk review"),
            ("technology_integration", "Technology integration"),
            ("member_onboarding", "Member onboarding"),
        ],
        "owner": "Grace",
        "status": "defined",
    }


def media_partnership_pipeline() -> dict:
    return {
        "name": "media_partnership",
        "steps": [
            ("content_workflow", "Content workflow setup"),
            ("sponsor_outreach", "Sponsor outreach"),
            ("presentation_generation", "AI Summit presentation"),
            ("partnership_agreement", "Partnership agreement"),
        ],
        "owner": "Olivia",
        "status": "defined",
    }


# ---------------------------------------------------------------------------
# Research Workflows
# ---------------------------------------------------------------------------

def due_diligence_pipeline() -> dict:
    return {
        "name": "due_diligence",
        "steps": [
            ("document_ingestion", "Ingest all documents"),
            ("financial_extraction", "Extract financial data"),
            ("legal_review", "Legal document review"),
            ("operational_review", "Operational assessment"),
            ("technical_review", "Technology assessment"),
            ("summary", "DD summary report"),
        ],
        "owner": "Evelyn",
        "status": "defined",
    }


def competitive_intelligence_pipeline() -> dict:
    return {
        "name": "competitive_intelligence",
        "steps": [
            ("data_gathering", "OSINT data gathering"),
            ("analysis", "Competitive analysis"),
            ("swot", "SWOT assessment"),
            ("report", "CI report"),
        ],
        "owner": "Evelyn",
        "status": "defined",
    }


# ---------------------------------------------------------------------------
# Register all workflows
# ---------------------------------------------------------------------------
for _wf in [
    deal_sourcing_pipeline,
    credit_committee_pipeline,
    bank_onboarding_pipeline,
    treasury_planning_pipeline,
    church_onboarding_pipeline,
    media_partnership_pipeline,
    due_diligence_pipeline,
    competitive_intelligence_pipeline,
]:
    spec = _wf()
    register_workflow(spec["name"], spec)

def get_workflow(name: str) -> dict | None:
    return WORKFLOWS.get(name)

def list_workflows() -> dict[str, dict]:
    return dict(WORKFLOWS)