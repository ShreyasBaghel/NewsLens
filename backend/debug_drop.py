import json
import sys
from sqlalchemy import create_engine, text
sys.path.append('d:/News_Dashboard/backend')
from app.services.cache import is_duplicate_of_any

engine = create_engine('mysql+pymysql://root:shreyas@localhost:3306/ai_news_dashboard')
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT payload FROM cached_pipeline_results WHERE keyword = 'default_dashboard'"))
        row = result.fetchone()
        payload = json.loads(row[0])
        articles = payload.get('articles', [])
        pinned = payload.get('pinned_articles', [])
        
        final_unpinned = []
        seen_unpinned = []
        for a in articles:
            if is_duplicate_of_any(a, pinned):
                print(f"Dropped duplicate of pinned: {a['title']}")
                continue
                
            if is_duplicate_of_any(a, seen_unpinned):
                print(f"Dropped duplicate of unpinned: {a['title']}")
                continue
                
            final_unpinned.append(a)
            seen_unpinned.append(a)
except Exception as e:
    print('Error:', e)
