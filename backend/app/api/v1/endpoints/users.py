from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, WalletUpdateRequest

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/streak/freeze", response_model=UserResponse)
async def use_streak_freeze(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.streak_freeze_count <= 0:
        raise HTTPException(status_code=400, detail="No streak freezes remaining")

    current_user.streak_freeze_count -= 1
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/wallet", response_model=UserResponse)
async def update_wallet(
    payload: WalletUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Links a Solana wallet to the account.

    NOTE: this records an address the client claims to own. It is NOT proof of
    ownership - that needs a signed message challenge. Nothing of value may be
    released on the strength of this field alone.
    """
    address = payload.wallet_address.strip()

    if current_user.solana_wallet == address:
        return UserResponse.model_validate(current_user)

    # solana_wallet is UNIQUE. Check first for a clean 409, and still catch
    # IntegrityError for the race between the check and the commit.
    taken = await db.execute(
        select(User.id).where(
            User.solana_wallet == address, User.id != current_user.id
        )
    )
    if taken.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This wallet is already linked to another account",
        )

    current_user.solana_wallet = address
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This wallet is already linked to another account",
        )

    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.delete("/wallet", response_model=UserResponse)
async def unlink_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlinks the wallet, freeing the address for another account."""
    current_user.solana_wallet = None
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)
