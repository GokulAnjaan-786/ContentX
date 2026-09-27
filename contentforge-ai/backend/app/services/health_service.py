import logging
import httpx
from typing import Any, Dict
from sqlalchemy import text
from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger("contentforge.health")


def check_database() -> Dict[str, Any]:
    """Verify database connection via a simple query."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "up", "details": "PostgreSQL reachable"}
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return {"status": "down", "error": str(e)}


def check_redis() -> Dict[str, Any]:
    """Verify Redis connection via ping with non-blocking socket check."""
    if settings.ENVIRONMENT == "testing":
        return {"status": "up", "details": "Testing simulated mode"}

    # Fast socket check
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        res = sock.connect_ex((settings.REDIS_HOST, settings.REDIS_PORT))
        sock.close()
        if res != 0:
            return {"status": "degraded", "error": f"Redis port {settings.REDIS_PORT} not listening"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.5, socket_timeout=0.5)
        if r.ping():
            return {"status": "up", "details": "Redis reachable"}
        return {"status": "degraded", "error": "Ping failed"}
    except Exception as e:
        logger.debug(f"Redis health check failed: {e}")
        return {"status": "degraded", "error": str(e)}


def check_storage() -> Dict[str, Any]:
    """Verify MinIO/S3 object storage connectivity."""
    if settings.ENVIRONMENT == "testing":
        return {"status": "up", "details": "Testing mock storage mode"}
    try:
        from app.services.storage_service import storage_service
        is_up = storage_service.ensure_bucket_exists()
        if is_up:
            return {"status": "up", "details": f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' reachable"}
        return {"status": "degraded", "details": "Local storage fallback active"}
    except Exception as e:
        logger.warning(f"MinIO health check failed: {e}")
        return {"status": "degraded", "error": str(e)}


async def check_ollama() -> Dict[str, Any]:
    """Verify Ollama LLM server reachability."""
    if settings.ENVIRONMENT == "testing":
        return {"status": "up", "details": "Testing simulated LLM mode"}
    url = f"{settings.OLLAMA_BASE_URL}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                return {"status": "up", "details": f"Ollama reachable ({len(models)} models available)"}
            return {"status": "degraded", "error": f"Ollama HTTP {resp.status_code}"}
    except Exception as e:
        logger.debug(f"Ollama health check failed: {e}")
        return {"status": "degraded", "error": "Local deterministic AI engine active"}


async def get_system_health() -> Dict[str, Any]:
    """Aggregate health status of all backing dependencies."""
    db_res = check_database()
    redis_res = check_redis()
    minio_res = check_storage()
    ollama_res = await check_ollama()

    # Database is the primary critical dependency
    db_healthy = (db_res["status"] == "up")
    all_healthy = db_healthy and (redis_res["status"] == "up") and (minio_res["status"] == "up") and (ollama_res["status"] == "up")

    overall_status = "healthy" if all_healthy else ("degraded" if db_healthy else "unhealthy")

    return {
        "status": overall_status,
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "dependencies": {
            "database": db_res,
            "redis": redis_res,
            "minio": minio_res,
            "ollama": ollama_res,
        },
    }
