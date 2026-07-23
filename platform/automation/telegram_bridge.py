#!/usr/bin/env python3
"""Lyons Command Center cockpit/telemetry automation harness."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from core.vault import optional
from core.config import Config

try:
    import requests as _requests
except Exception:  # pragma: no cover
    _requests = None  # type: ignore[assignment]

COCKIT_ROOT = Path(__file__).resolve().parent.parent.parent / "cockpit" / "static"
DEALS_PATH = COCKIT_ROOT / "data" / "deals.json"
BRIEfS_PATH = COCKIT_ROOT / "data" / "briefs.json"
ORDERS_PATH = COCKIT_ROOT / "data" / "orders.json"


def load_json(path: Path) -> Any:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def format_deals_text() -> str:
    deals = load_json(DEALS_PATH)
    lines = [f"Deal Desk Signal — {len(deals)} tracked"]
    for item in deals:
        lines.append(
            f"- {item['deal']}: {item['stage']} | Risk: {item['risk']} | Owner: {item['owner']}"
        )
    return "\n".join(lines)


def format_briefs_text() -> str:
    briefs = load_json(BRIEfS_PATH)
    lines = [f"Briefs & Research — {len(briefs)} items"]
    for item in briefs:
        lines.append(f"- {item['title']} ({item['source']}, {item['published_at']})")
    return "\n".join(lines)


def _normalize_match(value: Any) -> str:
    if not isinstance(value, str):
        return "pending"
    value = value.strip().lower()
    if value in {"matched", "clear", "approved", "selected"}:
        return "matched"
    if value in {"hold", "hard-stop", "stopped", "blocked"}:
        return "hold"
    return "pending"


def format_orders_text(mode: str = "marcus") -> str:
    orders = load_json(ORDERS_PATH)
    matched = [o for o in orders if _normalize_match(o.get("match")) == "matched"]
    pending = [o for o in orders if _normalize_match(o.get("match")) == "pending"]
    hold = [o for o in orders if _normalize_match(o.get("match")) == "hold"]

    if mode == "orders":
        lines = [f"Orders — {len(orders)} tracked", ""]
        for item in orders:
            lines.append(
                f"- {item['id']} {item['target']}: {item['stage']} | Risk: {item['risk']} | Match: {item.get('match','pending')}"
            )
        return "\n".join(lines)

    lines = [
        "Marcus Matching Orders",
        "",
        f"Matched: {len(matched)}",
    ]
    for item in matched:
        lines.append(f"- {item['id']} {item['target']} | Owner: {item['owner']} | {item['stage']}")

    lines += ["", f"Pending review: {len(pending)}"]
    for item in pending:
        lines.append(f"- {item['id']} {item['target']} | Owner: {item['owner']} | {item['stage']}")

    lines += ["", f"On hold: {len(hold)}"]
    for item in hold:
        lines.append(f"- {item['id']} {item['target']} | Owner: {item['owner']} | {item['stage']}")

    lines += ["", "Dispatch order: matched -> pending -> hold.", "Marcus ready."]
    return "\n".join(lines)


def telegram_send_message(text: str, chat_id: str, token: str) -> Dict[str, Any]:
    if _requests is None:
        return {"status": "error", "message": "requests missing from runtime"}

    resp = _requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=30,
    )
    try:
        payload = resp.json()
    except Exception:
        payload = {"raw": resp.text}
    return {"status": "ok" if resp.ok else "error", "response": payload}


def handle(command: str) -> str:
    cfg = Config()
    text = ""
    if command == "deals":
        text = format_deals_text()
    elif command in {"marcus", "orders"}:
        text = format_orders_text(mode=command)
    elif command == "briefs":
        text = format_briefs_text()
    else:
        text = "Cockpit: local shell at http://localhost:8537/index.html"

    if text and cfg.TELEGRAM_BOT_TOKEN and cfg.BLACKGOLD_GROUP:
        result = telegram_send_message(text, cfg.BLACKGOLD_GROUP, cfg.TELEGRAM_BOT_TOKEN)
        return f"SENT: {result.get('status', 'unknown')}\n{text}"

    return text


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cockpit"
    print(handle(cmd))
