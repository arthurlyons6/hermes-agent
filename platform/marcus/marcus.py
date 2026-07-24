"""Marcus — Lyons Command Center orchestration agent (hardened runtime).

Provides:
- PersistenceManager — atomic state writes, last-known-good, corrupt recovery
- ProviderChain — model rotation with health checks, circuit breaker, cooldown
- OllamaManager — local model discovery, health probe, fallback selection
- ProcessLockManager — duplicate-instance prevention, stale lock recovery
- StructuredLogger — rotating, secrets-redacted logs
- MarcusRuntime — orchestration state machine
- initialize_marcus / route_task / execute_task / shutdown_marcus
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import threading
import atexit
import signal
import logging
import logging.handlers
import re
import shutil
import tempfile
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple


# ---------------------------------------------------------------------------
# Constants / paths
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_RUNTIME_DIR = _REPO_ROOT / "runtime"
_STATE_FILE = _RUNTIME_DIR / "marcus-state.json"
_PROVIDER_FILE = _RUNTIME_DIR / "provider-health.json"
_WORKFORCE_FILE = _RUNTIME_DIR / "workforce-state.json"
_HISTORY_FILE = _RUNTIME_DIR / "execution-history.jsonl"
_LAST_KNOWN_GOOD = _RUNTIME_DIR / "last-known-good.json"
_LOCK_FILE = _RUNTIME_DIR / ".marcus.lock"
_PID_FILE = _RUNTIME_DIR / ".marcus.pid"
_LOG_DIR = _RUNTIME_DIR / "logs"
_LOG_FILE = _LOG_DIR / "marcus.log"

# Module-level reference to the initialized runtime, used by get_status()
_initialized_runtime: Optional[MarcusRuntime] = None

# Model routing policy
MODEL_POLICY = {
    "preferred": [
        {"provider": "nous", "model": "stepfun/step-3.7-flash:free", "tier": 1},
        {"provider": "openrouter", "model": "anthropic/claude-sonnet-4", "tier": 1},
    ],
    "secondary": [
        {"provider": "nous", "model": "poolside/laguna-s-2.1:free", "tier": 2},
    ],
    "ollama_priority": [
        "qwen2.5:3b-instruct",
        "llama3.2:3b-instruct",
        "gemma2:2b",
        "deepseek-r1:1.5b",
    ],
}

# Circuit breaker thresholds
CIRCUIT_BREAKER_MAX_FAILURES = 3
CIRCUIT_BREAKER_INITIAL_COOLDOWN_SEC = 300  # 5 minutes
CIRCUIT_BREAKER_MAX_COOLDOWN_SEC = 3600  # 1 hour max cooldown
CIRCUIT_BREAKER_COOLDOWN_MULTIPLIER = 2.0
MAX_IMMEDIATE_ATTEMPTS = 2
HEALTH_CHECK_TIMEOUT_SEC = 10

# Lock management
LOCK_STALE_AFTER_SEC = 300  # 5 minutes considered stale

# Known trusted docs (used by Marcus for trusted-context loading)
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

SECRET_PATTERNS = [
    (r"ghp_[A-Za-z0-9]+", "[REDACTED_GITHUB_TOKEN]"),
    (r"xoxb-[A-Za-z0-9-]+", "[REDACTED_BOT_TOKEN]"),
    (r"glpat-[A-Za-z0-9_-]+", "[REDACTED_GITLAB_TOKEN]"),
    (r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[REDACTED_JWT]"),
    (r"sk-[A-Za-z0-9]+", "[REDACTED_API_KEY]"),
]


# ===========================================================================
# Structured Logger
# ===========================================================================

class StructuredLogger:
    """Rotating, secrets-redacted structured logger."""

    def __init__(
        self,
        name: str = "marcus",
        log_dir: Path = _LOG_DIR,
        max_bytes: int = 5 * 1024 * 1024,  # 5 MB
        backup_count: int = 5,
    ) -> None:
        self.name = name
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)

        # Generate session ID _before_ adding handlers (handlers call _extra)
        self._session_id = hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}{os.getpid()}".encode()
        ).hexdigest()[:12]

        # Prevent duplicate handlers if re-initialized
        if self._logger.handlers:
            return

        rotator = logging.handlers.RotatingFileHandler(
            str(_LOG_FILE),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        rotator.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(component)-16s | %(session_id)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        rotator.setFormatter(formatter)
        self._logger.addHandler(rotator)

        # Console handler at INFO
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        self._logger.addHandler(console)

    def _redact(self, msg: str) -> str:
        for pattern, replacement in SECRET_PATTERNS:
            msg = re.sub(pattern, replacement, msg)
        return msg

    def _extra(self, component: str = "marcus", **kwargs: Any) -> dict:
        base = {
            "component": component,
            "session_id": self._session_id,
        }
        base.update(kwargs)
        return base

    def debug(self, msg: str, component: str = "marcus", **kwargs: Any) -> None:
        self._logger.log(logging.DEBUG, self._redact(msg), extra=self._extra(component, **kwargs))

    def info(self, msg: str, component: str = "marcus", **kwargs: Any) -> None:
        self._logger.log(logging.INFO, self._redact(msg), extra=self._extra(component, **kwargs))

    def warning(self, msg: str, component: str = "marcus", **kwargs: Any) -> None:
        self._logger.log(logging.WARNING, self._redact(msg), extra=self._extra(component, **kwargs))

    def error(self, msg: str, component: str = "marcus", **kwargs: Any) -> None:
        self._logger.log(logging.ERROR, self._redact(msg), extra=self._extra(component, **kwargs))


# ===========================================================================
# PersistenceManager
# ===========================================================================

class PersistenceManager:
    """Atomic state writer with last-known-good recovery."""

    def __init__(self, runtime_dir: Path = _RUNTIME_DIR, logger: Optional[StructuredLogger] = None) -> None:
        self.runtime_dir = runtime_dir
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.logger = logger or StructuredLogger()
        self._last_known_good: Dict[str, Any] = {}

        # Derive instance-level paths from runtime_dir (allows test overrides)
        self._state_file = self.runtime_dir / "marcus-state.json"
        self._provider_file = self.runtime_dir / "provider-health.json"
        self._history_file = self.runtime_dir / "execution-history.jsonl"
        self._last_known_good_file = self.runtime_dir / "last-known-good.json"

        self._load_last_known_good()

    @property
    def state_file(self) -> Path:
        return self._state_file

    @property
    def provider_file(self) -> Path:
        return self._provider_file

    @property
    def history_file(self) -> Path:
        return self._history_file

    def _load_last_known_good(self) -> None:
        if self._last_known_good_file.exists():
            try:
                self._last_known_good = json.loads(self._last_known_good_file.read_text(encoding="utf-8"))
                self.logger.info("Loaded last-known-good configuration", component="persistence")
            except (json.JSONDecodeError, OSError) as exc:
                self.logger.warning(f"Could not load last-known-good: {exc}", component="persistence")
                self._last_known_good = {}

    def _atomic_write(self, path: Path, data: Dict[str, Any]) -> None:
        """Write atomically: tmp -> flush/validate -> replace."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".writing_")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
                f.flush()
                os.fsync(f.fileno())
            # Validate the temp file is valid JSON
            with open(tmp_path, "r", encoding="utf-8") as f:
                json.load(f)
            # Atomic replace
            os.replace(tmp_path, str(path))
            self.logger.debug(f"Atomically wrote {path.name}", component="persistence")
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save Marcus runtime state atomically."""
        sanitized = self._sanitize(state)
        self._atomic_write(self._state_file, sanitized)
        self._last_known_good["state"] = sanitized
        self._last_known_good["saved_at"] = datetime.now(timezone.utc).isoformat()
        self._atomic_write(self._last_known_good_file, self._last_known_good)

    def save_provider_health(self, health: Dict[str, Any]) -> None:
        """Persist provider health state atomically."""
        sanitized = self._sanitize(health)
        self._atomic_write(self._provider_file, sanitized)
        self._last_known_good["provider_health"] = sanitized
        self._last_known_good["saved_at"] = datetime.now(timezone.utc).isoformat()
        self._atomic_write(self._last_known_good_file, self._last_known_good)

    def save_execution_record(self, record: Dict[str, Any]) -> None:
        """Append a single execution record as JSONL."""
        sanitized = self._sanitize(record)
        self._history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(sanitized, default=str) + "\n")

    def load_state(self) -> Dict[str, Any]:
        """Load persisted state. Returns empty dict if missing."""
        if not self._state_file.exists():
            return {}
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            self.logger.warning(f"State file corrupt ({exc}), attempting recovery", component="persistence")
            return self._recover_state()

    def _recover_state(self) -> Dict[str, Any]:
        """Attempt recovery from last-known-good. Quarantine the corrupt file."""
        if self._state_file.exists():
            quarantine_dir = self.runtime_dir / "quarantine"
            quarantine_dir.mkdir(exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            quarantine_path = quarantine_dir / f"marcus-state-corrupt-{ts}.json"
            try:
                shutil.copy2(str(self._state_file), str(quarantine_path))
            except OSError:
                pass
        if self._last_known_good.get("state"):
            self._atomic_write(self._state_file, self._last_known_good["state"])
            self.logger.info("Recovered state from last-known-good", component="persistence")
            return self._last_known_good["state"]
        self.logger.warning("No last-known-good available for recovery", component="persistence")
        return {}

    def load_provider_health(self) -> Dict[str, Any]:
        if not self._provider_file.exists():
            return {}
        try:
            with open(self._provider_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return self._recover_provider_health()

    def _recover_provider_health(self) -> Dict[str, Any]:
        if self._provider_file.exists():
            quarantine_dir = self.runtime_dir / "quarantine"
            quarantine_dir.mkdir(exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            quarantine_path = quarantine_dir / f"provider-health-corrupt-{ts}.json"
            try:
                shutil.copy2(str(self._provider_file), str(quarantine_path))
            except OSError:
                pass
        if self._last_known_good.get("provider_health"):
            self._atomic_write(self._provider_file, self._last_known_good["provider_health"])
            self.logger.info("Recovered provider health from last-known-good", component="persistence")
            return self._last_known_good["provider_health"]
        return {}

    @staticmethod
    def _sanitize(data: Any) -> Any:
        """Remove potential secrets from data before persistence."""
        if isinstance(data, dict):
            return {k: PersistenceManager._sanitize(v) for k, v in data.items()}
        if isinstance(data, list):
            return [PersistenceManager._sanitize(item) for item in data]
        if isinstance(data, str):
            return redact_secrets(data)
        return data


# ===========================================================================
# Secret redaction helper (module-level)
# ===========================================================================

def redact_secrets(text: str) -> str:
    """Redact potential secrets from log output."""
    for pattern, replacement in SECRET_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


# ===========================================================================
# Circuit Breaker
# ===========================================================================

@dataclass
class CircuitBreakerState:
    provider: str = ""
    model: str = ""
    consecutive_failures: int = 0
    state: str = "closed"  # closed = normal, open = blocking, half_open = testing
    opened_at: str = ""
    cooldown_until: str = ""
    last_failure: str = ""
    last_success: str = ""

    @property
    def is_open(self) -> bool:
        if self.state != "open":
            return False
        if not self.cooldown_until:
            return True
        try:
            until = datetime.fromisoformat(self.cooldown_until)
            return datetime.now(timezone.utc) < until
        except (ValueError, TypeError):
            return True

    @property
    def can_attempt(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open" and not self.is_open:
            return True  # cooldown expired, allow half-open probe
        return False

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = "closed"
        self.last_success = datetime.now(timezone.utc).isoformat()
        self.opened_at = ""
        self.cooldown_until = ""

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.last_failure = datetime.now(timezone.utc).isoformat()
        if self.consecutive_failures >= CIRCUIT_BREAKER_MAX_FAILURES:
            self.state = "open"
            self.opened_at = datetime.now(timezone.utc).isoformat()
            # Exponential backoff cooldown
            previous_cooldown = 0
            if self.cooldown_until:
                try:
                    prev = datetime.fromisoformat(self.cooldown_until)
                    now = datetime.now(timezone.utc)
                    delta = (prev - now).total_seconds()
                    previous_cooldown = max(0, delta)
                except (ValueError, TypeError):
                    previous_cooldown = 0
            base = CIRCUIT_BREAKER_INITIAL_COOLDOWN_SEC
            multiplier = 2 ** max(0, self.consecutive_failures - CIRCUIT_BREAKER_MAX_FAILURES)
            cooldown = min(base * multiplier, CIRCUIT_BREAKER_MAX_COOLDOWN_SEC)
            until = datetime.now(timezone.utc) + timedelta(seconds=cooldown)
            self.cooldown_until = until.isoformat()


# ===========================================================================
# ProviderChain
# ===========================================================================

@dataclass
class ProviderRecord:
    provider: str
    model: str
    tier: int
    healthy: bool = True
    last_check: str = ""
    last_success: str = ""
    last_failure: str = ""
    response_status: int = 0
    latency_ms: float = 0.0
    consecutive_failures: int = 0
    cooldown_until: str = ""


class ProviderChain:
    """Manages a prioritized chain of model providers with health checks."""

    def __init__(
        self,
        policy: Dict[str, Any] = None,
        persistence: Optional[PersistenceManager] = None,
        logger: Optional[StructuredLogger] = None,
    ) -> None:
        self.policy = policy or MODEL_POLICY
        self.persistence = persistence or PersistenceManager()
        self.logger = logger or StructuredLogger()
        self._lock = threading.RLock()
        self._circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self._load_provider_health()

    def _load_provider_health(self) -> None:
        saved = self.persistence.load_provider_health()
        for tier_key in ("preferred", "secondary", "ollama"):
            for rec in saved.get(tier_key, []):
                key = f"{rec.get('provider','')}/{rec.get('model','')}"
                cb = CircuitBreakerState(
                    provider=rec.get("provider", ""),
                    model=rec.get("model", ""),
                    consecutive_failures=rec.get("consecutive_failures", 0),
                    state="open" if rec.get("cooldown_until") and self._is_cooldown_active(rec.get("cooldown_until", "")) else "closed",
                    last_failure=rec.get("last_failure", ""),
                    last_success=rec.get("last_success", ""),
                    cooldown_until=rec.get("cooldown_until", ""),
                )
                self._circuit_breakers[key] = cb

    @staticmethod
    def _is_cooldown_active(cooldown_until: str) -> bool:
        if not cooldown_until:
            return False
        try:
            until = datetime.fromisoformat(cooldown_until)
            return datetime.now(timezone.utc) < until
        except (ValueError, TypeError):
            return False

    def _breaker_key(self, provider: str, model: str) -> str:
        return f"{provider}/{model}"

    @property
    def circuit_breakers(self) -> Dict[str, CircuitBreakerState]:
        return self._circuit_breakers

    @circuit_breakers.setter
    def circuit_breakers(self, val: Dict[str, CircuitBreakerState]) -> None:
        self._circuit_breakers = val

    def get_healthy_model(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Return (provider, model, tier) of the first healthy model in priority order."""
        with self._lock:
            for tier_models in [self.policy.get("preferred", []), self.policy.get("secondary", [])]:
                for model_entry in tier_models:
                    key = self._breaker_key(model_entry["provider"], model_entry["model"])
                    breaker = self._circuit_breakers.get(key)
                    if breaker is None or breaker.can_attempt:
                        return model_entry["provider"], model_entry["model"], str(model_entry["tier"])

            # Try Ollama fallback
            ollama_models = self._get_ollama_health().get("available_models", [])
            if ollama_models:
                return "ollama", ollama_models[0], "3"

        return None, None, None

    def record_success(self, provider: str, model: str) -> None:
        with self._lock:
            key = self._breaker_key(provider, model)
            if key not in self._circuit_breakers:
                self._circuit_breakers[key] = CircuitBreakerState(provider=provider, model=model)
            self._circuit_breakers[key].record_success()
            self._persist_health()

    def record_failure(self, provider: str, model: str, http_status: int = 0, error: str = "") -> None:
        with self._lock:
            key = self._breaker_key(provider, model)
            if key not in self._circuit_breakers:
                self._circuit_breakers[key] = CircuitBreakerState(provider=provider, model=model)
            self._circuit_breakers[key].record_failure()
            if provider == "nous" and model == "poolside/laguna-s-2.1:free":
                auth_failure = "unauthorized" in error.lower() or "401" in str(http_status) or "403" in str(http_status)
                if auth_failure:
                    self.logger.warning(f"Authentication failure for {provider}/{model} — will not retry continuously", component="provider")
            self._persist_health()

    def _persist_health(self) -> None:
        health: Dict[str, Any] = {"preferred": [], "secondary": [], "ollama": []}
        for key, cb in self._circuit_breakers.items():
            provider, model = key.split("/", 1)
            tier = "preferred" if (provider in [e["provider"] for e in self.policy.get("preferred", [])] and model in [e["model"] for e in self.policy.get("preferred", [])]) else "secondary" if (provider in [e["provider"] for e in self.policy.get("secondary", [])] and model in [e["model"] for e in self.policy.get("secondary", [])]) else "ollama"
            rec = {
                "provider": cb.provider,
                "model": cb.model,
                "consecutive_failures": cb.consecutive_failures,
                "cooldown_until": cb.cooldown_until,
                "last_failure": cb.last_failure,
                "last_success": cb.last_success,
                "state": cb.state,
                "is_open": cb.is_open,
            }
            health.setdefault(tier, []).append(rec)
        self.persistence.save_provider_health(health)

    def _get_ollama_health(self) -> Dict[str, Any]:
        """Check Ollama availability and return healthy model list."""
        ollama = OllamaManager(logger=self.logger)
        if not ollama.is_available():
            return {"available": False, "available_models": []}
        models = ollama.list_models()
        healthy_models = []
        for m in models:
            check = ollama.health_check(m)
            if check.get("healthy"):
                healthy_models.append(m)
        return {"available": True, "available_models": healthy_models}

    def health_check(self, provider: str, model: str) -> Dict[str, Any]:
        """Perform a minimal health check against a provider model."""
        start = time.monotonic()
        result: Dict[str, Any] = {
            "provider": provider,
            "model": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "healthy": False,
            "latency_ms": 0,
            "http_status": 0,
            "error": "",
        }
        try:
            if provider == "ollama":
                result = self._health_check_ollama(model, start)
            elif provider == "nous":
                result = self._health_check_nous(model, start)
            elif provider == "openrouter":
                result = self._health_check_openrouter(model, start)
            else:
                result["error"] = f"unknown provider: {provider}"
        except Exception as exc:
            result["error"] = str(exc)
            result["latency_ms"] = round((time.monotonic() - start) * 1000, 2)

        if result.get("healthy"):
            self.record_success(provider, model)
        else:
            self.record_failure(provider, model, http_status=result.get("http_status", 0), error=result.get("error", ""))

        return result

    def _health_check_ollama(self, model: str, start: float) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["ollama", "show", model],
                capture_output=True, text=True, timeout=HEALTH_CHECK_TIMEOUT_SEC,
            )
            elapsed = round((time.monotonic() - start) * 1000, 2)
            if result.returncode == 0:
                return {"healthy": True, "latency_ms": elapsed, "http_status": 200}
            return {"healthy": False, "latency_ms": elapsed, "http_status": 0, "error": result.stderr.strip()[:200]}
        except subprocess.TimeoutExpired:
            return {"healthy": False, "latency_ms": round((time.monotonic() - start) * 1000, 2), "http_status": 0, "error": "timeout"}
        except Exception as exc:
            return {"healthy": False, "latency_ms": round((time.monotonic() - start) * 1000, 2), "http_status": 0, "error": str(exc)}

    def _health_check_nous(self, model: str, start: float) -> Dict[str, Any]:
        try:
            import requests as req_lib
            resp = req_lib.post(
                "https://inference-api.nousresearch.com/v1/models",
                json={"model": model, "max_tokens": 1},
                timeout=HEALTH_CHECK_TIMEOUT_SEC,
            )
            elapsed = round((time.monotonic() - start) * 1000, 2)
            if resp.status_code == 429:
                return {"healthy": False, "latency_ms": elapsed, "http_status": 429, "error": "rate limited (429)"}
            if resp.status_code == 503:
                return {"healthy": False, "latency_ms": elapsed, "http_status": 503, "error": "service unavailable (503)"}
            if resp.status_code >= 500:
                return {"healthy": False, "latency_ms": elapsed, "http_status": resp.status_code, "error": f"server error ({resp.status_code})"}
            if resp.status_code in (401, 403):
                return {"healthy": False, "latency_ms": elapsed, "http_status": resp.status_code, "error": "authentication failed"}
            if resp.status_code == 200:
                return {"healthy": True, "latency_ms": elapsed, "http_status": 200}
            return {"healthy": False, "latency_ms": elapsed, "http_status": resp.status_code, "error": f"unexpected status {resp.status_code}"}
        except ImportError:
            return {"healthy": False, "latency_ms": 0, "http_status": 0, "error": "requests library not available"}
        except Exception as exc:
            return {"healthy": False, "latency_ms": round((time.monotonic() - start) * 1000, 2), "http_status": 0, "error": str(exc)}

    def _health_check_openrouter(self, model: str, start: float) -> Dict[str, Any]:
        try:
            import requests as req_lib
            resp = req_lib.get(
                f"https://openrouter.ai/api/v1/models/{model}",
                timeout=HEALTH_CHECK_TIMEOUT_SEC,
            )
            elapsed = round((time.monotonic() - start) * 1000, 2)
            if resp.status_code == 200:
                return {"healthy": True, "latency_ms": elapsed, "http_status": 200}
            return {"healthy": False, "latency_ms": elapsed, "http_status": resp.status_code, "error": f"status {resp.status_code}"}
        except Exception as exc:
            return {"healthy": False, "latency_ms": round((time.monotonic() - start) * 1000, 2), "http_status": 0, "error": str(exc)}


# ===========================================================================
# OllamaManager
# ===========================================================================

class OllamaManager:
    """Manages local Ollama model discovery and health checks."""

    def __init__(self, logger: Optional[StructuredLogger] = None) -> None:
        self.logger = logger or StructuredLogger()
        self._models_cache: Optional[List[str]] = None
        self._cache_time: float = 0

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def list_models(self) -> List[str]:
        now = time.monotonic()
        if self._models_cache is not None and (now - self._cache_time) < 60:
            return list(self._models_cache)
        models = self._discover_models()
        self._models_cache = models
        self._cache_time = now
        return list(models)

    def _discover_models(self) -> List[str]:
        if not self.is_available():
            return []
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                self.logger.warning("ollama list returned non-zero", component="ollama")
                return []
            models: List[str] = []
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 1 and ":" in parts[0]:
                    models.append(parts[0])
            self.logger.info(f"Discovered {len(models)} Ollama model(s)", component="ollama")
            return models
        except subprocess.TimeoutExpired:
            self.logger.warning("ollama list timed out", component="ollama")
            return []
        except Exception as exc:
            self.logger.warning(f"ollama list error: {exc}", component="ollama")
            return []

    def health_check(self, model: str) -> Dict[str, Any]:
        if not self.is_available():
            return {"available": False, "error": "ollama not installed"}
        try:
            result = subprocess.run(
                ["ollama", "show", model],
                capture_output=True, text=True, timeout=HEALTH_CHECK_TIMEOUT_SEC,
            )
            if result.returncode == 0:
                return {"available": True, "model": model, "healthy": True}
            return {"available": True, "model": model, "healthy": False, "error": result.stderr.strip()[:200]}
        except subprocess.TimeoutExpired:
            return {"available": True, "model": model, "healthy": False, "error": "timeout"}
        except Exception as exc:
            return {"available": True, "model": model, "healthy": False, "error": str(exc)}

    def select_fallback(self) -> Optional[str]:
        """Return the best available Ollama model based on priority list."""
        if not self.is_available():
            return None
        priority = MODEL_POLICY.get("ollama_priority", [])
        installed = self.list_models()
        for target in priority:
            for installed_model in installed:
                if installed_model.startswith(target):
                    check = self.health_check(installed_model)
                    if check.get("healthy"):
                        return installed_model
        # Fallback: return first healthy model
        for installed_model in installed:
            check = self.health_check(installed_model)
            if check.get("healthy"):
                return installed_model
        return None


# ===========================================================================
# ProcessLockManager
# ===========================================================================
class ProcessLockManager:
    """Prevents duplicate Marcus instances; handles stale lock cleanup.

    Uses file-level advisory locking (fcntl on Unix, msvcrt on Windows)
    plus PID tracking for stale lock detection and cleanup.
    """

    def __init__(self, lock_dir: Path = _RUNTIME_DIR, logger: Optional[StructuredLogger] = None) -> None:
        self.lock_dir = lock_dir
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file_path = self.lock_dir / ".marcus.lock"
        self.pid_file = _PID_FILE
        self.logger = logger or StructuredLogger()
        self._my_pid = os.getpid()
        self._lock_fd: Optional[int] = None

    def acquire(self) -> bool:
        """Try to acquire the lock. Returns False if another healthy instance holds it."""
        if self._is_stale_lock():
            self._cleanup_stale_lock()

        # Open the lock file for exclusive file-level locking
        try:
            fd = os.open(str(self.lock_file_path), os.O_CREAT | os.O_RDWR, 0o644)
        except OSError as exc:
            self.logger.warning(f"Lock file open error: {exc}", component="lock")
            return False

        # Determine appropriate locking call for this platform
        try:
            import msvcrt  # Windows
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except (IOError, OSError):
                # Lock is held by another process
                os.close(fd)
                self.logger.warning(f"Lock held by another process", component="lock")
                return False
        except ImportError:
            # Unix — use fcntl
            import fcntl
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError):
                os.close(fd)
                self.logger.warning(f"Lock held by another process", component="lock")
                return False

        # Write our PID to the lock file (overwrite any stale content)
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, f"{self._my_pid}\n".encode("utf-8"))
        os.fsync(fd)

        self._lock_fd = fd

        # Write PID file for external tooling
        try:
            with open(str(self.pid_file), "w", encoding="utf-8") as pf:
                pf.write(str(self._my_pid))
                pf.flush()
                os.fsync(pf.fileno())
        except OSError:
            pass

        self.logger.info(f"Lock acquired (PID {self._my_pid})", component="lock")
        return True

    def release(self) -> None:
        """Release the lock gracefully."""
        try:
            if self._lock_fd is not None:
                try:
                    import msvcrt
                    try:
                        msvcrt.locking(self._lock_fd, msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                except ImportError:
                    import fcntl
                    try:
                        fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                    except Exception:
                        pass
                try:
                    os.close(self._lock_fd)
                except OSError:
                    pass
                self._lock_fd = None
            # Remove lock and PID files
            try:
                if self.lock_file_path.exists():
                    self.lock_file_path.unlink()
            except OSError:
                pass
            try:
                if self.pid_file.exists():
                    self.pid_file.unlink()
            except OSError:
                pass
            self.logger.info("Lock released", component="lock")
        except Exception as exc:
            self.logger.warning(f"Lock release error: {exc}", component="lock")

    def _is_stale_lock(self) -> bool:
        """Check if the lock file exists and its PID is not alive."""
        if not self.lock_file_path.exists():
            return False
        pid = self._read_pid_from_lock()
        if pid is None:
            return False
        if not self._is_pid_alive(pid):
            return True
        return False

    def _cleanup_stale_lock(self) -> None:
        try:
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
            if self.pid_file.exists():
                self.pid_file.unlink()
            self.logger.info("Cleaned up stale lock files", component="lock")
        except OSError:
            pass

    def _read_pid_from_lock(self) -> Optional[int]:
        if self.lock_file_path.exists():
            try:
                content = self.lock_file_path.read_text(encoding="utf-8").strip()
                return int(content)
            except (ValueError, OSError):
                pass
        return None

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False


# ===========================================================================
# MarcusRuntime (extended with hardening)
# ===========================================================================

class MarcusRuntime:
    """Typed runtime model for the Marcus orchestration agent (hardened)."""

    def __init__(self) -> None:
        self.agent_id = "marcus"
        self.name = "Marcus"
        self.role = "Commander, Chief of Staff, Chief Improvement Officer"
        self.responsibilities = [
            "Coordinate Lyons Command Center operations",
            "Route tasks to registered specialist agents",
            "Load and maintain system context from trusted repository files",
            "Record execution history and session state",
            "Expose health and status reporting",
            "Enforce security boundaries and redact secrets from logs",
            "Manage provider chain with circuit breaker and cooldown",
            "Coordinate Ollama local fallback",
        ]
        self.permitted_skills: List[str] = []
        self.specialist_routes: Dict[str, Dict[str, Any]] = {}
        self.system_context: Dict[str, Any] = {}
        self.session_state: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.health_status = "not_initialized"
        self.provider_chain: Optional[ProviderChain] = None
        self.ollama_manager: Optional[OllamaManager] = None
        self.persistence: Optional[PersistenceManager] = None
        self.logger: Optional[StructuredLogger] = None
        self.lock_manager: Optional[ProcessLockManager] = None
        self.started_at: str = ""
        self.last_checkpoint: str = ""
        self._shutdown_requested = False

    def initialize_hardening(
        self,
        persistence: Optional[PersistenceManager] = None,
        logger: Optional[StructuredLogger] = None,
    ) -> None:
        """Initialize hardening subsystems."""
        self.logger = logger or StructuredLogger()
        self.persistence = persistence or PersistenceManager()
        self.lock_manager = ProcessLockManager(self.persistence.runtime_dir, self.logger)
        self.provider_chain = ProviderChain(persistence=self.persistence, logger=self.logger)
        self.ollama_manager = OllamaManager(self.logger)

        # Register graceful shutdown
        atexit.register(self.graceful_shutdown)
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, self._signal_handler)
            except (OSError, ValueError):
                pass

    def _signal_handler(self, signum: int, frame: Any) -> None:
        self.logger.warning(f"Received signal {signum}, initiating graceful shutdown", component="marcus")
        self._shutdown_requested = True
        self.graceful_shutdown()
        sys.exit(0)

    def graceful_shutdown(self) -> None:
        """Gracefully shut down: checkpoint work, save state, release locks."""
        self.logger.info("Initiating graceful shutdown", component="marcus")
        self.session_state["shutdown_at"] = datetime.now(timezone.utc).isoformat()
        self.session_state["completed_checkpoints"] = len(self.execution_history)
        if self.persistence and self.session_state:
            self.persistence.save_state({"session_state": self.session_state, "runtime": self._as_dict()})
        if self.lock_manager:
            self.lock_manager.release()
        self.logger.info("Graceful shutdown complete", component="marcus")

    def _as_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "health_status": self.health_status,
            "started_at": self.started_at,
            "last_checkpoint": self.last_checkpoint,
            "responsibilities_count": len(self.responsibilities),
            "specialists_count": len(self.specialist_routes),
            "execution_history_count": len(self.execution_history),
        }

    def load_persisted_state(self) -> None:
        """Restore Marcus state from persistent storage after restart."""
        if not self.persistence:
            return
        saved_state = self.persistence.load_state()
        if not saved_state:
            return
        # Support canonical nested schema, legacy _as_dict() flat output,
        # and any flat dict with health_status at root level (e.g. tests)
        session = saved_state.get("session_state", {})
        runtime = saved_state.get("runtime", {})
        if not runtime and ("agent_id" in saved_state or "health_status" in saved_state):
            # Legacy flat structure: migrate to canonical schema
            runtime = saved_state
            session = {}
        if session:
            self.session_state.update(session)
        if runtime:
            self.health_status = runtime.get("health_status", self.health_status)
            self.started_at = runtime.get("started_at", self.started_at)
            self.last_checkpoint = runtime.get("last_checkpoint", self.last_checkpoint)


# ===========================================================================
# Standalone helper functions (used by CLI)
# ===========================================================================

def load_trusted_context() -> Dict[str, Any]:
    """Load all trusted repository-controlled source files into context."""
    context: Dict[str, Any] = {}
    for path in KNOWN_TRUSTED_FILES:
        rel = str(path.relative_to(_REPO_ROOT))
        if not path.exists():
            context[rel] = {"exists": False, "title": ""}
            continue
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        title = next((l.lstrip("# ").strip() for l in lines if l.startswith("# ")), path.stem)
        context[rel] = {"exists": True, "title": title, "content": content}
    return context


def load_activation_manifest() -> Dict[str, Any]:
    manifest_path = _REPO_ROOT / "skills-registry" / "activation_manifest.json"
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"error": f"malformed activation manifest at {manifest_path}"}
    return {"error": f"missing activation manifest at {manifest_path}"}


def load_skills_registry() -> Dict[str, Any]:
    registry_path = _REPO_ROOT / "skills-registry" / "skills_registry.json"
    if registry_path.exists():
        try:
            return json.loads(registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"error": f"malformed skills registry at {registry_path}"}
    return {"error": f"missing skills registry at {registry_path}"}


DEFAULT_SPECIALISTS: Dict[str, Dict[str, Any]] = {
    "david":  {"name": "David",  "role": "Strategy and Executive Planning",      "skills": ["strategy", "executive-planning", "analysis"],                   "status": "available"},
    "evelyn": {"name": "Evelyn", "role": "Research and Intelligence",            "skills": ["research", "intelligence", "briefing"],                         "status": "available"},
    "miles":  {"name": "Miles",  "role": "Software Engineering and Development",  "skills": ["development", "engineering", "code-review"],                     "status": "available"},
    "victor": {"name": "Victor", "role": "Systems, Infrastructure, and Reliability","skills": ["infrastructure", "reliability", "ops"],                         "status": "available"},
    "sophia": {"name": "Sophia", "role": "Product Design, UX/UI, and Brand",     "skills": ["design", "ux", "ui", "brand"],                                  "status": "available"},
    "julian": {"name": "Julian", "role": "Banking, Fintech, and Financial",      "skills": ["banking", "fintech", "infrastructure"],                         "status": "available"},
    "elijah": {"name": "Elijah", "role": "Legal, Contracts, Compliance, and Risk","skills": ["legal", "compliance", "risk"],                                  "status": "available"},
    "grant":  {"name": "Grant",  "role": "Private Equity, Acquisitions, and Deals","skills": ["private-equity", "acquisitions", "deals"],                      "status": "available"},
    "caleb":  {"name": "Caleb",  "role": "Industrial Operations and Automation",  "skills": ["automation", "operations", "industrial"],                       "status": "available"},
    "naomi":  {"name": "Naomi",  "role": "Cybersecurity and Information Protection","skills": ["cybersecurity", "infosec", "protection"],                        "status": "available"},
    "olivia": {"name": "Olivia", "role": "Operations and Execution Management",  "skills": ["operations", "execution", "management"],                        "status": "available"},
    "grace":  {"name": "Grace",  "role": "Church Technology and Community",       "skills": ["church-tech", "community"],                                      "status": "available"},
    "jordan": {"name": "Jordan", "role": "Sales, Partnerships, and Business",    "skills": ["sales", "partnerships", "bizdev"],                              "status": "available"},
    "malcolm":{"name": "Malcolm","role": "Finance, Modeling, and Performance",   "skills": ["finance", "modeling", "analysis"],                              "status": "available"},
}


def identify_specialist_routes(activation: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    routes: Dict[str, Dict[str, Any]] = dict(DEFAULT_SPECIALISTS)
    for slot_name, slot_val in (activation or {}).items():
        if isinstance(slot_val, dict) and "error" not in str(slot_val):
            routes[slot_name] = {
                "name": slot_val.get("agent", slot_val.get("name", slot_name)),
                "skills": slot_val.get("skills", []),
                "status": slot_val.get("status", "available"),
                "source": "activation_manifest",
            }
    return routes


def initialize_marcus() -> Dict[str, Any]:
    """Bootstrap Marcus with full hardening."""
    logger = StructuredLogger()
    persistence = PersistenceManager(logger=logger)
    result: Dict[str, Any] = {
        "agent_id": "marcus",
        "steps": [],
        "warnings": [],
        "errors": [],
    }

    result["steps"].append("validating_repo_root")
    if not (_REPO_ROOT / "AGENTS.md").exists():
        result["errors"].append(f"missing required file: AGENTS.md")
        result["status"] = "failed"
        return result

    result["steps"].append("loading_trusted_context")
    context = load_trusted_context()
    result["trusted_context_loaded"] = len([v for v in context.values() if v.get("exists")])

    result["steps"].append("loading_manifests")
    activation = load_activation_manifest()
    registry = load_skills_registry()
    if "error" in activation:
        result["warnings"].append(activation["error"])
    if "error" in registry:
        result["warnings"].append(registry["error"])

    result["steps"].append("identifying_specialists")
    routes = identify_specialist_routes(activation, registry)

    result["steps"].append("initializing_hardening")
    runtime = MarcusRuntime()
    runtime.initialize_hardening(persistence=persistence, logger=logger)
    runtime.permitted_skills = list(routes.keys())
    runtime.specialist_routes = routes
    runtime.system_context = {"repo_root": str(_REPO_ROOT), "trusted_context_keys": list(context.keys())}
    runtime.started_at = datetime.now(timezone.utc).isoformat()

    # Try to restore persisted state (may overwrite health_status)
    runtime.load_persisted_state()

    # Set health_status = "initialized" AFTER loading persisted state
    # so it takes precedence over any stale persisted value
    runtime.health_status = "initialized"

    # Save initial state
    persistence.save_state(runtime._as_dict())

    # Run provider health checks
    result["steps"].append("provider_health_checks")
    provider_chain = ProviderChain(persistence=persistence, logger=logger)
    runtime.provider_chain = provider_chain

    for entry in MODEL_POLICY["preferred"] + MODEL_POLICY["secondary"]:
        health = provider_chain.health_check(entry["provider"], entry["model"])
        tag = "healthy" if health.get("healthy") else f"unhealthy ({health.get('error','unknown')})"
        logger.info(f"Provider check: {entry['provider']}/{entry['model']} = {tag}", component="provider")

    # Check Ollama
    ollama = OllamaManager(logger=logger)
    runtime.ollama_manager = ollama
    ollama_models = ollama.list_models()
    ollama_fallback = ollama.select_fallback()
    if ollama_fallback:
        logger.info(f"Ollama fallback model selected: {ollama_fallback}", component="ollama")
    else:
        logger.warning("No Ollama fallback model available", component="ollama")

    runtime.health_status = "initialized"
    global _initialized_runtime
    _initialized_runtime = runtime

    # Save final state
    persistence.save_state(runtime._as_dict())

    result["status"] = "initialized"
    result["marcus_runtime"] = runtime._as_dict()
    result["specialists_discovered"] = len(routes)
    result["ollama_models"] = ollama_models
    result["ollama_fallback"] = ollama_fallback
    result["warnings"] = result.get("warnings", [])
    result["errors"] = result.get("errors", [])
    return result


def route_task(task: Dict[str, Any], runtime: Optional[MarcusRuntime] = None) -> Dict[str, Any]:
    """Route a task to the appropriate registered specialist."""
    if not isinstance(task, dict):
        return {"status": "rejected", "reason": "task must be a dict with a 'command' key", "routed_to": "marcus"}

    command = task.get("command", "").strip().lower()
    specialist = task.get("specialist", "").strip().lower()

    routes = (runtime.specialist_routes if runtime and runtime.specialist_routes else DEFAULT_SPECIALISTS)
    if specialist and specialist in routes:
        return {"status": "routed", "command": command, "routed_to": specialist, "routing_decision": "direct_specialist"}

    # Keyword-based routing
    keyword_routes = {
        "strategy": "david", "executive": "david", "plan": "david",
        "research": "evelyn", "brief": "evelyn", "intelligence": "evelyn",
        "code": "miles", "develop": "miles", "engineer": "miles", "review": "miles",
        "infrastructure": "victor", "system": "victor", "reliability": "victor", "deploy": "victor",
        "design": "sophia", "ux": "sophia", "ui": "sophia",
        "bank": "julian", "fintech": "julian", "financial": "julian",
        "legal": "elijah", "compliance": "elijah", "contract": "elijah",
        "equity": "grant", "deal": "grant", "acquisition": "grant",
        "automate": "caleb", "operate": "caleb",
        "security": "naomi", "cyber": "naomi", "protect": "naomi",
        "execute": "olivia",
        "church": "grace",
        "sales": "jordan", "partner": "jordan",
        "finance": "malcolm", "model": "malcolm", "performance": "malcolm",
    }
    for keyword, owner in keyword_routes.items():
        if keyword in command:
            return {"status": "routed", "command": command, "routed_to": owner, "routing_decision": f"keyword_match:{keyword}"}

    return {"status": "routed", "command": command, "routed_to": "marcus", "routing_decision": "marcus_coordination"}


def execute_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Route a task and record in execution history."""
    routing = route_task(task)
    return routing


def get_status(runtime: Optional[MarcusRuntime] = None) -> Dict[str, Any]:
    if runtime is None:
        global _initialized_runtime
        if _initialized_runtime is not None:
            runtime = _initialized_runtime
        else:
            runtime = MarcusRuntime()
            runtime.specialist_routes = DEFAULT_SPECIALISTS
            runtime.health_status = "not_initialized"
            return {
                "agent_id": runtime.agent_id,
                "name": runtime.name,
                "role": runtime.role,
                "health_status": runtime.health_status,
                "specialists_available": len(runtime.specialist_routes),
                "execution_history_count": len(runtime.execution_history),
                "permitted_skills": runtime.permitted_skills,
            }
    return {
        "agent_id": runtime.agent_id,
        "name": runtime.name,
        "role": runtime.role,
        "health_status": runtime.health_status,
        "started_at": runtime.started_at,
        "specialists_available": len(runtime.specialist_routes),
        "execution_history_count": len(runtime.execution_history),
        "permitted_skills": runtime.permitted_skills,
        "provider_chain_healthy": runtime.provider_chain is not None,
        "ollama_available": runtime.ollama_manager.is_available() if runtime.ollama_manager else False,
        "session_state": runtime.session_state,
    }


def validate_config() -> Dict[str, Any]:
    """Validate all trusted configuration files."""
    missing = []
    for f in KNOWN_TRUSTED_FILES:
        if not f.exists():
            missing.append(str(f.relative_to(_REPO_ROOT)))
    return {
        "trusted_files_missing": missing,
        "all_trusted_files_present": len(missing) == 0,
        "runtime_dir_exists": _RUNTIME_DIR.exists(),
    }


def list_specialists() -> Dict[str, Any]:
    return {"specialists": DEFAULT_SPECIALISTS, "count": len(DEFAULT_SPECIALISTS)}


# ===========================================================================
# Watchdog
# ===========================================================================

class MarcusWatchdog:
    """Component-level health monitor that restarts only failed components."""

    def __init__(self, logger: Optional[StructuredLogger] = None) -> None:
        self.logger = logger or StructuredLogger()
        self.components: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def register_component(
        self,
        name: str,
        check_fn: Callable[[], bool],
        restart_fn: Optional[Callable[[], None]] = None,
        interval_sec: int = 30,
    ) -> None:
        self.components[name] = {
            "check": check_fn,
            "restart": restart_fn,
            "interval_sec": interval_sec,
            "last_check": "",
            "healthy": True,
            "consecutive_failures": 0,
            "last_restart_at": "",
            "component_type": name,
        }

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True, name="marcus-watchdog")
        self._thread.start()
        self.logger.info("Watchdog started", component="watchdog")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Watchdog stopped", component="watchdog")

    def _watch_loop(self) -> None:
        while self._running:
            for name, comp in list(self.components.items()):
                try:
                    healthy = comp["check"]()
                except Exception as exc:
                    healthy = False
                    self.logger.error(f"Watchdog check failed for {name}: {exc}", component="watchdog")

                comp["last_check"] = datetime.now(timezone.utc).isoformat()
                if healthy:
                    comp["consecutive_failures"] = 0
                    comp["healthy"] = True
                else:
                    comp["consecutive_failures"] += 1
                    comp["healthy"] = False
                    self.logger.warning(f"Component {name} unhealthy (failures: {comp['consecutive_failures']})", component="watchdog")
                    if comp["restart"] and comp["consecutive_failures"] >= 2:
                        self.logger.info(f"Restarting component {name}", component="watchdog")
                        try:
                            comp["restart"]()
                            comp["last_restart_at"] = datetime.now(timezone.utc).isoformat()
                            comp["consecutive_failures"] = 0
                            comp["healthy"] = True
                        except Exception as exc:
                            self.logger.error(f"Restart of {name} failed: {exc}", component="watchdog")
            time.sleep(10)


# ===========================================================================
# Windows startup helper
# ===========================================================================

def get_windows_startup_script() -> str:
    """Generate a Windows batch script for startup and recovery."""
    runtime_dir = str(_RUNTIME_DIR)
    repo_dir = str(_REPO_ROOT)
    script = f"""@echo off
REM Lyons Command Center -- Marcus startup script
REM Generated: {datetime.now(timezone.utc).isoformat()}

set REPO_DIR={repo_dir}
set RUNTIME_DIR={runtime_dir}
set PYTHONPATH=%REPO_DIR%

if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%"

cd /d "%REPO_DIR%\\platform"

python -m marcus.marcus start
if %ERRORLEVEL% neq 0 (
    echo Marcus failed to start, sleeping 10s before retry...
    timeout /t 10 /nobreak >nul
    python -m marcus.marcus start
)

echo Marcus startup complete.
"""
    return script


def get_schtasks_install_command() -> str:
    """Return the Windows scheduled task creation command (requires admin)."""
    script_path = _RUNTIME_DIR / "start-marcus.bat"
    return (
        f'schtasks /create /tn "Marcus Command Center" '
        f'/tr "{script_path}" '
        f'/sc onlogon /rl highest /f /ru "%USERNAME%"'
    )


# ===========================================================================
# CLI
# ===========================================================================

def _print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, default=str))


def cli_main(args: Optional[List[str]] = None) -> int:
    """Marcus hardened CLI."""
    import argparse

    parser = argparse.ArgumentParser(prog="marcus", description="Marcus orchestration agent (hardened)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("start", help="Initialize Marcus with full hardening")
    sub.add_parser("status", help="Report runtime status and component health")
    sub.add_parser("list", help="List registered specialists")
    sub.add_parser("validate", help="Validate all trusted configuration files")
    sub.add_parser("context", help="Load and summarize trusted context")
    sub.add_parser("health", help="Run full local health verification")

    rp = sub.add_parser("route", help="Route a task to a specialist")
    rp.add_argument("command", nargs="?", default="")
    rp.add_argument("--specialist", default="")

    ep = sub.add_parser("execute", help="Route and execute a task")
    ep.add_argument("command", nargs="?", default="")

    sub.add_parser("provider", help="Show provider chain status")
    sub.add_parser("watchdog", help="Show watchdog status")
    sub.add_parser("state", help="Show persisted runtime state")

    parsed = parser.parse_args(args)

    if parsed.command == "start":
        result = initialize_marcus()
        if result.get("errors"):
            _print_json({"status": "failed", "errors": result["errors"]})
            return 1
        _print_json({
            "marcus": "initialized",
            "specialists": result.get("specialists_discovered", 0),
            "trusted_context_loaded": result.get("trusted_context_loaded", 0),
            "ollama_models": result.get("ollama_models", []),
            "ollama_fallback": result.get("ollama_fallback"),
            "steps": result.get("steps", []),
            "warnings": result.get("warnings", []),
        })
        return 0

    if parsed.command == "status":
        _print_json(get_status())
        return 0

    if parsed.command == "list":
        _print_json(list_specialists())
        return 0

    if parsed.command == "validate":
        _print_json(validate_config())
        return 0

    if parsed.command == "context":
        ctx = load_trusted_context()
        summary = {k: {"exists": v.get("exists"), "title": v.get("title", "")} for k, v in ctx.items()}
        _print_json({"trusted_context": summary, "total": len(summary)})
        return 0

    if parsed.command == "health":
        result = initialize_marcus()
        config_valid = validate_config()
        _print_json({
            "marcus_initialized": result.get("status") == "initialized",
            "config_valid": config_valid.get("all_trusted_files_present", False),
            "specialists_discovered": result.get("specialists_discovered", 0),
            "trusted_context_loaded": result.get("trusted_context_loaded", 0),
            "ollama_available": result.get("ollama_fallback") is not None,
            "ollama_fallback_model": result.get("ollama_fallback"),
            "installed_ollama_models": result.get("ollama_models", []),
            "runtime_state_persisted": (_RUNTIME_DIR / "marcus-state.json").exists(),
            "errors": result.get("errors", []),
        })
        return 0

    if parsed.command == "route":
        command_text = parsed.command
        task = {"command": command_text}
        if parsed.specialist:
            task["specialist"] = parsed.specialist
        _print_json(route_task(task))
        return 0

    if parsed.command == "execute":
        task = {"command": parsed.command}
        _print_json(execute_task(task))
        return 0

    if parsed.command == "provider":
        pc = ProviderChain()
        preferred_health = []
        for entry in MODEL_POLICY["preferred"] + MODEL_POLICY["secondary"]:
            h = pc.health_check(entry["provider"], entry["model"])
            preferred_health.append(h)
        ollama = OllamaManager()
        ollama_models = ollama.list_models()
        ollama_fb = ollama.select_fallback()
        _print_json({
            "preferred_models": preferred_health,
            "ollama_models": ollama_models,
            "ollama_fallback": ollama_fb,
        })
        return 0

    if parsed.command == "watchdog":
        wd = MarcusWatchdog()
        _print_json({
            "running": wd._running,
            "components_registered": len(wd.components),
            "components": {k: {"healthy": v["healthy"], "last_check": v["last_check"], "type": v["component_type"]} for k, v in wd.components.items()},
        })
        return 0

    if parsed.command == "state":
        pm = PersistenceManager()
        state = pm.load_state()
        provider_health = pm.load_provider_health()
        history_lines = 0
        if _HISTORY_FILE.exists():
            try:
                history_lines = sum(1 for _ in open(_HISTORY_FILE, encoding="utf-8"))
            except OSError:
                pass
        _print_json({
            "runtime_state_exists": (_RUNTIME_DIR / "marcus-state.json").exists(),
            "provider_health_exists": (_RUNTIME_DIR / "provider-health.json").exists(),
            "state": state,
            "provider_health": provider_health,
            "execution_history_lines": history_lines,
        })
        return 0

    parser.print_help()
    return 0