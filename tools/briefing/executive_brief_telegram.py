from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TelegramDeliveryError(Exception):
    pass


def _get_home_channel() -> str:
    return os.environ.get("HERMES_TELEGRAM_HOME_CHANNEL") or "telegram"


async def _call_send_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from tools.send_message_tool import send_message_tool
    except Exception as exc:
        raise TelegramDeliveryError(f"send_message_tool unavailable: {exc}") from exc
    try:
        result = send_message_tool(payload)
    except Exception as exc:
        raise TelegramDeliveryError(f"send_message runtime error: {exc}") from exc
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result}
    return result if isinstance(result, dict) else {"raw": str(result)}


async def send_text(message: str, target: Optional[str] = None) -> Dict[str, Any]:
    payload = {
        "action": "send",
        "target": target or _get_home_channel(),
        "message": message,
    }
    return await _call_send_message(payload)


async def send_media(path: str, target: Optional[str] = None, caption: str = "") -> Dict[str, Any]:
    payload = {
        "action": "send",
        "target": target or _get_home_channel(),
        "message": f"MEDIA:{path}" + (f"\n{caption}" if caption else ""),
    }
    return await _call_send_message(payload)


async def deliver_brief(brief: Dict[str, Any], target: Optional[str] = None) -> Dict[str, Any]:
    message = _render_brief(brief)
    try:
        if len(message) > 3800:
            first = message[:3800]
            rest = message[3800:]
            a1 = await send_text(first, target=target)
            a2 = await send_text(rest or "(continued)", target=target)
            return {"success": True, "chunks": 2, "results": [a1, a2]}
        result = await send_text(message, target=target)
        return {"success": True, "chunks": 1, "results": [result]}
    except TelegramDeliveryError as exc:
        logger.error("Brief delivery failed: %s", exc)
        return {"success": False, "error": str(exc)}


def _render_brief(brief: Dict[str, Any]) -> str:
    lines = [
        "📋 *Executive Briefing*",
        f"*Generated:* `{brief.get('generated_at')}`",
        "",
    ]

    if brief.get("executive_summary"):
        es = brief["executive_summary"]
        lines += [
            "*Executive Summary*",
            f"{es.get('text','')} [`{es.get('provenance','')}`]",
            "",
        ]

    section_emojis = {
        "calendar": "📅",
        "blackgold_priority_items": "💼",
        "deal_pipeline": "🔁",
        "approval_queue": "✅",
        "banking_and_gci": "🏦",
        "portfolio_alerts": "📊",
        "market_intelligence": "🌐",
        "ai_workforce_status": "🤖",
        "infrastructure_health": "⚙️",
        "failed_jobs": "❌",
        "financial_alerts": "💸",
        "weather": "🌦",
        "scripture": "📖",
        "top_executive_priorities": "🎯",
    }
    for section in brief.get("sections", []):
        block = brief.get(section, {})
        data = block.get("data")
        if data in (None, {}, "") and block.get("provenance") == "unavailable":
            continue
        emoji = section_emojis.get(section, "•")

        lines.append(f"{emoji} *{section.replace('_', ' ').title()}* [`{block.get('provenance','')}`]")
        lines.append(_format_value(data))
        lines.append("")

    lines.append("_Provenance: live | cached | synthetic | pending | unavailable_")
    return "\n".join(lines)


def _format_value(data: Any) -> str:
    if data is None:
        return "_unavailable_"
    if isinstance(data, dict):
        out = []
        for key, value in data.items():
            out.append(f"• {key}: {_format_value(value)}")
        return "\n".join(out)
    if isinstance(data, list):
        return "\n".join([f"- {_format_value(item)}" for item in data])
    return str(data)
