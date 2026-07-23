"""Marcus orchestration agent runtime implementation.

Marcus serves as Commander, Chief of Staff, and Chief Improvement Officer
for the Lyons Command Center. He loads trusted repository configuration,
routes tasks to registered specialist agents, records execution results,
and exposes a structured CLI interface.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Typed runtime model
# ---------------------------------------------------------------------------

@dataclass
class MarcusRuntime:
    """Typed runtime model for the Marcus orchestration agent."""

    agent_id: str = "marcus"
    name: str = "Marcus"
    role: str = "Commander, Chief of Staff, Chief Improvement Officer"
    responsibilities: List[str] = field(default_factory=lambda: [
        "Coordinate Lyons Command Center operations",
        "Route tasks to registered specialist agents",
        "Load and maintain system context from trusted repository files",
        "Record execution history and session state",
        "Expose health and status reporting",
        "Enforce security boundaries and redact secrets from logs",
    ])
    permitted_skills: List[str] = field(default_factory=list)
    specialist_routes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    system_context: Dict[str, Any] = field(default_factory=dict)
    session_state: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    health_status: str = "not_initialized"

    @classmethod
    def create(cls, config: Dict[str, Any]) -> "MarcusRuntime":
        """Build a MarcusRuntime from a configuration dict."""
        runtime = cls(
            agent_id=config.get("agent_id", "marcus"),
            name=config.get("name", "Marcus"),
            role=config.get("role", "Commander, Chief of Staff, Chief Improvement Officer"),
            responsibilities=config.get("responsibilities", []),
            permitted_skills=config.get("permitted_skills", []),
            specialist_routes=config.get("specialist_routes", {}),
        )
        runtime.health_status = "initialized"
        return runtime


# ---------------------------------------------------------------------------
# Repository file loading
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

KNOWN_TRUSTED_FILES = [
    _REPO_ROOT / "docs" / "marcus-commander-directive.md",
    _REPO_ROOT / "docs" / "chief-improvement-officer.md",
    _REPO_ROOT / "docs" / "executive-operating-doctrine.md",
    _REPO_ROOT / "docs" / "commanders-oath.md",
    _REPO_ROOT / "docs" / "executive-governance-charter.md",
    _REPO_ROOT / "docs" / "executive-strategic-mandate.md",
    _REPO_ROOT / "docs" / "standing-order-01.md",
    _REPO_ROOT / "docs" / "standing-order-02.md",
    _REPO_ROOT / "docs" / "organizational-directive.md",
    _REPO_ROOT / "AGENTS.md",
    _REPO_ROOT / "MARCUS_CONSOLIDATION_MESSAGE.md",
]


def _load_md(path: Path) -> Dict[str, str]:
    """Load a markdown trusted file and return metadata."""
    if not path.exists():
        return {"path": str(path), "exists": False, "content": ""}
    content = path.read_text(encoding="utf-8")
    # Strip frontmatter/dashes for summary extraction
    lines = content.splitlines()
    title = next((l.lstrip("# ").strip() for l in lines if l.startswith("# ")), path.stem)
    return {
        "path": str(path),
        "exists": True,
        "title": title,
        "content": content,
    }


def load_trusted_context() -> Dict[str, Any]:
    """Load all trusted repository-controlled source files into context."""
    loaded = {}
    for path in KNOWN_TRUSTED_FILES:
        rel = str(path.relative_to(_REPO_ROOT))
        loaded[rel] = _load_md(path)
    return loaded


def load_activation_manifest() -> Dict[str, Any]:
    """Load the activation manifest if it exists."""
    manifest_path = _REPO_ROOT / "skills-registry" / "activation_manifest.json"
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"error": f"malformed activation manifest at {manifest_path}"}
    return {"error": f"missing activation manifest at {manifest_path}"}


def load_skills_registry() -> Dict[str, Any]:
    """Load the skills registry if it exists."""
    registry_path = _REPO_ROOT / "skills-registry" / "skills_registry.json"
    if registry_path.exists():
        try:
            return json.loads(registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"error": f"malformed skills registry at {registry_path}"}
    return {"error": f"missing skills registry at {registry_path}"}


# ---------------------------------------------------------------------------
# Specialist routing
# ---------------------------------------------------------------------------

DEFAULT_SPECIALISTS: Dict[str, Dict[str, Any]] = {
    "david": {
        "name": "David",
        "role": "Strategy and Executive Planning",
        "skills": ["strategy", "executive-planning", "analysis"],
        "status": "available",
    },
    "evelyn": {
        "name": "Evelyn",
        "role": "Research and Intelligence",
        "skills": ["research", "intelligence", "briefing"],
        "status": "available",
    },
    "miles": {
        "name": "Miles",
        "role": "Software Engineering and Development",
        "skills": ["development", "engineering", "code-review"],
        "status": "available",
    },
    "victor": {
        "name": "Victor",
        "role": "Systems, Infrastructure, and Reliability",
        "skills": ["infrastructure", "reliability", "ops"],
        "status": "available",
    },
    "sophia": {
        "name": "Sophia",
        "role": "Product Design, UX/UI, and Brand Experience",
        "skills": ["design", "ux", "ui", "brand"],
        "status": "available",
    },
    "julian": {
        "name": "Julian",
        "role": "Banking, Fintech, and Financial Infrastructure",
        "skills": ["banking", "fintech", "infrastructure"],
        "status": "available",
    },
    "elijah": {
        "name": "Elijah",
        "role": "Legal, Contracts, Compliance, and Risk",
        "skills": ["legal", "compliance", "risk"],
        "status": "available",
    },
    "grant": {
        "name": "Grant",
        "role": "Private Equity, Acquisitions, and Deal Analysis",
        "skills": ["private-equity", "acquisitions", "deals"],
        "status": "available",
    },
    "caleb": {
        "name": "Caleb",
        "role": "Industrial Operations and Automation",
        "skills": ["automation", "operations", "industrial"],
        "status": "available",
    },
    "naomi": {
        "name": "Naomi",
        "role": "Cybersecurity and Information Protection",
        "skills": ["cybersecurity", "infosec", "protection"],
        "status": "available",
    },
    "olivia": {
        "name": "Olivia",
        "role": "Operations and Execution Management",
        "skills": ["operations", "execution", "management"],
        "status": "available",
    },
    "grace": {
        "name": "Grace",
        "role": "Church Technology and Community Platforms",
        "skills": ["church-tech", "community"],
        "status": "available",
    },
    "jordan": {
        "name": "Jordan",
        "role": "Sales, Partnerships, and Business Development",
        "skills": ["sales", "partnerships", "bizdev"],
        "status": "available",
    },
    "malcolm": {
        "name": "Malcolm",
        "role": "Finance, Modeling, and Performance Analysis",
        "skills": ["finance", "modeling", "analysis"],
        "status": "available",
    },
}


def identify_specialist_routes(
    activation_manifest: Dict[str, Any],
    skills_registry: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Derive specialist routes from trusted manifest and registry data."""
    routes: Dict[str, Dict[str, Any]] = {}

    # Start from defaults and overlay with manifest/registry if available
    for key, spec in DEFAULT_SPECIALISTS.items():
        routes[key] = spec

    # Attempt to extract specialist mappings from activation manifest
    if activation_manifest and "error" not in activation_manifest:
        if isinstance(activation_manifest, dict):
            for slot_name, slot_val in activation_manifest.items():
                if isinstance(slot_val, dict):
                    agent = slot_val.get("agent", slot_val.get("name", slot_name))
                    skills = slot_val.get("skills", [])
                    routes[slot_name] = {
                        "name": agent,
                        "skills": skills,
                        "status": slot_val.get("status", "available"),
                        "source": "activation_manifest",
                    }

    # Attempt to enrich from skills registry
    if skills_registry and "error" not in skills_registry:
        if isinstance(skills_registry, dict):
            for skill_key, skill_val in skills_registry.items():
                if isinstance(skill_val, dict):
                    owner = skill_val.get("owner", skill_val.get("agent", ""))
                    owner_lower = owner.lower()
                    if owner_lower in routes:
                        if "skills" not in routes[owner_lower]:
                            routes[owner_lower]["skills"] = []
                        if skill_key not in routes[owner_lower].setdefault("skills", []):
                            routes[owner_lower]["skills"].append(skill_key)

    return routes


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

def load_model_config() -> Dict[str, Any]:
    """Load model routing configuration from the trusted snapshot."""
    snapshot_path = _REPO_ROOT / "platform" / "baseline.json"
    if snapshot_path.exists():
        try:
            data = json.loads(snapshot_path.read_text(encoding="utf-8"))
            return {
                "active": True,
                "source": str(snapshot_path),
                "telegram_commands": data.get("telegram_commands", []),
                "baseline_notes": data.get("baseline_notes", ""),
            }
        except (json.JSONDecodeError, OSError):
            pass
    return {"active": False, "source": None}


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def initialize_marcus() -> Dict[str, Any]:
    """Bootstrap the Marcus runtime from trusted repository configuration.

    Validates required files, loads manifests and registries, identifies
    specialist routes, creates an active session, and returns a structured
    initialization result. Fails safely with exact missing-path errors.
    """
    result: Dict[str, Any] = {
        "agent_id": "marcus",
        "status": "initialized",
        "steps": [],
        "warnings": [],
        "errors": [],
    }

    # Step 1: validate repository root
    result["steps"].append("validating_repo_root")
    if not (_REPO_ROOT / "AGENTS.md").exists():
        result["errors"].append(f"missing required file: {_REPO_ROOT / 'AGENTS.md'}")
        result["status"] = "failed"
        return result

    # Step 2: load trusted context
    result["steps"].append("loading_trusted_context")
    context = load_trusted_context()
    result["trusted_files_loaded"] = sum(1 for v in context.values() if v.get("exists"))
    result["trusted_files_missing"] = sum(1 for v in context.values() if not v.get("exists"))
    result["system_context"] = {
        "repo_root": str(_REPO_ROOT),
        "trusted_files": context,
        "loaded_at": datetime.now(timezone.utc).isoformat(),
    }

    # Step 3: load activation manifest
    result["steps"].append("loading_activation_manifest")
    activation = load_activation_manifest()
    if "error" in activation:
        result["warnings"].append(activation["error"])
    else:
        result["activation_manifest_loaded"] = True

    # Step 4: load skills registry
    result["steps"].append("loading_skills_registry")
    registry = load_skills_registry()
    if "error" in registry:
        result["warnings"].append(registry["error"])
    else:
        result["skills_registry_loaded"] = True

    # Step 5: identify specialist routes
    result["steps"].append("identifying_specialist_routes")
    routes = identify_specialist_routes(activation, registry)
    result["specialist_routes"] = routes
    result["specialists_discovered"] = len(routes)

    # Step 6: create Marcus runtime session
    result["steps"].append("creating_marcus_runtime")
    config = {"name": "Marcus", "role": "Commander, Chief of Staff, Chief Improvement Officer"}
    runtime = MarcusRuntime.create(config)
    runtime.permitted_skills = list(routes.keys())
    runtime.specialist_routes = routes
    runtime.system_context = result.get("system_context", {})
    result["marcus_runtime"] = {
        "agent_id": runtime.agent_id,
        "name": runtime.name,
        "role": runtime.role,
        "health_status": runtime.health_status,
        "responsibilities_count": len(runtime.responsibilities),
    }

    # Step 7: load model routing config
    result["steps"].append("loading_model_config")
    model_cfg = load_model_config()
    result["model_config"] = model_cfg

    result["status"] = "initialized"
    return result


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_task(task: Dict[str, Any], runtime: Optional[MarcusRuntime] = None) -> Dict[str, Any]:
    """Route a task to the appropriate registered specialist.

    Accepts an instruction dict with at minimum a 'command' key and optional
    'payload'. Routes to a named specialist if matchable, otherwise routes
    to Marcus for coordination. Returns a structured result.
    """
    if not isinstance(task, dict):
        return {
            "status": "rejected",
            "reason": "task must be a dict with a 'command' key",
            "routed_to": "marcus",
        }

    command = task.get("command", "").strip().lower()
    specialist = task.get("specialist", "").strip().lower()
    payload = task.get("payload", {})

    result: Dict[str, Any] = {
        "status": "routed",
        "command": command,
        "routed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Direct specialist dispatch
    if specialist and specialist in (runtime.specialist_routes if runtime else DEFAULT_SPECIALISTS):
        result["routed_to"] = specialist
        result["routing_decision"] = "direct_specialist"
        result["detail"] = f"Task '{command}' dispatched to specialist '{specialist}'"
        return result

    # Keyword-based routing
    keyword_routes = {
        "strategy": "david",
        "executive": "david",
        "plan": "david",
        "research": "evelyn",
        "brief": "evelyn",
        "intelligence": "evelyn",
        "code": "miles",
        "develop": "miles",
        "engineer": "miles",
        "review": "miles",
        "infrastructure": "victor",
        "system": "victor",
        "reliability": "victor",
        "deploy": "victor",
        "design": "sophia",
        "ux": "sophia",
        "ui": "sophia",
        "bank": "julian",
        "fintech": "julian",
        "financial": "julian",
        "legal": "elijah",
        "compliance": "elijah",
        "contract": "elijah",
        "equity": "grant",
        "deal": "grant",
        "acquisition": "grant",
        "automate": "caleb",
        "operate": "caleb",
        "ops": "caleb",
        "security": "naomi",
        "cyber": "naomi",
        "protect": "naomi",
        "execute": "olivia",
        "ops": "olivia",
        "church": "grace",
        "sales": "jordan",
        "partner": "jordan",
        "finance": "malcolm",
        "model": "malcolm",
        "performance": "malcolm",
    }

    for keyword, owner in keyword_routes.items():
        if keyword in command:
            result["routed_to"] = owner
            result["routing_decision"] = f"keyword_match:{keyword}"
            result["detail"] = f"Task '{command}' routed to '{owner}' via keyword '{keyword}'"
            return result

    # Fallback: Marcus coordinates
    result["routed_to"] = "marcus"
    result["routing_decision"] = "marcus_coordination"
    result["detail"] = f"Task '{command}' requires Marcus coordination — no matching specialist route found"
    return result


# ---------------------------------------------------------------------------
# Execution interface
# ---------------------------------------------------------------------------

def execute_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a task through Marcus: route, record, report."""
    runtime = MarcusRuntime.create({"name": "Marcus"})

    # Route the task
    routing = route_task(task, runtime)

    # Record in execution history
    entry = {
        "task": task,
        "routing": routing,
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }
    runtime.execution_history.append(entry)

    return routing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def redact_secrets(text: str) -> str:
    """Redact potential secrets and tokens from log output."""
    import re

    patterns = [
        (r"ghp_[A-Za-z0-9]+", "[REDACTED_GITHUB_TOKEN]"),
        (r"xoxb-[A-Za-z0-9-]+", "[REDACTED_BOT_TOKEN]"),
        (r"glpat-[A-Za-z0-9_-]+", "[REDACTED_GITLAB_TOKEN]"),
        (r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED_JWT]"),
        (r"sk-[A-Za-z0-9]+", "[REDACTED_API_KEY]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def get_status(runtime: MarcusRuntime) -> Dict[str, Any]:
    """Get Marcus runtime status."""
    return {
        "agent_id": runtime.agent_id,
        "name": runtime.name,
        "role": runtime.role,
        "health_status": runtime.health_status,
        "specialists_available": len(runtime.specialist_routes),
        "execution_history_count": len(runtime.execution_history),
        "permitted_skills": runtime.permitted_skills,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_json(data: Dict[str, Any]) -> None:
    """Print data as formatted JSON to stdout."""
    print(json.dumps(data, indent=2, default=str))


def main(args: Optional[List[str]] = None) -> int:
    """Marcus CLI entry point.

    Usage:
        python -m platform.marcus start    — Initialize Marcus and report status
        python -m platform.marcus status   — Report runtime status
        python -m platform.marcus list     — List registered specialists
        python -m platform.marcus route <command> [--specialist NAME]
        python -m platform.marcus validate — Validate all trusted configuration files
        python -m platform.marcus execute <command> — Route and execute a task
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="marcus",
        description="Marcus orchestration agent — Lyons Command Center",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("start", help="Initialize Marcus and start a session")
    sub.add_parser("status", help="Report Marcus runtime status")
    sub.add_parser("list", help="List registered specialists")
    sub.add_parser("validate", help="Validate trusted configuration files")

    route_p = sub.add_parser("route", help="Route a task to a specialist")
    route_p.add_argument("command", nargs="?", default="", help="Task command string")
    route_p.add_argument("--specialist", default="", help="Explicit specialist name")
    route_p.add_argument("--payload", default="{}", help="JSON payload")

    exec_p = sub.add_parser("execute", help="Route and execute a task")
    exec_p.add_argument("command", nargs="?", default="", help="Task command string")
    exec_p.add_argument("--specialist", default="", help="Explicit specialist name")

    sub.add_parser("context", help="Load and summarize trusted context")
    sub.add_parser("health", help="Run local health verification")

    parsed = parser.parse_args(args)

    if parsed.command == "start":
        init_result = initialize_marcus()
        if init_result["errors"]:
            _print_json({"status": "failed", "errors": init_result["errors"]})
            return 1
        _print_json({
            "marcus": "initialized",
            "specialists": init_result.get("specialists_discovered", 0),
            "steps_completed": init_result.get("steps", []),
            "warnings": init_result.get("warnings", []),
        })
        return 0

    if parsed.command == "status":
        runtime = MarcusRuntime.create({"name": "Marcus"})
        # Try to load existing state from session
        if os.environ.get("MARCUS_SESSION_STATE"):
            try:
                state = json.loads(os.environ["MARCUS_SESSION_STATE"])
                runtime.health_status = state.get("health_status", runtime.health_status)
            except json.JSONDecodeError:
                pass
        _print_json(get_status(runtime))
        return 0

    if parsed.command == "list":
        routes = DEFAULT_SPECIALISTS
        _print_json({"specialists": routes, "count": len(routes)})
        return 0

    if parsed.command == "validate":
        missing = []
        for f in KNOWN_TRUSTED_FILES:
            if not f.exists():
                missing.append(str(f.relative_to(_REPO_ROOT)))
        activation = load_activation_manifest()
        registry = load_skills_registry()
        result = {
            "trusted_files_missing": missing,
            "activation_manifest_valid": "error" not in activation,
            "skills_registry_valid": "error" not in registry,
        }
        _print_json(result)
        return 0 if not missing else 1

    if parsed.command == "route":
        payload_str = parsed.payload
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            payload = {}
        task = {"command": parsed.command, "specialist": parsed.specialist, "payload": payload}
        _print_json(route_task(task))
        return 0

    if parsed.command == "execute":
        task = {"command": parsed.command, "specialist": parsed.specialist}
        _print_json(execute_task(task))
        return 0

    if parsed.command == "context":
        ctx = load_trusted_context()
        summary = {k: {"exists": v.get("exists"), "title": v.get("title", "")} for k, v in ctx.items()}
        _print_json({"trusted_context": summary, "total": len(summary)})
        return 0

    if parsed.command == "health":
        init = initialize_marcus()
        _print_json({
            "marcus_initialized": init["status"] == "initialized",
            "specialists_discovered": init.get("specialists_discovered", 0),
            "trusted_files_loaded": init.get("trusted_files_loaded", 0),
            "trusted_files_missing_count": init.get("trusted_files_missing", 0),
            "activation_manifest_loaded": init.get("activation_manifest_loaded", False),
            "skills_registry_loaded": init.get("skills_registry_loaded", False),
            "model_config_active": load_model_config().get("active", False),
            "steps": init.get("steps", []),
            "errors": init.get("errors", []),
        })
        return 0 if init["status"] == "initialized" else 1

    parser.print_help()
    return 0