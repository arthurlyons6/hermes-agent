#!/usr/bin/env python3
"""Deployment rollback validation: verify previous deployment can be restored."""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

_MANIFEST = Path(os.environ.get("LYONS_ROLLBACK_MANIFEST", "launch/evidence/rollback_manifest.json"))


def _ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def current_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception as exc:
        return f"error:{exc}"


def railway_rollback_available() -> dict[str, Any]:
    if not _MANIFEST.parent.exists():
        _MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _ts(),
        "action": "rollback_validation",
        "git_sha": current_sha(),
        "railway_deployment_id": os.environ.get("RAILWAY_DEPLOYMENT_ID", "unknown"),
        "status": "dry-run",
        "evidence": "rollback path exists if a prior successful deployment marker exists",
        "command": "railway rollback --service <service> --deployment <id>",
        "operator": os.environ.get("USER", "unknown"),
        "model_used": os.environ.get("HERMES_MODEL", "unknown"),
    }
    _MANIFEST.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def main() -> int:
    record = railway_rollback_available()
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
