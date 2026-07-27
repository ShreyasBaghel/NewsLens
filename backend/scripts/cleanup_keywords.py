import os
import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.config import settings
from app.database import ArticleKeyword, CachedPipelineResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(settings.sqlalchemy_database_uri)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

FORBIDDEN_KEYWORDS = {"furthermore", "default", "story", "content", "section", "manufacturing"}

def is_bad_keyword(kw):
    return kw.lower().strip() in FORBIDDEN_KEYWORDS

def cleanup_cache_json():
    cache_file = settings.cache_path_resolved
    if not os.path.exists(cache_file):
        logger.info("cache.json not found, skipping.")
        return
        
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    modified = False
    for key, article in data.items():
        url = article.get("url", "")
        keywords = article.get("keywords", [])
        
        if "-mock.com" in url:
            if keywords:
                article["keywords"] = []
                modified = True
                logger.info(f"Cleared keywords for mock article in cache.json: {url}")
        else:
            if keywords:
                new_kws = [k for k in keywords if not is_bad_keyword(k)]
                if len(new_kws) != len(keywords):
                    article["keywords"] = new_kws
                    modified = True
                    logger.info(f"Filtered bad keywords in cache.json for: {url}")
                    
    if modified:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logger.info("Saved updated cache.json")

def cleanup_db():
    with SessionLocal() as db:
        # Clean ArticleKeyword
        rows = db.query(ArticleKeyword).all()
        for row in rows:
            if "-mock.com" in row.url:
                db.delete(row)
                logger.info(f"Deleted ArticleKeyword for mock url: {row.url}")
            else:
                try:
                    kws = json.loads(row.keywords)
                    new_kws = [k for k in kws if not is_bad_keyword(k)]
                    if len(new_kws) != len(kws):
                        row.keywords = json.dumps(new_kws)
                        logger.info(f"Filtered bad keywords in ArticleKeyword for: {row.url}")
                except Exception:
                    pass
                    
        # Clean CachedPipelineResult (which stores a serialized dataset with articles)
        results = db.query(CachedPipelineResult).all()
        for res in results:
            try:
                data = json.loads(res.result_json)
                arts = data.get("articles", [])
                modified = False
                for art in arts:
                    url = art.get("url", "")
                    keywords = art.get("keywords", [])
                    if "-mock.com" in url and keywords:
                        art["keywords"] = []
                        modified = True
                        logger.info(f"Cleared keywords for mock article in CachedPipelineResult: {url}")
                    elif keywords:
                        new_kws = [k for k in keywords if not is_bad_keyword(k)]
                        if len(new_kws) != len(keywords):
                            art["keywords"] = new_kws
                            modified = True
                
                # Also regenerate keyword counts if necessary
                if modified:
                    # Clear keyword counts since we will rely on global aggregation
                    data["keyword_counts"] = {}
                    res.result_json = json.dumps(data)
                    logger.info(f"Updated CachedPipelineResult for keyword: {res.keyword}")
            except Exception:
                pass
                
        db.commit()
        logger.info("Database cleanup committed.")

if __name__ == "__main__":
    logger.info("Starting keyword cleanup...")
    cleanup_cache_json()
    cleanup_db()
    logger.info("Keyword cleanup complete.")
