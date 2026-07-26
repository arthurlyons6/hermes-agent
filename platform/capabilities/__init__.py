"""Lyons Command Center Module System.

Every capability is an independent module with:
  - purpose
  - inputs
  - outputs
  - dependencies
  - tests
  - metrics
  - owner

Modules are registered here and loaded by Marcus at runtime.
"""
from __future__ import annotations

MODULES: dict[str, dict] = {}


def register_module(name: str, spec: dict) -> None:
    """Register a capability module in the module system."""
    MODULES[name] = spec


def get_module(name: str) -> dict | None:
    """Retrieve a module by name."""
    return MODULES.get(name)


def list_modules() -> dict[str, dict]:
    """Return all registered modules."""
    return dict(MODULES)


def load_all_modules() -> None:
    """Load all module definitions from platform/capabilities/."""
    import importlib
    import pkgutil

    # Import this package to trigger __init__ registration
    # Individual modules self-register when imported


# ---------------------------------------------------------------------------
# Module specifications for all 12 capabilities
# ---------------------------------------------------------------------------

MODULE_SPECS = {
    "research": {
        "purpose": "OSINT, market research, competitive intelligence, document ingestion",
        "inputs": ["queries", "documents", "urls", "databases"],
        "outputs": ["research_reports", "summaries", "key_facts", "citations"],
        "dependencies": ["memory", "docling", "browser-harness"],
        "owner": "Evelyn",
        "tests": "platform/capabilities/research/tests/",
        "metrics": ["research_completeness", "source_citation_count", "report_accuracy"],
    },
    "memory": {
        "purpose": "Persistent organizational memory with dashboard visibility",
        "inputs": ["events", "meetings", "deals", "contacts", "decisions"],
        "outputs": ["memories", "memories_by_context", "memory_consistency_report"],
        "dependencies": ["hyatlas-memory"],
        "owner": "Marcus",
        "tests": "platform/capabilities/memory/tests/",
        "metrics": ["memory_recall_accuracy", "memory_growth_rate", "context_retrieval_latency"],
    },
    "planning": {
        "purpose": "Structured planning for PE deals, banking workflows, and projects",
        "inputs": ["objectives", "constraints", "resources", "timeline"],
        "outputs": ["plan", "milestones", "risk_assessment", "resource_allocation"],
        "dependencies": ["hermes-council"],
        "owner": " Marcus",
        "tests": "platform/capabilities/planning/tests/",
        "metrics": ["plan_completion_rate", "milestone_on_time_rate", "risk_coverage"],
    },
    "negotiation": {
        "purpose": "Negotiation support, term sheet analysis, counter-strategy",
        "inputs": ["term_sheets", "market_data", "counter_proposals", "party_profiles"],
        "outputs": ["negotiation_strategy", "best_alternative", "recommended_terms"],
        "dependencies": ["hermes-council", "memory"],
        "owner": "Grant",
        "tests": "platform/capabilities/negotiation/tests/",
        "metrics": ["negotiation_outcome_score", "term_optimization_rate"],
    },
    "banking": {
        "purpose": "Bank onboarding, deposit analysis, compliance review, treasury",
        "inputs": ["bank_profiles", "deposit_data", "compliance_requirements", "kyc"],
        "outputs": ["onboarding_status", "compliance_report", "treasury_plan"],
        "dependencies": ["platform/nexabaas-patterns"],
        "owner": "Julian",
        "tests": "platform/capabilities/banking/tests/",
        "metrics": ["onboarding_completion_rate", "compliance_score", "time_to_deposit"],
    },
    "private_equity": {
        "purpose": "Deal sourcing, screening, financial modeling, QoE, IC, closing",
        "inputs": ["deal_pipeline", "financial_models", "market_comps", "IC_members"],
        "outputs": ["deal_recommendations", "financial_model", "ic_outcome"],
        "dependencies": ["hermes-council", "docling", "memory", "planning"],
        "owner": "Grant",
        "tests": "platform/capabilities/private_equity/tests/",
        "metrics": ["deal_flow_efficiency", "ic_decision_quality", "closing_rate"],
    },
    "document_intelligence": {
        "purpose": "Document ingestion, parsing, extraction, and LLM-ready conversion",
        "inputs": ["documents", "pdfs", "images", "contracts", "financials"],
        "outputs": ["structured_data", "extracted_fields", "llm_ready_context"],
        "dependencies": ["docling"],
        "owner": "Evelyn",
        "tests": "platform/capabilities/document_intelligence/tests/",
        "metrics": ["extraction_accuracy", "document_processing_latency", "output_usability_score"],
    },
    "workflow": {
        "purpose": "Durable workflow execution with retry, scheduling, and concurrency",
        "inputs": ["workflow_definitions", "tasks", "triggers"],
        "outputs": ["workflow_results", "execution_logs", "error_reports"],
        "dependencies": ["hatchet-patterns"],
        "owner": "Victor",
        "tests": "platform/capabilities/workflow/tests/",
        "metrics": ["workflow_completion_rate", "retry_success_rate", "execution_latency_p99"],
    },
    "browser_automation": {
        "purpose": "Browser-based task automation with self-healing and session sharing",
        "inputs": ["urls", "interactions", "session_state"],
        "outputs": ["task_results", "session_context", "error_recovery_log"],
        "dependencies": ["browser-harness", "ego-lite-pattern"],
        "owner": "Sophia",
        "tests": "platform/capabilities/browser_automation/tests/",
        "metrics": ["task_success_rate", "self_heal_recovery_rate", "session_continuity"],
    },
    "developer": {
        "purpose": "Developer tooling, code intelligence, dependency analysis, architecture",
        "inputs": ["code_repos", "dependencies", "architecture_diagrams"],
        "outputs": ["code_search_results", "dependency_graph", "architecture_analysis"],
        "dependencies": ["codegraph"],
        "owner": "Miles",
        "tests": "platform/capabilities/developer/tests/",
        "metrics": ["token_savings", "code_search_latency", "dependency_accuracy"],
    },
    "governance": {
        "purpose": "Tool call governance, policy enforcement, audit logging, cost tracking",
        "inputs": ["tool_calls", "policies", "audit_rules"],
        "outputs": ["approval_decisions", "audit_log", "cost_report", "risk_assessment"],
        "dependencies": ["acp-plugin"],
        "owner": "Naomi",
        "tests": "platform/capabilities/governance/tests/",
        "metrics": ["policy_violation_rate", "audit_completeness", "cost_per_workflow"],
    },
    "communication": {
        "purpose": "Multi-channel communication, briefing generation, presentation",
        "inputs": ["content", "channel_config", "audience_profile"],
        "outputs": ["briefings", "presentations", "channel_messages"],
        "dependencies": ["telegram_poller", "hermes-council"],
        "owner": "Olivia",
        "tests": "platform/capabilities/communication/tests/",
        "metrics": ["message_delivery_rate", "briefing_quality_score", "response_latency"],
    },
}


# ---------------------------------------------------------------------------
# Initialize module system
# ---------------------------------------------------------------------------

def initialize_modules() -> None:
    """Register all module specifications."""
    for name, spec in MODULE_SPECS.items():
        register_module(name, spec)


def get_module_dependencies(module_name: str) -> list[str]:
    """Return the dependency list for a module."""
    spec = MODULES.get(module_name)
    if spec is None:
        return []
    return spec.get("dependencies", [])


def get_module_owner(module_name: str) -> str:
    """Return the owner agent for a module."""
    spec = MODULES.get(module_name)
    if spec is None:
        return "unassigned"
    return spec.get("owner", "unassigned")


def get_modules_by_owner(owner: str) -> dict[str, dict]:
    """Return all modules owned by a given agent."""
    return {name: spec for name, spec in MODULES.items() if spec.get("owner") == owner}