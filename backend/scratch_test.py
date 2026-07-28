import sys
import os
import asyncio
import time

# Set up path so app imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.pipeline import run_pipeline
from pool.article_pool_fetcher import ensure_fresh_pool_on_startup

async def main():
    print("Running pipeline manually for validation report...")
    start_time = time.time()
    
    # We will trigger the pipeline which fetches from APIs, then DuckDuckGo if needed.
    payload = await run_pipeline(keyword=None, force_refresh=True, trigger_type="Manual Validation")
    
    end_time = time.time()
    
    print(f"Pipeline Execution Time: {end_time - start_time:.2f} seconds")
    
    articles = payload.get("articles", [])
    print(f"Total articles in payload: {len(articles)}")
    
    sources_count = {}
    for a in articles:
        src = a.get("source", "Unknown")
        sources_count[src] = sources_count.get(src, 0) + 1
        
    print("Articles by source:")
    for k, v in sources_count.items():
        print(f"  {k}: {v}")
        
    # Let's also check the pool fetching directly to see the exact numbers from the fetchers.
    from pool.article_pool_fetcher import fetch_articles_for_pool
    print("\nRunning fetch_articles_for_pool to inspect DuckDuckGo fallback directly...")
    pool_start = time.time()
    pool_articles = await fetch_articles_for_pool(force_refresh=True)
    pool_end = time.time()
    
    print(f"fetch_articles_for_pool execution time: {pool_end - pool_start:.2f} seconds")
    print(f"Total pool articles generated: {len(pool_articles)}")
    
    pool_sources = {}
    for a in pool_articles:
        src = a.get("source", "Unknown")
        pool_sources[src] = pool_sources.get(src, 0) + 1
        
    print("Pool Articles by source:")
    for k, v in pool_sources.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(main())
