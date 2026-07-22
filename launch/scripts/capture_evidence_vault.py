#!/usr/bin/env python3
"""Operational Evidence Vault writer for launch artifacts."""
from __future__ import annotations

import datetime
import json
import os
import subprocess
from pathlib import Path

_ROOT = Path(os.environ.get("LYONS_EVIDENCE_ROOT", "launch/evidence/vault"))
_NOW = datetime.datetime.now(datetime.timezone.utc)
_DEFAULT_META = {
    "git_sha": os.environ.get("LYONS_GIT_SHA", "unknown"),
    "railway_deployment_id": os.environ.get("RAILWAY_DEPLOYMENT_ID", "unknown"),
    "operator": os.environ.get("USER", "unknown"),
    "model_used": os.environ.get("HERMES_MODEL", "unknown"),
}


def _ensure(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def capture(event_label: str, payload: dict[str, Any]) -> Path:
    stamp = _NOW.strftime("%Y-%m-%dT%H%M%SZ")
    month = _NOW.strftime("%Y-%m")
    day = _NOW.strftime("%Y-%m-%d")
    event_dir = _ROOT / f"{month}" / day / event_label / stamp
    _ensure(event_dir)
    record = {
        "timestamp": _NOW.isoformat(),
        **_DEFAULT_META,
        "event_label": event_label,
        "payload": payload,
    }
    out = event_dir / "evidence.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    path = capture("production-readiness", {"status": "in_progress", "acceptance_gates": []})
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
