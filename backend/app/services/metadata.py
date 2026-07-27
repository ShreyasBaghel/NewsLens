import logging
from datetime import datetime, timezone
from app.database import SessionLocal, SystemMetadata

logger = logging.getLogger(__name__)

def get_metadata(key: str) -> str | None:
    with SessionLocal() as db:
        entry = db.query(SystemMetadata).filter(SystemMetadata.key == key).first()
        return entry.value if entry else None

def set_metadata(key: str, value: str):
    with SessionLocal() as db:
        entry = db.query(SystemMetadata).filter(SystemMetadata.key == key).first()
        if entry:
            entry.value = value
        else:
            db.add(SystemMetadata(key=key, value=value))
        db.commit()

def is_cache_fresh() -> bool:
    """Checks if the cached pipeline result is still fresh based on REFRESH_INTERVAL_HOURS."""
    from app.config import settings
    last_refresh = get_metadata("last_pipeline_run")
    if not last_refresh:
        return False
    try:
        dt = datetime.fromisoformat(last_refresh)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = (now - dt).total_seconds() / 3600.0
        return age_hours < settings.REFRESH_INTERVAL_HOURS
    except Exception as e:
        logger.warning(f"Error parsing last_pipeline_run metadata: {e}")
        return False

def mark_refreshed():
    """Records the successful completion of a pipeline refresh."""
    now_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    set_metadata("last_pipeline_run", now_str)
    logger.info(f"System metadata updated: last_pipeline_run = {now_str}")
