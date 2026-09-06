from typing import Any, AsyncGenerator, Dict

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs: Dict[str, Any] = {"echo": False, "future": True}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Recycle before typical proxy/idle timeouts and verify liveness so a
    # dropped Postgres connection surfaces as a retry, not a 500.
    _engine_kwargs.update(
        pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=1800
    )

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models (SQLAlchemy 2.0 style)."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Request-scoped session.

    Endpoints commit their own work; this only rolls back on an unhandled
    exception. The previous version committed on the way out, which turned a
    handler that raised after a partial write into a silent partial commit.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
