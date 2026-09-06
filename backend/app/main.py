import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.rate_limit import RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def _verify_production_config() -> None:
    """
    Refuses to start a production process with a development-shaped config.
    Failing loudly at boot beats discovering it from an incident.
    """
    problems = []
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is empty - Telegram login is disabled.")
    if settings.DATABASE_URL.startswith("sqlite"):
        problems.append("DATABASE_URL still points at SQLite")
    if any("localhost" in o for o in settings.BACKEND_CORS_ORIGINS):
        problems.append("BACKEND_CORS_ORIGINS still contains localhost")
    if settings.TRUSTED_PROXY_COUNT == 0:
        logger.warning(
            "TRUSTED_PROXY_COUNT=0 behind a proxy makes rate limiting global "
            "rather than per-client. Set it to the number of proxies in front."
        )
    if problems:
        raise RuntimeError(
            "Refusing to start in "
            f"{settings.ENVIRONMENT}: " + "; ".join(problems)
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.is_production:
        _verify_production_config()
        # Schema in production is owned by Alembic ("alembic upgrade head"),
        # not by create_all, which cannot express a migration.
        logger.info("Production mode: skipping create_all; run Alembic migrations.")
    else:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Development mode: schema ensured via create_all.")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    # Interactive docs are a discovery aid for attackers in production.
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)

# Explicit origins only; settings rejects "*" so this can safely send
# credentials. Methods and headers are narrowed to what the client uses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "solana_network": settings.SOLANA_NETWORK,
    }
