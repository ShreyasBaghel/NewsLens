import sys
import os
import asyncio
import json

from app.main import prepare_dashboard_response

def test():
    # Simulate a payload with 150 articles and the tricky keyword
    payload = {
        "keyword": "General Manufacturing & Industry",
        "articles": [{"url": f"http://example.com/{i}", "title": f"Article {i}"} for i in range(150)],
        "pinned_articles": [{"url": "http://example.com/pinned", "title": "Pinned 1"}]
    }
    
    # Run the function
    result = prepare_dashboard_response(payload)
    
    print(f"Keyword in payload: {payload['keyword']}")
    print(f"Total articles returned: {len(result['articles'])}")
    print(f"Total pinned returned: {len(result.get('pinned_articles', []))}")
    
if __name__ == "__main__":
    test()
