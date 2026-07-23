from unittest.mock import MagicMock, patch

import pytest

from automation.telegram_bridge import handle


def test_command_cockpit(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("BLACKGOLD_GROUP", "-100123")

    fake = {"ok": True, "result": {"message_id": 1}}
    mock_post = MagicMock(return_value=MagicMock(ok=True, json=lambda: fake))

    with patch("automation.telegram_bridge._requests.post", mock_post):
        result = handle("cockpit")

    assert mock_post.called
    assert "localhost:8537/index.html" in result


def test_command_briefs(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("BLACKGOLD_GROUP", "-100123")

    fake = {"ok": True, "result": {"message_id": 2}}
    mock_post = MagicMock(return_value=MagicMock(ok=True, json=lambda: fake))

    with patch("automation.telegram_bridge._requests.post", mock_post):
        result = handle("briefs")

    assert "Briefs" in result


def test_command_deals(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("BLACKGOLD_GROUP", "-100123")

    fake = {"ok": True, "result": {"message_id": 3}}
    mock_post = MagicMock(return_value=MagicMock(ok=True, json=lambda: fake))

    with patch("automation.telegram_bridge._requests.post", mock_post):
        result = handle("deals")

    assert "Deal Desk Signal" in result
