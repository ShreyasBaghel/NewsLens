import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.pipeline import run_pipeline
from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def scheduled_pipeline_run(trigger_type="Scheduled"):
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
        await run_pipeline(keyword=None, force_refresh=True, trigger_type=trigger_type)
        logger.info("Scheduled news dashboard refresh completed successfully.")
    except Exception as e:
        logger.error(f"Scheduled pipeline run failed: {str(e)}")

def start_scheduler():
    """Initialize and start the background scheduler."""
    if not scheduler.running:
        # Schedule the pipeline to run periodically
        job = scheduler.add_job(
            scheduled_pipeline_run,
            'interval',
            hours=settings.REFRESH_INTERVAL_HOURS,
            id='default_pipeline_job',
            replace_existing=True
        )
        
        logger.info("[Startup]")
        logger.info("Loading latest dashboard snapshot...")
        
        from app.services.dataset_manager import dataset_manager
        active = dataset_manager.get_active_dataset()
        has_articles = bool(active.get("articles"))
        
        if has_articles:
            logger.info("Snapshot loaded successfully.")
        else:
            logger.warning("Snapshot loaded, but it is empty.")
            
        logger.info("Automatic scraping: DISABLED")
        logger.info("Serving stored snapshot.")
        
        scheduler.start()
        logger.info("Background news pipeline scheduler started.")

        # Retrieve the job after the scheduler has started so it is fully initialized
        active_job = scheduler.get_job('default_pipeline_job')
        
        # Determine the next run time safely
        next_run = "Unknown"
        if active_job and getattr(active_job, 'next_run_time', None):
            next_run = active_job.next_run_time.strftime("%I:%M %p")
            
        logger.info("Next scheduled APScheduler run:")
        logger.info(f"{next_run}")

def shutdown_scheduler():
    """Shut down the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background news pipeline scheduler shut down.")
