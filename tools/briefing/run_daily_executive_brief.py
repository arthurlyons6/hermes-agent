#!/usr/bin/env python3
"""Railway entrypoint for the Executive Telegram Briefing.

Run as a cron job, not a long-lived service.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

from tools.briefing.executive_brief import make_executive_brief, store_brief


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _deliver(brief: dict) -> dict:
    try:
        from tools.briefing.executive_brief_telegram import deliver_brief
    except Exception as exc:
        return {"success": False, "error": f"telegram module unavailable: {exc}"}
    return await deliver_brief(brief)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deliver", action="store_true", help="Send via Telegram")
    parser.add_argument("--db", default=os.environ.get("HERMES_DB", "/app/.hermes/executions.db"))
    args = parser.parse_args(argv)

    brief = make_executive_brief()
    captured_at = _now()
    brief["generated_at"] = captured_at
    brief["delivery"] = {"attempted": False, "result": {}}

    if args.deliver:
        brief["delivery"]["attempted"] = True
        try:
            result = asyncio.run(_deliver(brief))
            brief["delivery"]["result"] = result
        except Exception as exc:
            brief["delivery"]["result"] = {"success": False, "error": str(exc)}

    persist = store_brief(brief, db_path=args.db)
    brief["persistence"] = persist
    logging.getLogger().info("Brief generated=%s persisted=%s delivery_attempted=%s", captured_at, persist.get("success"), brief["delivery"]["attempted"])
    print(json.dumps(brief, ensure_ascii=False))
    return 0 if persist.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
