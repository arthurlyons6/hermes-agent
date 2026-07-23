import os
import pytest
from core.vault import SecretVault, VAULT, require, optional
from core.config import Config


def test_vault_get_existing(monkeypatch):
    monkeypatch.setenv("TEST_KEY", "abc")
    assert VAULT.get("TEST_KEY") == "abc"


def test_vault_get_missing_required():
    with pytest.raises(KeyError):
        require("MISSING_REQUIRED_KEY")


def test_vault_get_missing_optional():
    assert optional("MISSING_OPTIONAL_KEY", "fallback") == "fallback"


def test_config_reads_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token123")
    monkeypatch.setenv("BLACKGOLD_GROUP", "-100999")
    cfg = Config()
    assert cfg.TELEGRAM_BOT_TOKEN == "token123"
    assert cfg.BLACKGOLD_GROUP == "-100999"
