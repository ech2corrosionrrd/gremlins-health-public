"""
Telegram WebApp initData verification.

The Mini App hands the backend an initData query string. Everything in it is
attacker-controlled until the HMAC is checked against the bot token, so this
module is the only place allowed to turn initData into a trusted user.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qsl

from app.core.config import settings


class InitDataError(Exception):
    """initData was missing, malformed, expired or failed the HMAC check."""


@dataclass(frozen=True)
class TelegramUser:
    id: str
    username: Optional[str]
    first_name: Optional[str]
    language_code: Optional[str]


def _secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def verify_init_data(
    init_data: str,
    bot_token: Optional[str] = None,
    max_age_seconds: Optional[int] = None,
) -> TelegramUser:
    """
    Verifies the HMAC-SHA256 signature and freshness of initData.

    Returns the authenticated Telegram user. Raises InitDataError on any
    failure - callers must never fall back to parsing the string themselves.
    """
    token = bot_token if bot_token is not None else settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise InitDataError("Telegram login is not configured on this server")
    if not init_data:
        raise InitDataError("Missing initData")

    try:
        # keep_blank_values so an empty field still participates in the hash.
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError as exc:
        raise InitDataError("Malformed initData") from exc

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("initData has no hash field")

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    computed = hmac.new(
        _secret_key(token), data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed, received_hash):
        raise InitDataError("initData signature mismatch")

    # A valid but old signature is still replayable, so bound its lifetime.
    max_age = (
        max_age_seconds
        if max_age_seconds is not None
        else settings.TELEGRAM_INIT_DATA_MAX_AGE_SECONDS
    )
    auth_date_raw = pairs.get("auth_date")
    if not auth_date_raw:
        raise InitDataError("initData has no auth_date")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise InitDataError("initData auth_date is not an integer") from exc

    age = time.time() - auth_date
    if age > max_age:
        raise InitDataError(f"initData expired ({int(age)}s old, max {max_age}s)")
    # Small negative skew is normal; a far-future date is not.
    if age < -300:
        raise InitDataError("initData auth_date is in the future")

    user_raw = pairs.get("user")
    if not user_raw:
        raise InitDataError("initData has no user payload")
    try:
        user = json.loads(user_raw)
        user_id = user["id"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise InitDataError("initData user payload is malformed") from exc

    return TelegramUser(
        id=str(user_id),
        username=user.get("username"),
        first_name=user.get("first_name"),
        language_code=user.get("language_code"),
    )
