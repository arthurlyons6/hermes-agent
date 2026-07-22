#!/usr/bin/env python3
"""Railway health, Telegram heartbeat, volume, Postgres, and gateway probes."""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

_RAILWAY_HEALTH_URL = os.environ.get("RAILWAY_HEALTH_URL", "http://localhost:8080/health")
_TELEGRAM_ENDPOINT = "https://api.telegram.org/bot{token}/getMe"
_VOLUME_TEST_PATH = "/opt/data/launch_runtime/healthprobe.txt"


def _ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _run(cmd: list[str] | str) -> dict[str, Any]:
    try:
        p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, check=False)
        return {"cmd": cmd, "stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode}
    except Exception as exc:
        return {"cmd": cmd, "error": str(exc), "returncode": -1}


def check_gateway_health() -> dict[str, Any]:
    import urllib.request
    try:
        req = urllib.request.Request(_RAILWAY_HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            code = resp.status
        return {"timestamp": _ts(), "status": str(code), "evidence": body, "result": "passed" if code == 200 else "failed"}
    except Exception as exc:
        return {"timestamp": _ts(), "status": "error", "evidence": str(exc), "result": "failed"}


def check_telegram_heartbeat() -> dict[str, Any]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"timestamp": _ts(), "status": "skipped", "command": "telegram getMe", "evidence": "TELEGRAM_BOT_TOKEN not set", "result": "failed"}
    probe = _run(["python", "-c", f"import urllib.request; print(urllib.request.urlopen('{_TELEGRAM_ENDPOINT.format(token=token)}').read().decode())"])
    out = probe.get("stdout", "")
    try:
        data = json.loads(out)
        ok = data.get("ok") is True
    except Exception:
        ok = False
    return {"timestamp": _ts(), "status": "ok" if ok else "error", "command": _TELEGRAM_ENDPOINT.format(token=token), "evidence": out[:500], "result": "passed" if ok else "failed"}


def check_persistent_volume() -> dict[str, Any]:
    base = Path(_VOLUME_TEST_PATH).parent
    try:
        base.mkdir(parents=True, exist_ok=True)
        probe_file = base / "healthprobe.txt"
        payload = f"{_ts()}\nhealthprobe\n"
        probe_file.write_text(payload, encoding="utf-8")
        readback = probe_file.read_text(encoding="utf-8") == payload
        probe_file.unlink(missing_ok=True)
        passed = readback and base.exists()
        return {"timestamp": _ts(), "status": "ok" if passed else "error", "command": f"write/read {probe_file}", "evidence": f"base_exists={base.exists()}", "result": "passed" if passed else "failed"}
    except Exception as exc:
        return {"timestamp": _ts(), "status": "error", "command": f"write/read {_VOLUME_TEST_PATH}", "evidence": str(exc), "result": "failed"}


def check_postgres() -> dict[str, Any]:
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not dsn:
        return {"timestamp": _ts(), "status": "skipped", "command": "psql $DATABASE_URL", "evidence": "DATABASE_URL/POSTGRES_URL not set", "result": "failed"}
    probe = _run(["python", "-c", f"import urllib.parse as up,psycopg2; c=psycopg2.connect('{dsn}'); cur=c.cursor(); cur.execute('SELECT 1'); print(cur.fetchone()); c.close()"])
    passed = probe.get("stdout", "").strip() == "(1,)" and probe.get("returncode") == 0
    return {"timestamp": _ts(), "status": "ok" if passed else "error", "command": f"psycopg2 connect SELECT 1", "evidence": probe.get("stdout", ""), "result": "passed" if passed else "failed"}


def write_evidence(record: dict[str, Any], label: str) -> Path:
    path = Path("launch/evidence") / f"{label}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    results = {
        "generated": _ts(),
        "checks": {
            "gateway": check_gateway_health(),
            "telegram": check_telegram_heartbeat(),
            "persistent_volume": check_persistent_volume(),
            "postgres": check_postgres(),
        },
    }
    print(json.dumps(results, ensure_ascii=False, indent=2))
    for label, record in results["checks"].items():
        write_evidence(record, label)
    return 0 if all((v.get("result") == "passed" or v.get("status") == "skipped") for v in results["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
