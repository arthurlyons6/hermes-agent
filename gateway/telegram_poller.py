"""Telegram polling runtime for Hermes gateway."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

import requests as _requests  # type: ignore[import-not-found]

logger = logging.getLogger("gateway.telegram_poller")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

# Telegram long-poll timeout must be shorter than the HTTP read timeout.
# The HTTP client needs margin for TLS handshake, JSON transfer, and network latency.
TELEGRAM_LONG_POLL_SECONDS = 25
HTTP_CONNECT_TIMEOUT_SECONDS = 10
HTTP_READ_TIMEOUT_SECONDS = TELEGRAM_LONG_POLL_SECONDS + 10  # 35s total


def _post(method: str, token: str, json_payload: Dict[str, Any] = None) -> Dict[str, Any]:
    url = TELEGRAM_API.format(token=token, method=method)
    resp = _requests.post(
        url,
        json=json_payload or {},
        timeout=(HTTP_CONNECT_TIMEOUT_SECONDS, HTTP_READ_TIMEOUT_SECONDS),  # nosec B113
    )
    resp.raise_for_status()
    return resp.json()


def get_me(token: str) -> Optional[Dict[str, Any]]:
    result = _post("getMe", token)
    return result.get("result")


def get_updates(token: str, offset: int, poll_timeout: int = TELEGRAM_LONG_POLL_SECONDS) -> tuple[list[Dict[str, Any]], int]:
    result = _post(
        "getUpdates",
        token,
        {
            "offset": offset,
            "timeout": poll_timeout,
            "allowed_updates": ["message"],
        },
    )
    updates = result.get("result", [])
    new_offset = offset
    if updates:
        new_offset = updates[-1]["update_id"] + 1
    return updates, new_offset


def send_message(token: str, chat_id: str, text: str) -> Dict[str, Any]:
    return _post("sendMessage", token, {"chat_id": chat_id, "text": text, "disable_web_page_preview": True})


def authorize(update: Dict[str, Any], allowed_users: str) -> bool:
    if not allowed_users:
        return True
    allowed = {str(u.strip()) for u in allowed_users.split(",") if u.strip()}
    user_id = str(update.get("message", {}).get("from", {}).get("id", ""))
    return user_id in allowed


async def poll(token: str, allowed_users: str = "", poll_timeout: int = TELEGRAM_LONG_POLL_SECONDS) -> None:
    offset = 0
    me = get_me(token)
    if me:
        logger.info("Telegram bot authenticated: @%s", me.get("username"))
    else:
        logger.warning("Telegram getMe failed, polling may not work")

    while True:
        try:
            updates, offset = get_updates(token, offset, poll_timeout)
            for update in updates:
                if not authorize(update, allowed_users):
                    logger.warning(
                        "Unauthorized update from user %s",
                        update.get("message", {}).get("from", {}).get("id"),
                    )
                    continue
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = str(message.get("chat", {}).get("id", ""))
                if not text or not chat_id:
                    continue
                logger.info("Inbound Telegram update: chat=%s text=%s", chat_id, text[:80])
                response = _handle_command(text)
                if response:
                    send_message(token, chat_id, response)
                    logger.info("Outbound Telegram message sent to chat=%s", chat_id)
        except _requests.exceptions.ReadTimeout:
            logger.debug("Telegram long poll completed without an update")
            continue
        except _requests.exceptions.ConnectionError as e:
            logger.warning("Telegram connection error: %s — retrying in 30s", e)
            await asyncio.sleep(30)
        except _requests.exceptions.Timeout as e:
            logger.warning("Telegram request timed out: %s — retrying in 10s", e)
            await asyncio.sleep(10)
        except _requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 0)
            if status == 401:
                logger.error("Telegram authentication failed (HTTP 401) — check bot token")
                await asyncio.sleep(60)
            elif status == 409:
                logger.warning("Telegram conflict (HTTP 409) — another getUpdates session active; retrying in 5s")
                await asyncio.sleep(5)
            elif status == 429:
                retry_after = int(e.response.headers.get("Retry-After", 30))
                logger.warning("Telegram rate limited (HTTP 429) — backing off %ss", retry_after)
                await asyncio.sleep(retry_after)
            elif status >= 500:
                logger.warning("Telegram server error (HTTP %d) — retrying in 30s", status)
                await asyncio.sleep(30)
            else:
                logger.warning("Telegram HTTP error (HTTP %d): %s", status, e)
                await asyncio.sleep(10)
        except Exception as e:
            logger.warning("Telegram polling error: %s", e)
            await asyncio.sleep(5)


def _handle_command(command: str) -> str:
    try:
        from platform.automation.telegram_bridge import handle

        return handle(command)
    except Exception as e:
        logger.warning("Telegram handler error: %s", e)
        return f"Error: {e}"