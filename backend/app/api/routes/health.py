"""Health check route."""
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.schemas.common import HealthResponse

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    # Check database
    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Check storage
    storage_ok = Path(settings.STORAGE_PATH).exists()

    status = "ok" if (db_ok and storage_ok) else "degraded"

    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        database=db_ok,
        storage=storage_ok,
        demo_mode=settings.DEMO_MODE,
        timestamp=datetime.utcnow(),
    )
