#!/usr/bin/env python3
"""Railway-side Telegram diagnostics."""
import json
import os
import urllib.request


def tg(method, payload=None):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload else "GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    env_keys = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_ALLOWED_USERS",
        "GATEWAY_ALLOW_ALL_USERS",
        "TELEGRAM_GROUP_ALLOWED_USERS",
        "TELEGRAM_GROUP_ALLOWED_CHATS",
        "HERMES_HOME",
        "HERMES_FORCE_TELEGRAM_POLLING",
    ]
    print("env:")
    for key in env_keys:
        print(f"{key}={os.getenv(key, '')}")

    me = tg("getMe")
    print("getMe=", json.dumps(me["result"], ensure_ascii=False))

    webhook = tg("getWebhookInfo")
    print("webhook=", json.dumps(webhook["result"], ensure_ascii=False))

    target_user_id = (os.getenv("TELEGRAM_ALLOWED_USERS") or "").split(",")[0].strip()
    last_text = None
    chat_id = None
    updates = tg("getUpdates", {"timeout": 1, "limit": 20})
    updates = updates.get("result", [])
    print("updates_count=", len(updates))
    for upd in updates:
        msg = upd.get("message") or upd.get("channel_post") or {}
        if not msg:
            continue
        text = msg.get("text")
        from_user = msg.get("from") or {}
        uid = str(from_user.get("id", "")).strip()
        if text and uid == target_user_id:
            last_text = text
            chat_id = msg.get("chat", {}).get("id") or from_user.get("id")
            break

    print("target_user_id=", target_user_id)
    print("last_text=", last_text)
    print("chat_id=", chat_id)

    if not chat_id:
        return 0

    probe_text = "Hermes Railway probe: Telegram send path is live." + "\n\n" + "Send me a message so I can validate Hermes replies end-to-end."
    sent = tg("sendMessage", {"chat_id": chat_id, "text": probe_text})
    print("sent=", json.dumps(sent["result"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
