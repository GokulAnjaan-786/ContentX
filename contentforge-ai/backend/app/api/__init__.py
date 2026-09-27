from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.generation import router as generation_router

__all__ = ["auth_router", "documents_router", "generation_router"]
