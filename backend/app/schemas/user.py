import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    username: Optional[str] = Field(None, max_length=64)
    email: Optional[EmailStr] = None
    telegram_id: Optional[str] = None
    solana_wallet: Optional[str] = Field(None, max_length=64)


class UserCreate(BaseModel):
    username: Optional[str] = Field(None, max_length=64)
    email: Optional[EmailStr] = None
    solana_wallet: Optional[str] = Field(None, max_length=64)
    # Minimum length is a floor, not a policy; enforce the rest at the edge.
    password: Optional[str] = Field(None, min_length=12, max_length=128)
    # Signed Telegram payload. telegram_id is never accepted from the client -
    # it is derived from this after the HMAC check.
    telegram_init_data: Optional[str] = None


class UserLogin(BaseModel):
    username_or_email: Optional[str] = Field(None, max_length=255)
    telegram_init_data: Optional[str] = None
    password: Optional[str] = Field(None, max_length=128)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_device_verified: bool
    reputation_score: float
    streak_days: int
    streak_freeze_count: int
    stamina_balance: int
    grln_token_balance: float
    created_at: datetime


# Solana addresses are 32 raw bytes rendered in base58, which lands in the
# 32-44 character range. The alphabet deliberately omits 0, O, I and l.
_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
SOLANA_ADDRESS_RE = re.compile(rf"^[{_BASE58_ALPHABET}]{{32,44}}$")


class WalletUpdateRequest(BaseModel):
    wallet_address: str = Field(
        ...,
        min_length=32,
        max_length=44,
        description="Solana base58 wallet address",
    )

    @field_validator("wallet_address")
    @classmethod
    def _validate_base58(cls, v: str) -> str:
        # Length alone let through 40 exclamation marks, and strings using the
        # four characters base58 excludes. Decode to be sure it is 32 bytes.
        v = v.strip()
        if not SOLANA_ADDRESS_RE.match(v):
            raise ValueError("Not a valid base58-encoded Solana address")

        number = 0
        for char in v:
            number = number * 58 + _BASE58_ALPHABET.index(char)
        decoded_len = (number.bit_length() + 7) // 8 + (len(v) - len(v.lstrip("1")))
        if decoded_len != 32:
            raise ValueError("Solana address must decode to exactly 32 bytes")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
