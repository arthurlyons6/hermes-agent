from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class BriefItem:
    label: str
    value: str
    provenance: str  # live | cached | synthetic | pending | unavailable
    updated_at: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_executive_brief(
    *,
    calendar: Optional[Dict[str, Any]] = None,
    blackgold: Optional[Dict[str, Any]] = None,
    pipeline: Optional[Dict[str, Any]] = None,
    approvals: Optional[Dict[str, Any]] = None,
    banking: Optional[Dict[str, Any]] = None,
    portfolio: Optional[Dict[str, Any]] = None,
    market: Optional[Dict[str, Any]] = None,
    workforce: Optional[Dict[str, Any]] = None,
    infra: Optional[Dict[str, Any]] = None,
    failed_jobs: Optional[Dict[str, Any]] = None,
    financial: Optional[Dict[str, Any]] = None,
    weather: Optional[Dict[str, Any]] = None,
    scripture: Optional[str] = None,
    priorities: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a structured executive briefing with per-section provenance.

    Every section records whether its data is live, cached, synthetic,
    pending, or unavailable.
    """
    return {
        "generated_at": _now(),
        "currency": "USD",
        "timezone": "UTC",
        "executive_summary": {
            "text": "System is validating end-to-end briefing generation.",
            "provenance": "synthetic",
            "updated_at": _now(),
        },
        "sections": [
            "calendar",
            "blackgold_priority_items",
            "deal_pipeline",
            "approval_queue",
            "banking_and_gci",
            "portfolio_alerts",
            "market_intelligence",
            "ai_workforce_status",
            "infrastructure_health",
            "failed_jobs",
            "financial_alerts",
            "weather",
            "scripture",
            "top_executive_priorities",
        ],
        "calendar": _section(calendar, _now()),
        "blackgold_priority_items": _section(blackgold, _now()),
        "deal_pipeline": _section(pipeline, _now()),
        "approval_queue": _section(approvals, _now()),
        "banking_and_gci": _section(banking, _now()),
        "portfolio_alerts": _section(portfolio, _now()),
        "market_intelligence": _section(market, _now()),
        "ai_workforce_status": _section(workforce, _now()),
        "infrastructure_health": _section(infra, _now()),
        "failed_jobs": _section(failed_jobs, _now()),
        "financial_alerts": _section(financial, _now()),
        "weather": _section(weather, _now()),
        "scripture": _scripture_section(scripture, _now()),
        "top_executive_priorities": _section(priorities, _now()),
        "provenance_legend": {
            "live": "Real operational data",
            "cached": "Recent data returned from storage",
            "synthetic": "Generated placeholder pending integration",
            "pending": "Awaiting upstream source",
            "unavailable": "Integration not yet connected",
        },
    }


def _section(value: Optional[Dict[str, Any]], updated_at: str) -> Dict[str, Any]:
    if value is None:
        return {"data": {}, "provenance": "unavailable", "updated_at": updated_at}
    return {
        "data": value.get("data", value),
        "provenance": value.get("provenance", "synthetic"),
        "updated_at": value.get("updated_at", updated_at),
    }


def _scripture_section(value: Optional[str], updated_at: str) -> Dict[str, Any]:
    if not value:
        return {"data": "", "provenance": "unavailable", "updated_at": updated_at}
    return {"data": value, "provenance": "cached", "updated_at": updated_at}


def remainder(item: str, text: str) -> str:
    return text[len(item):].strip()


def store_brief(pack: Dict[str, Any], db_path: str = "/app/.hermes/executions.db") -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS briefs (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, payload TEXT)"
        )
        cur.execute(
            "INSERT INTO briefs(created_at, payload) VALUES(?, ?)",
            (_now(), json.dumps(pack)),
        )
        conn.commit()
        conn.close()
        return {"success": True, "id": pack.get("generated_at")}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
