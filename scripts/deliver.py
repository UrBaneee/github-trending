#!/usr/bin/env python3
"""
GitHub Trending — Delivery
===========================
Sends a digest to the user via their chosen delivery method.
Supports: Telegram bot, Email (via Resend), or stdout (default).

Usage:
    python3 deliver.py --file /path/to/digest.txt
    python3 deliver.py --message "digest text"
    echo "digest text" | python3 deliver.py

Reads delivery config from ~/.github-trending/config.json
and API keys from ~/.github-trending/.env
"""

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

import httpx

USER_DIR = Path.home() / ".github-trending"
CONFIG_PATH = USER_DIR / "config.json"
ENV_PATH = USER_DIR / ".env"


def load_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def get_digest_text(args) -> str:
    if args.message:
        return args.message
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    return sys.stdin.read()


def send_telegram(text: str, bot_token: str, chat_id: str):
    max_len = 4000
    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n", 0, max_len)
        if split_at < max_len * 0.5:
            split_at = max_len
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:]

    for i, chunk in enumerate(chunks):
        resp = httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            err = resp.json()
            if "can't parse" in err.get("description", ""):
                resp = httpx.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": chunk,
                        "disable_web_page_preview": True,
                    },
                    timeout=30,
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"Telegram API error: {resp.json().get('description')}")
            else:
                raise RuntimeError(f"Telegram API error: {err.get('description')}")

        if len(chunks) > 1 and i < len(chunks) - 1:
            time.sleep(0.5)


def send_email(text: str, api_key: str, to_email: str):
    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": "GitHub Trending Digest <digest@resend.dev>",
            "to": [to_email],
            "subject": f"GitHub Trending Digest — {date.today().strftime('%B %d, %Y')}",
            "text": text,
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        err = resp.json()
        raise RuntimeError(f"Resend API error: {err.get('message') or err}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file")
    parser.add_argument("--message")
    args = parser.parse_args()

    env = load_env()
    config = {}
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text())

    delivery = config.get("delivery", {"method": "stdout"})
    digest_text = get_digest_text(args)

    if not digest_text or not digest_text.strip():
        print(json.dumps({"status": "skipped", "reason": "Empty digest text"}))
        return

    method = delivery.get("method", "stdout")
    try:
        if method == "telegram":
            bot_token = env.get("TELEGRAM_BOT_TOKEN")
            chat_id = delivery.get("chatId")
            if not bot_token:
                raise RuntimeError("TELEGRAM_BOT_TOKEN not found in .env")
            if not chat_id:
                raise RuntimeError("delivery.chatId not found in config.json")
            send_telegram(digest_text, bot_token, chat_id)
            print(json.dumps({"status": "ok", "method": "telegram", "message": "Digest sent to Telegram"}))

        elif method == "email":
            api_key = env.get("RESEND_API_KEY")
            to_email = delivery.get("email")
            if not api_key:
                raise RuntimeError("RESEND_API_KEY not found in .env")
            if not to_email:
                raise RuntimeError("delivery.email not found in config.json")
            send_email(digest_text, api_key, to_email)
            print(json.dumps({"status": "ok", "method": "email", "message": f"Digest sent to {to_email}"}))

        else:
            print(digest_text)

    except Exception as err:
        print(json.dumps({"status": "error", "method": method, "message": str(err)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
