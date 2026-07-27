import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'd:/News_Dashboard/backend')
from app.database import SessionLocal, CachedPipelineResult, ArticleKeyword, SystemMetadata
import json
import os

with SessionLocal() as db:
    # ==========================================================================
    # 1. cached_pipeline_results - full inspection
    # ==========================================================================
    results = db.query(CachedPipelineResult).all()
    print("=== cached_pipeline_results ===")
    print(f"Total rows: {len(results)}")
    for r in results:
        try:
            payload = json.loads(r.payload)
            articles = payload.get("articles", [])
            pinned = payload.get("pinned_articles", [])
            keyword = r.keyword
            updated_at = r.updated_at
            print(f"  keyword={repr(keyword)}: {len(articles)} articles, {len(pinned)} pinned | updated_at={updated_at}")
            for a in articles:
                title = (a.get("title") or "(no title)")[:80].encode('ascii', 'replace').decode('ascii')
                url = (a.get("url") or "")[:80]
                print(f"    ARTICLE: {title}")
                print(f"      url: {url}")
        except Exception as e:
            print(f"  ERROR parsing row {repr(r.keyword)}: {e}")

    # ==========================================================================
    # 2. system_metadata
    # ==========================================================================
    print()
    print("=== system_metadata ===")
    metas = db.query(SystemMetadata).all()
    for m in metas:
        print(f"  {m.key} = {m.value}")

    # ==========================================================================
    # 3. article_keywords count and top 10
    # ==========================================================================
    print()
    print("=== article_keywords ===")
    kw_count = db.query(ArticleKeyword).count()
    print(f"  Total keyword rows: {kw_count}")
    kw_rows = db.query(ArticleKeyword).limit(5).all()
    for r in kw_rows:
        kws = r.keywords[:100]
        print(f"  url={r.url[:60]} kws={kws}")

# ==========================================================================
# 4. Inspect cache.json
# ==========================================================================
print()
print("=== cache.json ===")
cache_path = 'd:/News_Dashboard/backend/cache.json'
if os.path.exists(cache_path):
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)
    print(f"  Total entries in cache.json: {len(cache_data)}")
    # Count how many have summaries vs just URLs
    has_summary = sum(1 for e in cache_data.values() if e.get("summary"))
    has_keywords = sum(1 for e in cache_data.values() if e.get("keywords"))
    print(f"  Entries with summaries: {has_summary}")
    print(f"  Entries with keywords: {has_keywords}")
else:
    print("  NOT FOUND")

# ==========================================================================
# 5. Inspect data/article_pool.json
# ==========================================================================
print()
print("=== data/article_pool.json ===")
pool_path = 'd:/News_Dashboard/backend/data/article_pool.json'
if os.path.exists(pool_path):
    with open(pool_path, 'r', encoding='utf-8') as f:
        pool_data = json.load(f)
    articles = pool_data.get("articles", [])
    gen_at = pool_data.get("pool_generated_at", "unknown")
    print(f"  pool_generated_at: {gen_at}")
    print(f"  Total articles in pool: {len(articles)}")
else:
    print("  NOT FOUND")

# ==========================================================================
# 6. Inspect seen_articles.json
# ==========================================================================
print()
print("=== seen_articles.json ===")
seen_path = 'd:/News_Dashboard/backend/seen_articles.json'
if os.path.exists(seen_path):
    with open(seen_path, 'r', encoding='utf-8') as f:
        seen_data = json.load(f)
    print(f"  Total seen article entries: {len(seen_data)}")
else:
    print("  NOT FOUND")

# ==========================================================================
# 7. Simulate what load_startup_snapshot does
# ==========================================================================
print()
print("=== Simulated load_startup_snapshot() flow ===")
from app.services.cache import get_cached_results
cached = get_cached_results("default_dashboard")
if cached and isinstance(cached, dict) and cached.get("articles"):
    print(f"  -> PRIMARY path: Found 'default_dashboard' with {len(cached['articles'])} articles")
else:
    print(f"  -> MISS: 'default_dashboard' not found or has no articles")
    print(f"     raw value = {repr(str(cached)[:200])}")
    print()
    print("  -> FALLBACK path: get_all_mysql_cached_articles()")
    from app.services.cache import get_all_mysql_cached_articles, deduplicate_articles
    all_mysql = get_all_mysql_cached_articles()
    print(f"     Total articles from ALL cached_pipeline_results rows: {len(all_mysql)}")
    unique = deduplicate_articles(all_mysql)
    print(f"     After deduplication: {len(unique)}")
    matching = unique[:50]
    print(f"     Top 50 selected: {len(matching)}")
    for a in matching:
        title = (a.get('title') or '(no title)')[:80].encode('ascii', 'replace').decode('ascii')
        print(f"       - {title}")
    print()
    print("  => CONCLUSION: Startup uses FALLBACK path with this result set")

# ==========================================================================
# 8. CRITICAL: Why is 'default_dashboard' key missing?
# ==========================================================================
print()
print("=== CRITICAL: cached_pipeline_results keys ===")
with SessionLocal() as db:
    results = db.query(CachedPipelineResult).all()
    keys = [r.keyword for r in results]
    print(f"  All keyword keys stored: {keys}")
    print()
    has_default = "default_dashboard" in keys
    print(f"  'default_dashboard' exists: {has_default}")
    has_dummy = "dummy_keyword" in keys
    print(f"  'dummy_keyword' exists: {has_dummy}")
