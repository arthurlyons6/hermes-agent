"""Gateway runner - Hermes CLI entry point with early /health binding for Railway."""

try:
    import hermes_bootstrap  # noqa: F401
except ModuleNotFoundError:
    pass

import asyncio
import concurrent.futures
import dataclasses
import logging
import os
from contextlib import suppress
from typing import Any, Dict, Optional

logger = logging.getLogger("gateway.run")

_API_ADAPTER: Optional[Any] = None
_API_STARTED: bool = False


async def _start_early_api_server() -> None:
    global _API_ADAPTER, _API_STARTED
    port = int(os.environ.get("PORT") or os.environ.get("API_SERVER_PORT") or "3006")
    try:
        from gateway.api_server import APIServerAdapter
        _API_ADAPTER = APIServerAdapter(dataclasses.make_dataclass("Config", [("port", int), ("host", str)])(port=port, host="0.0.0.0"))
        _API_ADAPTER.gateway_runner = _get_runner_reference()
        await _API_ADAPTER.start()
        _API_STARTED = True
        logger.info("API server started early for health probe readiness on 0.0.0.0:%d", port)
        print(f"HERMES_API_SERVER_STARTED:0.0.0.0:{port}", flush=True)
    except Exception as e:
        logger.warning("Early API server start failed: %s", e)
        _API_ADAPTER = None
        _API_STARTED = False


def _get_runner_reference() -> Optional[Any]:
    return None


class SimpleNamespace:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


async def start_gateway() -> None:
    await _start_early_api_server()

    # Platform initialization runs in background so /health responds immediately.
    # Railway readiness probes must succeed while Telegram and other adapters
    # continue initializing asynchronously.
    from gateway.telegram_poller import poll as _telegram_poll

    _telegram_task: Optional[asyncio.Task] = None
    _telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if _telegram_token:
        allowed_users = os.environ.get("TELEGRAM_ALLOWED_USERS", "")

        async def _run_telegram() -> None:
            await _telegram_poll(_telegram_token, allowed_users)

        _telegram_task = asyncio.create_task(_run_telegram())
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set, Telegram polling disabled")

    # Keep the process alive so /health remains served by the early-bound API server.
    # Platform adapters (e.g., Telegram) initialize in the background task above.
    logger.info(
        "Gateway running — API server on 0.0.0.0:%s serving /health",
        int(os.environ.get("PORT") or os.environ.get("API_SERVER_PORT") or "3006"),
    )
    while True:
        await asyncio.sleep(60)


class GatewayRunner:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._running = False

    async def start(self) -> None:
        self._running = True
        await start_gateway()

    async def stop(self) -> None:
        self._running = False
        if _API_ADAPTER is not None:
            with suppress(Exception):
                await _API_ADAPTER.stop()


if __name__ == "__main__":
    asyncio.run(start_gateway())