"""Tests for automation/telegram_bridge.py."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from automation.telegram_bridge import (
    format_deals_text,
    format_orders_text,
    format_briefs_text,
    handle,
)


def test_format_deals_text(tmp_path, monkeypatch):
    deals_path = tmp_path / "deals.json"
    deals_path.write_text(
        json.dumps([{"deal": "TestCo", "stage": "LOI", "risk": "Low", "owner": "Arthur"}]),
        encoding="utf-8",
    )
    monkeypatch.setattr("automation.telegram_bridge.DEALS_PATH", deals_path)
    text = format_deals_text()
    assert "TestCo" in text
    assert "LOI" in text


def test_format_briefs_text(tmp_path, monkeypatch):
    briefs_path = tmp_path / "briefs.json"
    briefs_path.write_text(
        json.dumps([{"title": "Brief 1", "source": "Test", "published_at": "2026-01-01T00:00:00Z"}]),
        encoding="utf-8",
    )
    monkeypatch.setattr("automation.telegram_bridge.BRIEfS_PATH", briefs_path)
    text = format_briefs_text()
    assert "Brief 1" in text


def _write_orders(path: Path) -> None:
    path.write_text(
        json.dumps([
            {
                "id": "ORD-1",
                "target": "Acme",
                "stage": "IC Review",
                "risk": "Low",
                "owner": "Arthur",
                "match": "matched",
                "updated_at": "2026-01-02T00:00:00Z",
            },
            {
                "id": "ORD-2",
                "target": "Beta",
                "stage": "LOI",
                "risk": "Watch",
                "owner": "Grant",
                "match": "pending",
                "updated_at": "2026-01-03T00:00:00Z",
            },
            {
                "id": "ORD-3",
                "target": "Gamma",
                "stage": "Teaser",
                "risk": "Hard Stop",
                "owner": "Julian",
                "match": "hold",
                "updated_at": "2026-01-04T00:00:00Z",
            },
        ]),
        encoding="utf-8",
    )


def test_format_marcus_orders(tmp_path, monkeypatch):
    orders_path = tmp_path / "orders.json"
    _write_orders(orders_path)
    monkeypatch.setattr("automation.telegram_bridge.ORDERS_PATH", orders_path)
    text = format_orders_text(mode="marcus")
    assert "ORD-1" in text
    assert "Matched:" in text
    assert "Pending review:" in text
    assert "On hold:" in text


def test_format_orders_verbatim(tmp_path, monkeypatch):
    orders_path = tmp_path / "orders.json"
    _write_orders(orders_path)
    monkeypatch.setattr("automation.telegram_bridge.ORDERS_PATH", orders_path)
    text = format_orders_text(mode="orders")
    assert "Orders — 3 tracked" in text
    assert "ORD-1 Acme" in text


def test_handle_commands_sends_telegram(monkeypatch):
    monkeypatch.setattr(
        "automation.telegram_bridge.DEALS_PATH",
        Path(__file__).resolve().parent.parent / "cockpit" / "static" / "data" / "deals.json",
    )
    monkeypatch.setattr(
        "automation.telegram_bridge.BRIEfS_PATH",
        Path(__file__).resolve().parent.parent / "cockpit" / "static" / "data" / "briefs.json",
    )
    monkeypatch.setattr(
        "automation.telegram_bridge.ORDERS_PATH",
        Path(__file__).resolve().parent.parent / "cockpit" / "static" / "data" / "orders.json",
    )
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("BLACKGOLD_GROUP", "-100123")

    fake = {"ok": True, "result": {"message_id": 1}}
    mock_post = MagicMock(return_value=MagicMock(ok=True, json=lambda: fake))

    with patch("automation.telegram_bridge._requests.post", mock_post):
        for command in ("deals", "briefs", "marcus", "orders"):
            result = handle(command)
            assert mock_post.called
            assert "SENT" in result
            mock_post.reset_mock()
