#!/usr/bin/env python3
"""Render a Quarto target from a document workflow package."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DEFAULT_PACKAGE = Path("launch/black-gold-business-plan.package.json")
DEFAULT_TEMPLATE = Path("launch/templates/quarto/black-gold/business-plan.qmd")
DEFAULT_OUTPUT = Path("launch/rendered/black-gold-business-plan.pdf")


def load_package(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"package not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def render(package_path: Path, template: Path, output: Path) -> int:
    package = load_package(package_path)
    if not template.exists():
        raise SystemExit(f"template not found: {template}")
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "quarto",
        "render",
        str(template),
        "--to",
        "pdf",
        "--output",
        str(output),
    ]
    res = subprocess.run(cmd, check=False, text=True, capture_output=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    if res.returncode != 0:
        print("quarto render failed")
        return 1
    print(f"render_output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(render(DEFAULT_PACKAGE, DEFAULT_TEMPLATE, DEFAULT_OUTPUT))
