"""
API server adapter — provides the /health endpoint for Railway startup probes.

Starts an aiohttp server on API_SERVER_PORT (default 3006, matching
Railway PORT=3006) and registers GET /health immediately so that
Railway's startup health probe succeeds while platform adapters
(Telegram, etc.) continue initializing asynchronously.
"""
import asyncio
import logging
import os

logger = logging.getLogger("gateway.api_server")


class APIServerAdapter:
    """aiohttp-based API server with /health endpoint."""

    def __init__(self, config):
        self.port = (
            getattr(config, "port", None)
            or int(os.environ.get("API_SERVER_PORT") or os.environ.get("PORT") or "3006")
        )
        self.host = getattr(config, "host", None) or "0.0.0.0"
        self._app = None
        self._runner = None
        self._site = None
        self.gateway_runner = None

    async def start(self):
        """Start the aiohttp server and register /health."""
        try:
            import aiohttp
            from aiohttp import web
        except ImportError:
            logger.warning("aiohttp not available, API server not started")
            return

        self._app = web.Application()
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_get("/", self._handle_root)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()
        logger.info(
            "API server bound to %s:%d for /health readiness",
            self.host,
            self.port,
        )

    async def _handle_health(self, request):
        """Return HTTP 200 with gateway state while starting up."""
        state = "starting"
        if getattr(self.gateway_runner, "_running", False):
            state = "running"
        return web.json_response(
            {
                "status": "ok",
                "service": "hermes-gateway",
                "gateway": state,
            }
        )

    async def _handle_root(self, request):
        """Root endpoint returns same health response."""
        return await self._handle_health(request)

    async def stop(self):
        """Stop the API server gracefully."""
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        logger.info("API server stopped")

    @property
    def is_running(self) -> bool:
        return self._site is not None and not getattr(self._site, "_stopped", False)