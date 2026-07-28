import logging
from duckduckgo_search import DDGS
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def fetch_duckduckgo_articles(topic: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches articles from DuckDuckGo using duckduckgo_search.
    Returns a list of articles formatted like the API responses.
    """
    articles = []
    try:
        with DDGS() as ddgs:
            # We use 'news' search for articles
            results = ddgs.news(keywords=topic, max_results=max_results)
            if not results:
                return articles
                
            for res in results:
                # DDGS news returns: title, url, body, date, source
                url = res.get("url")
                if not url:
                    continue
                    
                title = res.get("title", "")
                description = res.get("body", "")
                source = res.get("source", "DuckDuckGo")
                date_str = res.get("date", "")
                
                # Try to parse ISO date from DDG if available
                published_at = datetime.now(timezone.utc).isoformat() + "Z"
                if date_str:
                    try:
                        # Sometimes date is in ISO format, e.g. '2023-11-20T12:00:00+00:00'
                        parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        published_at = parsed_date.isoformat()
                        if not published_at.endswith("Z") and "+00:00" in published_at:
                            published_at = published_at.replace("+00:00", "Z")
                    except Exception:
                        pass

                articles.append({
                    "title": title,
                    "url": url,
                    "description": description,
                    "source": source,
                    "published_at": published_at,
                    "fetched_via": "DuckDuckGo"
                })
    except Exception as e:
        logger.error(f"DuckDuckGo fetch failed for topic '{topic}': {e}")
        
    return articles
