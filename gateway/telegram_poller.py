"""Telegram polling runtime for Hermes gateway."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("gateway.telegram_poller")

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _post(method: str, token: str, json_payload: Dict[str, Any] = None) -> Dict[str, Any]:
    import requests as _requests  # type: ignore[import-not-found]

    url = TELEGRAM_API.format(token=token, method=method)
    resp = _requests.post(url, json=json_payload or {}, timeout=30)  # nosec B113
    resp.raise_for_status()
    return resp.json()


def get_me(token: str) -> Optional[Dict[str, Any]]:
    result = _post("getMe", token)
    return result.get("result")


def get_updates(token: str, offset: int, timeout: int = 30) -> tuple[list[Dict[str, Any]], int]:
    result = _post(
        "getUpdates",
        token,
        {"offset": offset, "timeout": timeout, "allowed_updates": ["message"]},
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


async def poll(token: str, allowed_users: str = "", poll_timeout: int = 30) -> None:
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