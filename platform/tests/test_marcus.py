"""Tests for the Marcus orchestration agent runtime (legacy compatibility)."""
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
    redact_secrets,
    route_task,
    get_status,
)


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
    result = execute_task(task)
    assert result is not None


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

def test_get_status_has_required_fields():
    runtime = MarcusRuntime()
    status = get_status(runtime)
    for field in ("agent_id", "name", "role", "health_status", "specialists_available"):
        assert field in status


# ---------------------------------------------------------------------------
# All 14 specialists present
# ---------------------------------------------------------------------------

def test_all_14_specialists():
    expected = {"david","evelyn","miles","victor","sophia","julian","elijah","grant","caleb","naomi","olivia","grace","jordan","malcolm"}
    assert set(DEFAULT_SPECIALISTS.keys()) == expected


def test_model_config_no_secrets_in_listing():
    listing = json.dumps(DEFAULT_SPECIALISTS)
    assert "TELEGRAM_BOT_TOKEN" not in listing
    assert "secret" not in listing.lower()