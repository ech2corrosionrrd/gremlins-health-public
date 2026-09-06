import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_password_hash,
    needs_rehash,
    verify_password,
)
from app.core.telegram_auth import InitDataError, verify_init_data
from app.models.gremlin import Gremlin
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# One message for every credential failure so the endpoint cannot be used to
# enumerate which emails or Telegram accounts exist.
_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _create_starter_gremlin(db: AsyncSession, user: User) -> None:
    db.add(Gremlin(owner_id=user.id, name="Gremly", level=1, xp=0, hp=100, mood=100, hunger=0))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # A classic account needs a password; a Telegram account is proven by
    # initData at login time instead.
    if not user_in.telegram_init_data and not user_in.password:
        raise HTTPException(
            status_code=400,
            detail="A password is required unless registering via Telegram",
        )

    telegram_id = None
    if user_in.telegram_init_data:
        try:
            tg_user = verify_init_data(user_in.telegram_init_data)
        except InitDataError as exc:
            logger.warning("Rejected Telegram registration: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram authentication data",
            ) from exc
        telegram_id = tg_user.id

    if user_in.email:
        res = await db.execute(select(User).where(User.email == user_in.email))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="This account cannot be registered")

    if telegram_id:
        res = await db.execute(select(User).where(User.telegram_id == telegram_id))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="This account cannot be registered")

    db_user = User(
        username=user_in.username or f"hiker_{telegram_id or 'anon'}",
        email=user_in.email,
        telegram_id=telegram_id,
        solana_wallet=user_in.solana_wallet,
        hashed_password=get_password_hash(user_in.password) if user_in.password else None,
        stamina_balance=100,
    )
    db.add(db_user)
    await db.flush()

    await _create_starter_gremlin(db, db_user)
    await db.commit()
    await db.refresh(db_user)

    return Token(
        access_token=create_access_token(db_user.id),
        user=UserResponse.model_validate(db_user),
    )


@router.post("/login", response_model=Token)
async def login_user(login_in: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user: User | None = None

    if login_in.telegram_init_data:
        # The HMAC is the credential. Never parse the id out of the raw string.
        try:
            tg_user = verify_init_data(login_in.telegram_init_data)
        except InitDataError as exc:
            logger.warning("Rejected Telegram login: %s", exc)
            raise _INVALID_CREDENTIALS from exc

        res = await db.execute(select(User).where(User.telegram_id == tg_user.id))
        db_user = res.scalar_one_or_none()

        if db_user is None:
            # First launch from the Mini App: the signature already proves who
            # they are, so provision the account instead of bouncing them.
            db_user = User(
                username=tg_user.username or f"hiker_{tg_user.id}",
                telegram_id=tg_user.id,
                stamina_balance=100,
            )
            db.add(db_user)
            await db.flush()
            await _create_starter_gremlin(db, db_user)
            await db.commit()
            await db.refresh(db_user)

    elif login_in.username_or_email:
        if not login_in.password:
            raise _INVALID_CREDENTIALS

        res = await db.execute(
            select(User).where(
                (User.email == login_in.username_or_email)
                | (User.username == login_in.username_or_email)
            )
        )
        candidate = res.scalar_one_or_none()

        # A row with no password hash is a Telegram-only account: it can never
        # be entered through this branch.
        if (
            candidate is not None
            and candidate.hashed_password
            and verify_password(login_in.password, candidate.hashed_password)
        ):
            db_user = candidate
            if needs_rehash(candidate.hashed_password):
                candidate.hashed_password = get_password_hash(login_in.password)
                await db.commit()
        else:
            # Spend comparable time on a miss so timing does not reveal
            # whether the account exists.
            verify_password(
                login_in.password,
                "pbkdf2_sha256$600000$" + "0" * 32 + "$" + "0" * 64,
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either telegram_init_data or username_or_email + password",
        )

    if not db_user:
        raise _INVALID_CREDENTIALS
    if not bool(db_user.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return Token(
        access_token=create_access_token(db_user.id),
        user=UserResponse.model_validate(db_user),
    )
