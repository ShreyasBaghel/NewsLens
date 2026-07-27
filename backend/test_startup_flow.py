import asyncio
import logging
from datetime import datetime, timezone, timedelta
from app.config import settings
from app.services.metadata import set_metadata
from app.main import lifespan
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_scenario():
    app = FastAPI()
    
    # Simulate a fresh cache (Scenario A)
    now = datetime.now(timezone.utc)
    set_metadata("last_pipeline_run", now.isoformat().replace("+00:00", "Z"))
    
    logger.info("=== Starting Scenario A: Fresh Cache ===")
    async with lifespan(app):
        logger.info("Scenario A startup complete.")
        
    # Simulate an expired cache (Scenario C)
    stale_time = now - timedelta(hours=settings.REFRESH_INTERVAL_HOURS + 1)
    set_metadata("last_pipeline_run", stale_time.isoformat().replace("+00:00", "Z"))
    
    logger.info("=== Starting Scenario C: Expired Cache ===")
    async with lifespan(app):
        logger.info("Scenario C startup complete.")

if __name__ == "__main__":
    asyncio.run(run_scenario())
