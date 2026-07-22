#!/usr/bin/env python3
"""Run Promptfoo regression tests for the Black Gold document pipeline."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DEFAULT_CONFIG = Path("launch/promptfoo.black-gold.yaml")


def run(cfg: Path) -> int:
    if not cfg.exists():
        raise SystemExit(f"Promptfoo config not found: {cfg}")
    cmd = ["npx", "promptfoo", "eval", "--config", str(cfg), "--json"]
    res = subprocess.run(cmd, check=False, text=True, capture_output=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    if res.returncode != 0:
        print("promptfoo eval failed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run(DEFAULT_CONFIG))
