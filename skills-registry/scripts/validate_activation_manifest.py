#!/usr/bin/env python3
"""Validate the Lyons controlled-activation manifest without changing runtime state."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_MANIFEST = Path("skills-registry/activation_manifest.json")


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(obj: dict) -> dict:
    package = obj.get("package", [])
    validated = obj.get("validated_pending_activation", [])
    held = obj.get("held", [])
    selected = [item for item in package if item.get("id")]
    gaps = [item for item in package if not item.get("id")]
    explicit_gaps = [
        item
        for item in package
        if isinstance(item.get("selected_reason"), str)
        and "gap — mark for separate evaluation" in item["selected_reason"]
    ]

    duplicate_ids = sorted(
        {
            x["id"]
            for x in selected
            if x.get("id") and sum(1 for y in selected if y.get("id") == x["id"]) > 1
        }
    )
    validated_status_errors = 0
    for item in validated:
        if item.get("status") != "validated_pending_activation":
            validated_status_errors += 1

    errors = 0
    messages = []
    if len(validated) != len(selected):
        messages.append("validated count does not match selected package size")
        errors += 1
    if len(gaps) != len(explicit_gaps):
        messages.append("untagged gaps in package must be marked as `selected_reason` containing `gap — mark for separate evaluation`")
        errors += 1
    if gaps:
        messages.append("gaps detected")
        errors += 1
    if duplicate_ids:
        messages.append("duplicate selection ids: " + ", ".join(duplicate_ids))
        errors += 1
    if validated_status_errors:
        messages.append("validated items with wrong status: " + str(validated_status_errors))
        errors += 1

    return {
        "selected_count": len(selected),
        "validated_pending_activation_count": len(validated),
        "held_count": len(held),
        "gaps": gaps,
        "duplicate_selection_ids": duplicate_ids,
        "validated_status_errors": validated_status_errors,
        "errors": errors,
        "messages": messages,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lyons activation manifest validator")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST), type=Path)
    args = ap.parse_args(argv)
    report = validate_manifest(load_manifest(args.manifest))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
