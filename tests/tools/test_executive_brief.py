from __future__ import annotations

import json
import sqlite3

import pytest

from tools.briefing.executive_brief import (
    _scripture_section,
    _section,
    make_executive_brief,
    store_brief,
)


def _brief(**sections):
    return make_executive_brief(**sections)


def test_required_sections_present():
    brief = _brief()
    for section in [
        "executive_summary",
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
    ]:
        assert section in brief


def test_unavailable_defaults():
    brief = _brief()
    assert brief["weather"]["provenance"] == "unavailable"
    assert brief["calendar"]["provenance"] == "unavailable"


def test_provenance_override():
    brief = _brief(weather={"data": {"temp_c": 21}, "provenance": "live"})
    assert brief["weather"]["provenance"] == "live"
    assert brief["weather"]["data"]["temp_c"] == 21


def test_store_brief_persists(tmp_path):
    db = str(tmp_path / "briefs.db")
    brief = _brief(scripture="Provident")

    result = store_brief(brief, db_path=db)
    assert result["success"] is True
    assert result["id"] == brief["generated_at"]

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT payload FROM briefs")
    row = cur.fetchone()
    conn.close()
    assert row is not None
    assert json.loads(row[0])["generated_at"] == brief["generated_at"]


def test_scripture_wrapped():
    out = _scripture_section("Provident", "now")
    assert out["data"] == "Provident"
    assert out["provenance"] == "cached"

    empty = _scripture_section(None, "now")
    assert empty["provenance"] == "unavailable"


def test_wrap_with_empty_value():
    out = _section(None, "now")
    assert out["provenance"] == "unavailable"
    assert out["data"] == {}
