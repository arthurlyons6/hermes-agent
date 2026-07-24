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
from typing import Any, Dict, Optional

logger = logging.getLogger("gateway.run")

_API_ADAPTER: Optional[Any] = None
_API_STARTED: bool = False


def _start_early_api_server() -> None:
    global _API_ADAPTER, _API_STARTED
    port = int(os.environ.get("API_SERVER_PORT") or os.environ.get("PORT") or "3006")
    try:
        from gateway.api_server import APIServerAdapter
        cfg = dataclasses.replace(
            SimpleNamespace(value="api_server", extra=SimpleNamespace(port=port, host="0.0.0.0")),
            port=port, host="0.0.0.0",
        )
        _API_ADAPTER = APIServerAdapter(cfg)
        _API_ADAPTER.gateway_runner = _get_runner_reference()
        _API_ADAPTER.start()
        _API_STARTED = True
        logger.info("API server started early for health probe readiness on 0.0.0.0:%d", port)
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
    _start_early_api_server()
    try:
        from gateway.platform_registry import get_platforms
    except ImportError:
        logger.warning("platform_registry not available, skipping platform init")
        return
    platforms = get_platforms()
    async with concurrent.futures.AsyncExecutor() as executor:
        tasks = []
        for platform in platforms:
            if getattr(platform, "value", None) == "api_server" and _API_STARTED:
                continue
            tasks.append(executor.submit(platform.initialize))
        for task in tasks:
            try:
                await asyncio.wrap_future(task)
            except Exception:
                pass


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