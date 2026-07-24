"""Hardened tests for the Marcus orchestration agent runtime."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from marcus.marcus import (
    PersistenceManager,
    ProviderChain,
    OllamaManager,
    ProcessLockManager,
    CircuitBreakerState,
    MarcusRuntime,
    MarcusWatchdog,
    redact_secrets,
    initialize_marcus,
    route_task,
    execute_task,
    get_status,
    load_trusted_context,
    validate_config,
    list_specialists,
    DEFAULT_SPECIALISTS,
)

# Import module-level runtime dir for assertions
import marcus.marcus as mm


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

def test_circuit_breaker_starts_closed():
    cb = CircuitBreakerState()
    assert cb.state == "closed"
    assert cb.can_attempt is True


def test_circuit_breaker_opens_after_max_failures():
    cb = CircuitBreakerState()
    for _ in range(3):
        cb.record_failure()
    assert cb.state == "open"


def test_circuit_breaker_resets_on_success():
    cb = CircuitBreakerState()
    for _ in range(3):
        cb.record_failure()
    assert cb.state == "open"
    cb.record_success()
    assert cb.state == "closed"
    assert cb.consecutive_failures == 0


def test_circuit_breaker_records_failure_count():
    cb = CircuitBreakerState()
    cb.record_failure()
    assert cb.consecutive_failures == 1
    cb.record_failure()
    assert cb.consecutive_failures == 2


def test_circuit_breaker_opens_after_5_failures():
    cb = CircuitBreakerState()
    for _ in range(5):
        cb.record_failure()
    assert cb.state == "open"
    assert cb.consecutive_failures == 5


# ---------------------------------------------------------------------------
# PersistenceManager
# ---------------------------------------------------------------------------

def test_persistence_manager_atomic_write():
    """Atomic write creates valid JSON."""
    pm = PersistenceManager()
    pm.save_state({"health_status": "initialized", "agent_id": "marcus"})
    state_file = mm._STATE_FILE
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["health_status"] == "initialized"


def test_persistence_redacts_secrets():
    pm = PersistenceManager()
    pm.save_state({"token": "ghp_abc123def456", "plain": "ok"})
    content = mm._STATE_FILE.read_text()
    assert "ghp_abc123def456" not in content
    assert "[REDACTED_GITHUB_TOKEN]" in content
    assert "plain" in content


def test_persistence_corrupt_recovery(tmp_path):
    """If state file is corrupt, recovery from last-known-good works."""
    pm = PersistenceManager(runtime_dir=tmp_path)
    # First write a healthy state as last-known-good
    pm.save_state({"health_status": "initialized", "agent_id": "marcus"})
    # Now corrupt the state file
    (tmp_path / "marcus-state.json").write_text("corrupt json content {{{")
    try:
        pm2 = PersistenceManager(runtime_dir=tmp_path)
        recovered = pm2.load_state()
        assert recovered.get("health_status") == "initialized"
    finally:
        (tmp_path / "marcus-state.json").unlink(missing_ok=True)


def test_persistence_quarantine_on_corrupt():
    """Corrupt state file gets quarantined."""
    pm = PersistenceManager()
    pm.save_state({"health_status": "initialized", "agent_id": "marcus"})
    mm._STATE_FILE.write_text("not-valid-json")
    try:
        pm2 = PersistenceManager()
        pm2.load_state()
        quarantine_dir = mm._RUNTIME_DIR / "quarantine"
        assert quarantine_dir.exists()
    finally:
        mm._STATE_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# ProcessLockManager
# ---------------------------------------------------------------------------

def test_process_lock_acquire_and_release(tmp_path):
    lm = ProcessLockManager(lock_dir=tmp_path)
    acquired = lm.acquire()
    assert acquired is True
    lm.release()


def test_process_lock_stale_cleanup(tmp_path):
    lm = ProcessLockManager(lock_dir=tmp_path)
    # Write a stale lock with an impossible PID
    marker = tmp_path / ".marcus.lock"
    marker.write_text("99999999\n")
    pid_file = tmp_path / ".marcus.pid"
    pid_file.write_text("99999999")

    acquired = lm.acquire()
    assert acquired is True
    lm.release()


# ---------------------------------------------------------------------------
# ProviderChain
# ---------------------------------------------------------------------------

def test_provider_chain_initializes_without_error():
    pc = ProviderChain()
    assert pc is not None


def test_provider_chain_records_success():
    pc = ProviderChain()
    pc.record_success("test", "test-model")
    assert pc.circuit_breakers["test/test-model"].state == "closed"


def test_provider_chain_records_failure():
    pc = ProviderChain()
    pc.record_failure("test", "test-model", http_status=503, error="service unavailable")
    assert pc.circuit_breakers["test/test-model"].consecutive_failures == 1


def test_provider_chain_health_check_429(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(ProviderChain, "_health_check_nous", lambda self, *a, **kw: {"healthy": False, "latency_ms": 10, "http_status": 429, "error": "rate limited"})
        pc = ProviderChain()
        result = pc.health_check("nous", "stepfun/step-3.7-flash:free")
        assert result["healthy"] is False
        assert result["http_status"] == 429


def test_provider_chain_health_check_503(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(ProviderChain, "_health_check_nous", lambda self, *a, **kw: {"healthy": False, "latency_ms": 20, "http_status": 503, "error": "service unavailable"})
        pc = ProviderChain()
        result = pc.health_check("nous", "poolside/laguna-s-2.1:free")
        assert result["healthy"] is False
        assert result["http_status"] == 503


def test_provider_chain_circuit_breaker_opens_after_3_failures(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(ProviderChain, "_health_check_nous", lambda self, *a, **kw: {"healthy": False, "latency_ms": 5, "http_status": 500, "error": "server error"})
        pc = ProviderChain()
        for _ in range(3):
            pc.health_check("nous", "stepfun/step-3.7-flash:free")
        key = "nous/stepfun/step-3.7-flash:free"
        breaker = pc.circuit_breakers.get(key)
        assert breaker is not None
        assert breaker.state == "open"


def test_provider_chain_circuit_breaker_resets_after_success(monkeypatch):
    call_count = {"n": 0}
    def side_effect(*args, **kwargs):
        call_count["n"] += 1
        n = call_count["n"]
        if n >= 3:
            return {"healthy": True, "latency_ms": 5, "http_status": 200}
        return {"healthy": False, "latency_ms": 5, "http_status": 500, "error": "server error"}

    with monkeypatch.context() as m:
        m.setattr(ProviderChain, "_health_check_nous", side_effect)
        pc = ProviderChain()
        for _ in range(4):
            pc.health_check("nous", "stepfun/step-3.7-flash:free")
        key = "nous/stepfun/step-3.7-flash:free"
        breaker = pc.circuit_breakers.get(key)
        assert breaker is not None
        assert breaker.state == "closed"


# ---------------------------------------------------------------------------
# OllamaManager
# ---------------------------------------------------------------------------

def test_ollama_is_available():
    om = OllamaManager()
    assert om.is_available() is True


def test_ollama_lists_models():
    om = OllamaManager()
    models = om.list_models()
    assert isinstance(models, list)
    assert "qwen2.5:3b-instruct" in models


def test_ollama_selects_fallback_model():
    om = OllamaManager()
    fallback = om.select_fallback()
    assert fallback is not None
    assert fallback == "qwen2.5:3b-instruct"


# ---------------------------------------------------------------------------
# MarcusRuntime hardening
# ---------------------------------------------------------------------------

def test_marcus_runtime_can_initialize_hardening():
    runtime = MarcusRuntime()
    runtime.initialize_hardening()
    assert runtime.provider_chain is not None
    assert runtime.ollama_manager is not None
    assert runtime.lock_manager is not None
    assert runtime.persistence is not None


def test_marcus_runtime_graceful_shutdown():
    runtime = MarcusRuntime()
    runtime.initialize_hardening()
    runtime.session_state["test_key"] = "test_value"
    runtime.graceful_shutdown()


def test_marcus_runtime_persists_state():
    pm = PersistenceManager()
    pm.save_state({"health_status": "initialized", "started_at": "2026-01-01T00:00:00+00:00"})
    runtime = MarcusRuntime()
    runtime.initialize_hardening()
    runtime.load_persisted_state()
    assert runtime.health_status == "initialized"


# ---------------------------------------------------------------------------
# MarcusWatchdog
# ---------------------------------------------------------------------------

def test_watchdog_register_component():
    wd = MarcusWatchdog()
    wd.register_component("test_component", lambda: True, interval_sec=30)
    assert len(wd.components) == 1


def test_watchdog_tracks_health():
    wd = MarcusWatchdog()
    wd.register_component("healthy", lambda: True)
    assert wd.components["healthy"]["healthy"] is True


def test_watchdog_start_no_duplicate():
    wd = MarcusWatchdog()
    wd.start()
    wd.start()  # should be no-op
    assert wd._running is True
    wd.stop()


def test_watchdog_stop():
    wd = MarcusWatchdog()
    wd.start()
    wd.stop()
    assert wd._running is False


# ---------------------------------------------------------------------------
# Windows startup
# ---------------------------------------------------------------------------

def test_windows_startup_script_generates():
    from marcus.marcus import get_windows_startup_script
    script = get_windows_startup_script()
    assert "@echo off" in script
    assert "python -m marcus.marcus start" in script
    assert "timeout /t 10" in script


def test_windows_schtasks_command_generates():
    from marcus.marcus import get_schtasks_install_command
    cmd = get_schtasks_install_command()
    assert "schtasks /create" in cmd
    assert "Marcus Command Center" in cmd
    assert "start-marcus.bat" in cmd


# ---------------------------------------------------------------------------
# Integration / end-to-end
# ---------------------------------------------------------------------------

def test_initialize_marcus_creates_runtime_dir():
    result = initialize_marcus()
    assert result["status"] == "initialized"
    assert mm._RUNTIME_DIR.exists()


def test_initialize_marcus_persists_state():
    initialize_marcus()
    assert mm._STATE_FILE.exists()


def test_initialize_marcus_persists_provider_health():
    initialize_marcus()
    assert mm._PROVIDER_FILE.exists()


def test_validate_config_all_trusted_files_present():
    result = validate_config()
    assert result["all_trusted_files_present"] is True


def test_load_trusted_context_exists():
    ctx = load_trusted_context()
    assert isinstance(ctx, dict)
    assert len(ctx) > 0


def test_redact_secrets_removes_github_token():
    assert "[REDACTED_GITHUB_TOKEN]" in redact_secrets("ghp_abc123")


def test_redact_secrets_removes_bot_token():
    assert "[REDACTED_BOT_TOKEN]" in redact_secrets("xoxb-1234-5678")


def test_redact_secrets_removes_api_key():
    assert "[REDACTED_API_KEY]" in redact_secrets("sk-live-abc")


def test_redact_secrets_preserves_normal_text():
    assert redact_secrets("normal text") == "normal text"


def test_get_status_after_initialize():
    result = initialize_marcus()
    status = get_status()
    assert status["health_status"] == "initialized"
    assert status["specialists_available"] == result["specialists_discovered"]


def test_list_specialists_count():
    result = list_specialists()
    assert result["count"] == 14


def test_execute_task_routes_to_evelyn_for_research():
    result = execute_task({"command": "run research on market trends"})
    assert result["routed_to"] == "evelyn"


def test_route_task_direct_specialist():
    result = route_task({"command": "deploy", "specialist": "victor"})
    assert result["routed_to"] == "victor"


def test_route_task_unknown_routes_to_marcus():
    result = route_task({"command": "unknown task that matches nothing"})
    assert result["routed_to"] == "marcus"


def test_all_14_specialists():
    expected = {"david","evelyn","miles","victor","sophia","julian","elijah","grant","caleb","naomi","olivia","grace","jordan","malcolm"}
    assert set(DEFAULT_SPECIALISTS.keys()) == expected


def test_model_config_no_secrets_in_listing():
    listing = json.dumps(DEFAULT_SPECIALISTS)
    assert "TELEGRAM_BOT_TOKEN" not in listing
    assert "secret" not in listing.lower()