from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "ContentForge AI"
    API_V1_STR: str = "/api/v1"

    # Security & Auth
    SECRET_KEY: str = "insecure-development-secret-key-at-least-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"

    # Rate Limiting (SlowAPI)
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_UPLOAD: str = "10/hour"
    RATE_LIMIT_GENERATE: str = "20/hour"
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # Data Retention & Maintenance
    DATA_RETENTION_DAYS: int = 90

    # Monitoring & Observability (Part 4)
    PROMETHEUS_ENABLED: bool = True
    SENTRY_DSN: str = ""

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "contentforge"
    POSTGRES_PASSWORD: str = "contentforge_secret_pw"
    POSTGRES_DB: str = "contentforge_db"
    DATABASE_URL: str = ""

    # Redis & Celery
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "contentforge-documents"
    MINIO_SECURE: bool = False

    # ClamAV
    CLAMAV_ENABLED: bool = True
    CLAMAV_HOST: str = "localhost"
    CLAMAV_PORT: int = 3310
    CLAMAV_TIMEOUT: int = 30

    # Ingestion & Chunking
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
    CHUNK_SIZE_TARGET: int = 600  # Words
    CHUNK_OVERLAP: int = 50       # Words

    # LLM & Ollama (Part 2)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"
    OLLAMA_TIMEOUT: int = 120
    EMBEDDING_MODEL: str = "bge-m3:latest"
    RAG_CONTEXT_TOKEN_LIMIT: int = 6000

    # Blockchain Trust Layer & Verification (Part 5)
    FRONTEND_URL: str = "http://localhost:3000"
    ENABLE_PUBLIC_ANCHOR: bool = False
    POLYGON_AMOY_RPC_URL: str = "https://rpc-amoy.polygon.technology"
    POLYGON_AMOY_CHAIN_ID: int = 80002
    PUBLIC_ANCHOR_PRIVATE_KEY: str = ""
    PUBLIC_ANCHOR_CONTRACT_ADDRESS: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return ["*"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str, info) -> str:
        if isinstance(v, str) and v.strip():
            return v
        data = info.data
        user = data.get("POSTGRES_USER", "contentforge")
        pw = data.get("POSTGRES_PASSWORD", "contentforge_secret_pw")
        server = data.get("POSTGRES_SERVER", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "contentforge_db")
        return f"postgresql://{user}:{pw}@{server}:{port}/{db}"


settings = Settings()
