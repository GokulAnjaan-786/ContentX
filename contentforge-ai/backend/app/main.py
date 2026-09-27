import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Ensure base and app paths are recognized
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)
for p in [BASE_DIR, ROOT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.config import settings
from app.core.rate_limit import limiter
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.generation import router as generation_router
from app.api.admin import router as admin_router
from app.api.verification import router as verification_router
from app.services.storage_service import storage_service
from app.core import metrics


logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("contentforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing ContentForge AI platform services...")
    # Attempt to initialize MinIO bucket if storage service is reachable
    try:
        storage_service.ensure_bucket_exists()
    except Exception as e:
        logger.warning(f"Storage initialization non-fatal warning: {e}")
    yield
    logger.info("Shutting down ContentForge AI platform...")


# Sentry Error Tracking Initialization (if DSN provided)
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=1.0 if settings.DEBUG else 0.1,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        )
        logger.info("Sentry error tracking initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize Sentry: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    description="ContentForge AI — Multi-format content transformation platform (Part 4 Production)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Attach SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Database or backend service temporary issue."},
        headers={"Access-Control-Allow-Origin": "*"},
    )

# Prometheus Metrics Instrumentation
if settings.PROMETHEUS_ENABLED:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            excluded_handlers=["/metrics", "/health"],
        )
        instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
        logger.info("Prometheus metrics instrumented at /metrics")
    except Exception as e:
        logger.warning(f"Could not instrument Prometheus metrics: {e}")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """
    Unified system health check verifying DB, Redis, MinIO, and Ollama status.
    Returns 200 for healthy or degraded (non-critical), 503 for unhealthy.
    """
    from app.services.health_service import get_system_health
    report = await get_system_health()
    status_code = status.HTTP_200_OK if report["status"] in ("healthy", "degraded") else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=report)


@app.get("/", tags=["System"])
def root():
    """Root info endpoint."""
    return {
        "message": "Welcome to ContentForge AI API",
        "docs": "/docs",
        "version": "1.0.0",
    }


# Mount routers at both root (/auth, /documents, /generate) and versioned (/api/v1/...)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(generation_router)
app.include_router(admin_router)
app.include_router(verification_router)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(generation_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(verification_router, prefix=settings.API_V1_STR)

