#!/usr/bin/env python3
"""Database backup and restore validation for production readiness."""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

_BACKUP_DIR = Path(os.environ.get("LYONS_BACKUP_DIR", "launch/evidence/db_backup"))
_POSTGRES_DUMP = os.environ.get("PG_DUMP", "pg_dump")
_RESTORE_DUMP = os.environ.get("PSQL", "psql")
_MANIFEST = _BACKUP_DIR / "db_backup_manifest.json"


def _ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def backup_postgres() -> dict[str, Any]:
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not dsn:
        return {"timestamp": _ts(), "status": "skipped", "evidence": "DATABASE_URL/POSTGRES_URL not set"}
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dump_file = _BACKUP_DIR / f"backup-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S')}.sql"
    cmd = [_POSTGRES_DUMP, dsn, "-F", "c" if "pg_dump" in _POSTGRES_DUMP else "p", "-f", str(dump_file), "--no-owner"]
    probe = subprocess.run(cmd, capture_output=True, text=True, check=False)
    passed = probe.returncode == 0 and dump_file.exists() and dump_file.stat().st_size > 0
    manifest = {
        "timestamp": _ts(),
        "status": "ok" if passed else "error",
        "backup_file": str(dump_file),
        "size_bytes": dump_file.stat().st_size if passed else 0,
        "stdout": probe.stdout,
        "stderr": probe.stderr,
        "command": " ".join(cmd),
    }
    _MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def restore_postgres(dump_file: Path) -> dict[str, Any]:
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not dsn or not dump_file.exists():
        return {"timestamp": _ts(), "status": "skipped", "evidence": "missing dsn or dump file"}
    restore = subprocess.run([_RESTORE_DUMP, dsn, "-f", str(dump_file)], capture_output=True, text=True, check=False)
    passed = restore.returncode == 0
    return {"timestamp": _ts(), "status": "ok" if passed else "error", "command": f"psql restore {dump_file}", "stdout": restore.stdout, "stderr": restore.stderr}


def main() -> int:
    backup = backup_postgres()
    print(json.dumps(backup, ensure_ascii=False, indent=2))
    if backup.get("status") == "ok":
        restore = restore_postgres(Path(backup["backup_file"]))
        print(json.dumps(restore, ensure_ascii=False, indent=2))
        return 0 if restore.get("status") == "ok" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
