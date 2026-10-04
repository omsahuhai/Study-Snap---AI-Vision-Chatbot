"""
Telegram Service for StudySnap.
Handles Telegram Bot configuration and delivers study summaries.
"""

import os
import re
from typing import Optional, Tuple
from pathlib import Path
import requests

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
PLACEHOLDER_TOKEN = "your-telegram-bot-token-here"
PLACEHOLDER_CHAT_ID = "your-telegram-chat-id-here"


def get_telegram_config() -> Tuple[Optional[str], Optional[str]]:
    """
    Resolves Telegram bot token and chat ID from secrets or environment variables.
    Returns (bot_token, chat_id) or (None, None) if not configured.
    """
    token = None
    chat_id = None

    # 1. Check Streamlit secrets
    secrets_path = Path(".streamlit/secrets.toml")
    if secrets_path.exists():
        try:
            import tomllib
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
                raw_token = secrets.get("TELEGRAM_BOT_TOKEN")
                raw_chat_id = secrets.get("TELEGRAM_CHAT_ID")
                if raw_token and str(raw_token).strip() != PLACEHOLDER_TOKEN:
                    token = str(raw_token).strip()
                if raw_chat_id and str(raw_chat_id).strip() != PLACEHOLDER_CHAT_ID:
                    chat_id = str(raw_chat_id).strip()
        except Exception:
            pass

    # 2. Check environment variables as fallback
    if not token:
        env_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if env_token and env_token.strip() != PLACEHOLDER_TOKEN:
            token = env_token.strip()

    if not chat_id:
        env_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if env_chat_id and env_chat_id.strip() != PLACEHOLDER_CHAT_ID:
            chat_id = env_chat_id.strip()

    return token, chat_id


def is_telegram_configured() -> bool:
    """Returns True if valid Telegram credentials are configured."""
    token, chat_id = get_telegram_config()
    return bool(token and chat_id)


def sanitize_telegram_error(error_message: str, token: Optional[str] = None) -> str:
    """Redacts any bot token instances from error messages or URLs."""
    sanitized = error_message
    if token:
        sanitized = sanitized.replace(token, "[REDACTED_TOKEN]")
    # Catch any generic bot token patterns: bot<digits>:<alphanumeric>
    sanitized = re.sub(r'bot\d+:[A-Za-z0-9_-]+', 'bot[REDACTED_TOKEN]', sanitized)
    return sanitized


def send_telegram_message(
    message: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sends a text message to Telegram via the official Bot API.
    Returns (success: bool, info_or_error: str).
    """
    if not message or not message.strip():
        return False, "Cannot send an empty message to Telegram."

    # Resolve credentials if not provided
    token = bot_token
    target_chat = chat_id
    if not token or not target_chat:
        resolved_token, resolved_chat = get_telegram_config()
        token = token or resolved_token
        target_chat = target_chat or resolved_chat

    if not token or not target_chat:
        return False, "Telegram credentials are not configured. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .streamlit/secrets.toml."

    # Telegram message length limit is 4096 characters
    text_to_send = message.strip()
    if len(text_to_send) > 4000:
        text_to_send = text_to_send[:3950] + "\n\n...[Summary truncated for Telegram]"

    url = TELEGRAM_API_URL.format(token=token)

    try:
        # First try sending with Markdown formatting
        response = requests.post(
            url,
            json={
                "chat_id": target_chat,
                "text": text_to_send,
                "parse_mode": "Markdown"
            },
            timeout=10
        )

        if response.status_code == 200:
            return True, "Study summary delivered to Telegram successfully!"

        # If Markdown entity parsing failed (HTTP 400), retry as clean plain text
        if response.status_code == 400 and "can't parse entities" in response.text.lower():
            retry_resp = requests.post(
                url,
                json={
                    "chat_id": target_chat,
                    "text": text_to_send
                },
                timeout=10
            )
            if retry_resp.status_code == 200:
                return True, "Study summary delivered to Telegram successfully!"
            return False, sanitize_telegram_error(f"Telegram API error ({retry_resp.status_code}): {retry_resp.text}", token)

        return False, sanitize_telegram_error(f"Telegram API error ({response.status_code}): {response.text}", token)

    except requests.exceptions.RequestException as e:
        clean_err = sanitize_telegram_error(str(e), token)
        return False, f"Network error contacting Telegram: {clean_err}"
    except Exception as e:
        clean_err = sanitize_telegram_error(str(e), token)
        return False, f"Unexpected error: {clean_err}"
