"""Regression test for Railway Telegram connectability with env token.

With ``platforms.telegram: enabled: true`` and ``TELEGRAM_BOT_TOKEN``
provided at runtime, ``get_connected_platforms()`` must include
``Platform.TELEGRAM`` even when the token is not duplicated in YAML.
"""
from gateway.config import GatewayConfig, Platform, PlatformConfig


def test_telegram_connectable_when_enabled_with_token() -> None:
    cfg = GatewayConfig()
    cfg.platforms[Platform.TELEGRAM] = PlatformConfig(enabled=True, token="123456:ABC")

    assert Platform.TELEGRAM in cfg.get_connected_platforms(), (
        "telegram must be connectable when enabled in config and a token is set"
    )


def test_telegram_not_connectable_when_disabled_even_with_token() -> None:
    cfg = GatewayConfig()
    cfg.platforms[Platform.TELEGRAM] = PlatformConfig(enabled=False, token="123456:ABC")

    assert Platform.TELEGRAM not in cfg.get_connected_platforms(), (
        "telegram must stay disconnected when explicitly disabled in config, "
        "even when a token is present"
    )
