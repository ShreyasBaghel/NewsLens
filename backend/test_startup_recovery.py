import sys
import logging
from app.database import SessionLocal, CachedPipelineResult
from app.services.dataset_manager import dataset_manager
from app.services.cache import save_cached_results, get_global_keyword_counts

logging.basicConfig(level=logging.INFO)

db = SessionLocal()

def clear_cache():
    db.query(CachedPipelineResult).delete()
    db.commit()

def insert_dummy():
    payload = {"keyword": "dummy_keyword", "articles": [{"title": "dummy"}], "pinned_articles": [], "keyword_counts": {}, "last_updated": "2026-07-22T00:00:00Z", "next_update": "2026-07-22T12:00:00Z"}
    save_cached_results("dummy_keyword", payload, session=db)
    db.commit()

def insert_valid():
    payload = {"keyword": "default_dashboard", "articles": [{"title": "valid"}], "pinned_articles": [], "keyword_counts": {}, "last_updated": "2026-07-22T00:00:00Z", "next_update": "2026-07-22T12:00:00Z"}
    save_cached_results("default_dashboard", payload, session=db)
    db.commit()
    
def insert_invalid():
    payload = {"keyword": "default_dashboard", "articles": [], "pinned_articles": [], "keyword_counts": {}, "last_updated": "2026-07-22T00:00:00Z", "next_update": "2026-07-22T12:00:00Z"}
    save_cached_results("default_dashboard", payload, session=db)
    db.commit()

def test_missing():
    print("\n--- Scenario C: Missing Dashboard ---")
    clear_cache()
    dataset_manager.load_startup_snapshot()
    active = dataset_manager.get_active_dataset()
    print("Has articles:", bool(active.get("articles")))

def test_dummy_only():
    print("\n--- Scenario D: Dummy Data Only ---")
    clear_cache()
    insert_dummy()
    dataset_manager.load_startup_snapshot()
    active = dataset_manager.get_active_dataset()
    print("Has articles:", bool(active.get("articles")))
    
def test_valid():
    print("\n--- Scenario B: Valid Dashboard ---")
    clear_cache()
    insert_valid()
    insert_dummy() # mix in dummy data
    dataset_manager.load_startup_snapshot()
    active = dataset_manager.get_active_dataset()
    print("Has articles:", bool(active.get("articles")))

def test_invalid():
    print("\n--- Scenario E: Invalid Dashboard (empty articles) ---")
    clear_cache()
    insert_invalid()
    dataset_manager.load_startup_snapshot()
    active = dataset_manager.get_active_dataset()
    print("Has articles:", bool(active.get("articles")))

if __name__ == "__main__":
    test_missing()
    test_dummy_only()
    test_valid()
    test_invalid()
