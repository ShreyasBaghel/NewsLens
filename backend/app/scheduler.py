import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.pipeline import run_pipeline
from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def scheduled_pipeline_run():
    """Trigger the scheduled pipeline run in the background (every 24 hours)."""
    logger.info("Executing scheduled news dashboard refresh...")
    
    from app.services.metadata import is_cache_fresh
    from app.services.dataset_manager import dataset_manager, snapshot_has_mock_content
    
    active = dataset_manager.get_active_dataset()
    has_articles = bool(active.get("articles"))
    pinned_articles = active.get("pinned_articles", [])
    has_mock = snapshot_has_mock_content(pinned_articles)
    
    if has_mock:
        logger.warning("[STARTUP] Cached snapshot contains mock/placeholder content — forcing refresh.")

    if is_cache_fresh() and has_articles and not has_mock:
        logger.info("[STARTUP] Scheduler refresh skipped")
        logger.info("[STARTUP] Using cached dashboard")
        return
        
    logger.info("[STARTUP] Scheduler triggered refresh")
    logger.info("[STARTUP] Running live scraping")
    try:
        await run_pipeline(keyword=None, force_refresh=True)
        logger.info("Scheduled news dashboard refresh completed successfully.")
    except Exception as e:
        logger.error(f"Scheduled pipeline run failed: {str(e)}")

def start_scheduler():
    """Initialize and start the background scheduler."""
    if not scheduler.running:
        # Schedule the pipeline to run periodically
        scheduler.add_job(
            scheduled_pipeline_run,
            'interval',
            hours=settings.REFRESH_INTERVAL_HOURS,
            id='default_pipeline_job',
            replace_existing=True
        )
        
        from app.services.metadata import is_cache_fresh
        from app.services.dataset_manager import dataset_manager, snapshot_has_mock_content
        
        active = dataset_manager.get_active_dataset()
        has_articles = bool(active.get("articles"))
        pinned_articles = active.get("pinned_articles", [])
        has_mock = snapshot_has_mock_content(pinned_articles)
        
        if not is_cache_fresh() or not has_articles or has_mock:
            if not has_articles:
                logger.warning("[STARTUP] Dashboard snapshot missing or invalid. Starting recovery pipeline...")
            elif has_mock:
                # Logging for this handled in scheduled_pipeline_run itself or we can add it here too
                # Main.py logs it, scheduled_pipeline_run logs it. But start_scheduler schedules it, so let's log it here too if needed, wait, we don't strictly need to log it here if main.py already does, but let's be explicit
                logger.warning("[STARTUP] Cached snapshot contains mock/placeholder content — forcing initial refresh.")
            else:
                logger.info("[STARTUP] Cache is stale. Running initial refresh...")
                
            # Trigger an initial run immediately on startup
            scheduler.add_job(
                scheduled_pipeline_run,
                id='startup_pipeline_job'
            )
        else:
            logger.info("[STARTUP] Dashboard snapshot found and today's refresh completed.")
            logger.info("[STARTUP] Skipping startup refresh.")
            logger.info("[STARTUP] Serving dashboard from MySQL.")
        
        scheduler.start()
        logger.info("Background news pipeline scheduler started.")

def shutdown_scheduler():
    """Shut down the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background news pipeline scheduler shut down.")
