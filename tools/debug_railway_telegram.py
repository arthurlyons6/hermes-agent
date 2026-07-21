#!/usr/bin/env python3
"""Railway Telegram probe: validate inbound/outbound via bot API only."""
import json
import os
import urllib.parse
import urllib.request


def tg(method: str, payload: dict | None = None) -> dict:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload else "GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if not body.get("ok"):
        raise RuntimeError(body)
    return body["result"]


def main() -> int:
    me = tg("getMe")
    print("bot=", json.dumps(me, ensure_ascii=False))

    updates = tg("getUpdates", {"timeout": 2, "limit": 20, "offset": -20})
    print("recent_updates=", json.dumps(updates, ensure_ascii=False))

    target_user_id = os.environ.get("TELEGRAM_ALLOWED_USERS", "").split(",")[0].strip()
    last_text = None
    chat_id = None
    for upd in updates:
        msg = ((upd.get("message") or upd.get("channel_post")) or {})
        text = msg.get("text")
        from_user = msg.get("from") or {}
        if text and str(from_user.get("id")) == target_user_id:
            last_text = text
            chat_id = msg.get("chat", {}).get("id") or from_user.get("id")
            break

    print("target_user_id=", target_user_id)
    print("last_text=", last_text)
    print("chat_id=", chat_id)

    if not chat_id:
        return 0

    probe_text = "Hermes Railway probe: Telegram send path is live."
    sent = tg("sendMessage", {"chat_id": chat_id, "text": probe_text})
    print("sent_message=", json.dumps(sent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
