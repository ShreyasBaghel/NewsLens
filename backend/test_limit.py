import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.dataset_manager import dataset_manager

async def test_api():
    dataset_manager.load_startup_snapshot()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("Testing limit=1000, offset=0...")
        resp = await ac.get("/api/news?limit=1000&offset=0")
        articles = resp.json().get("articles", [])
        pinned = resp.json().get("pinned_articles", [])
        print(f"Returned {len(articles)} articles and {len(pinned)} pinned.")
        print(f"Total: {len(articles) + len(pinned)}")
        
        print("Testing out of bounds offset=120...")
        resp = await ac.get("/api/news?limit=10&offset=120")
        articles = resp.json().get("articles", [])
        print(f"Returned {len(articles)} articles.")

if __name__ == "__main__":
    asyncio.run(test_api())
