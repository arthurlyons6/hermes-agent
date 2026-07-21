#!/usr/bin/env python3
"""Persistent volume health probe: write/read directory tree with creation timestamps."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

_VOLUME_ROOT = Path(os.environ.get("LYONS_VOLUME_ROOT", "/opt/data"))
_MANIFEST_NAME = "volume_manifest.json"


def _ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_probe(root: Path) -> dict[str, Any]:
    probe_dir = root / "launch" / "probes"
    probe_dir.mkdir(parents=True, exist_ok=True)
    probe_file = probe_dir / "evidence.txt"
    now = _ts()
    probe_file.write_text(f"{now}\nvolume health probe\n", encoding="utf-8")
    readback = probe_file.read_text(encoding="utf-8")
    manifest_path = probe_dir / _MANIFEST_NAME
    manifest = {"timestamp": now, "files": [p.name for p in sorted(root.rglob("*")) if p.is_file()][:200], "probe": readback}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"timestamp": now, "status": "ok" if readback.startswith(now) else "error", "evidence": str(probe_file), "manifest": str(manifest_path)}


def main() -> int:
    result = write_probe(_VOLUME_ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
