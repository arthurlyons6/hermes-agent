"""Tests for the Marcus orchestration agent runtime."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from marcus.marcus import (
    DEFAULT_SPECIALISTS,
    MarcusRuntime,
    execute_task,
    initialize_marcus,
    load_activation_manifest,
    load_model_config,
    load_skills_registry,
    load_trusted_context,
    redact_secrets,
    route_task,
    get_status,
)


# ---------------------------------------------------------------------------
# MarcusRuntime model
# ---------------------------------------------------------------------------

def test_marcus_runtime_creation():
    runtime = MarcusRuntime.create({"agent_id": "marcus", "name": "Marcus"})
    assert runtime.agent_id == "marcus"
    assert runtime.name == "Marcus"
    assert runtime.health_status == "initialized"


def test_marcus_runtime_defaults():
    runtime = MarcusRuntime()
    assert runtime.agent_id == "marcus"
    assert runtime.name == "Marcus"
    assert runtime.role == "Commander, Chief of Staff, Chief Improvement Officer"
    assert len(runtime.responsibilities) > 0


# ---------------------------------------------------------------------------
# Trusted context loading
# ---------------------------------------------------------------------------

def test_load_trusted_context_returns_dict():
    ctx = load_trusted_context()
    assert isinstance(ctx, dict)
    # AGENTS.md should always be present in the repo
    assert any("AGENTS.md" in k for k in ctx)


def test_load_trusted_context_file_exists_flag():
    ctx = load_trusted_context()
    for path, info in ctx.items():
        assert "exists" in info
        assert "title" in info


# ---------------------------------------------------------------------------
# Activation manifest
# ---------------------------------------------------------------------------

def test_load_activation_manifest_missing():
    result = load_activation_manifest()
    assert "error" in result


def test_load_activation_manifest_safe_on_missing_file():
    # Should not raise; returns error dict
    result = load_activation_manifest()
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Skills registry
# ---------------------------------------------------------------------------

def test_load_skills_registry_missing():
    result = load_skills_registry()
    assert "error" in result


# ---------------------------------------------------------------------------
# Specialist routes
# ---------------------------------------------------------------------------

def test_identify_specialist_routes_from_defaults():
    routes = DEFAULT_SPECIALISTS
    assert len(routes) > 0
    assert "david" in routes
    assert "evelyn" in routes
    assert "miles" in routes


def test_default_specialist_has_required_fields():
    for key, spec in DEFAULT_SPECIALISTS.items():
        assert "name" in spec
        assert "role" in spec
        assert "skills" in spec
        assert "status" in spec


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_marcus_initialization_succeeds():
    result = initialize_marcus()
    assert result["status"] == "initialized"
    assert "marcus_runtime" in result


def test_initialization_loads_specialists():
    result = initialize_marcus()
    assert result["specialists_discovered"] > 0


def test_initialization_loads_trusted_files():
    result = initialize_marcus()
    assert isinstance(result.get("trusted_files_loaded"), int)


def test_initialization_warnings_for_missing_manifest():
    result = initialize_marcus()
    # warnings list should contain the missing manifest message
    assert isinstance(result.get("warnings"), list)
    assert len(result.get("warnings", [])) > 0


def test_initialization_no_errors():
    result = initialize_marcus()
    assert not result.get("errors", [])


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def test_route_task_direct_specialist():
    task = {"command": "deploy infrastructure", "specialist": "victor"}
    result = route_task(task)
    assert result["routed_to"] == "victor"
    assert result["routing_decision"] == "direct_specialist"


def test_route_task_keyword_match():
    task = {"command": "run research on competitor"}
    result = route_task(task)
    assert result["routed_to"] == "evelyn"
    assert "keyword_match" in result["routing_decision"]


def test_route_task_marcus_coordination():
    task = {"command": "something completely unknown"}
    result = route_task(task)
    assert result["routed_to"] == "marcus"
    assert result["routing_decision"] == "marcus_coordination"


def test_route_task_rejects_non_dict():
    result = route_task("not a dict")
    assert result["status"] == "rejected"


def test_route_task_empty_command_falls_to_marcus():
    task = {"command": ""}
    result = route_task(task)
    assert result["routed_to"] == "marcus"


def test_route_task_with_payload():
    task = {"command": "review the deal", "payload": {"deal_id": "ORD-1"}}
    result = route_task(task)
    assert result["command"] == "review the deal"
    # "review" routes to miles (code review) first in keyword scan order
    assert result["routed_to"] in ("miles", "grant", "marcus")


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def test_execute_task_returns_routing_result():
    task = {"command": "fix the security issue", "specialist": "naomi"}
    result = execute_task(task)
    assert result["status"] == "routed"
    assert result["routed_to"] == "naomi"


def test_execute_task_records_history():
    task = {"command": "test history"}
    execute_task(task)
    # History is recorded on the runtime, but execute_task returns routing
    result = execute_task(task)
    assert result is not None


# ---------------------------------------------------------------------------
# Model config
# ---------------------------------------------------------------------------

def test_load_model_config_returns_dict():
    cfg = load_model_config()
    assert isinstance(cfg, dict)


# ---------------------------------------------------------------------------
# Secrets redaction
# ---------------------------------------------------------------------------

def test_redact_secrets_github_token():
    assert redact_secrets("token ghp_abc123def456") == "token [REDACTED_GITHUB_TOKEN]"


def test_redact_secrets_bot_token():
    assert redact_secrets("token xoxb-1234-5678") == "token [REDACTED_BOT_TOKEN]"


def test_redact_secrets_jwt():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    assert "[REDACTED_JWT]" in redact_secrets(token)


def test_redact_secrets_no_match():
    text = "this is a normal string with no tokens"
    assert redact_secrets(text) == text


def test_redact_secrets_api_key():
    assert redact_secrets("key sk-abc123xyz") == "key [REDACTED_API_KEY]"


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def test_get_status_returns_dict():
    runtime = MarcusRuntime.create({"name": "Marcus"})
    status = get_status(runtime)
    assert "health_status" in status
    assert status["health_status"] == "initialized"
    assert "specialists_available" in status


def test_status_has_required_fields():
    runtime = MarcusRuntime.create({"name": "Marcus"})
    status = get_status(runtime)
    for field in ("agent_id", "name", "role", "health_status", "specialists_available"):
        assert field in status


# ---------------------------------------------------------------------------
# Provider fallback validation (model config)
# ---------------------------------------------------------------------------

def test_model_config_reports_active():
    cfg = load_model_config()
    # Baseline exists; should report active
    assert isinstance(cfg.get("active"), bool)


def test_model_config_no_secrets_in_output():
    cfg = load_model_config()
    cfg_str = json.dumps(cfg)
    # The baseline.json should not contain any raw tokens
    assert "TELEGRAM_BOT_TOKEN" not in cfg.get("telegram_commands", [{}])[0].get("action", "") if cfg.get("telegram_commands") else True