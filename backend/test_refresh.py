import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.dataset_manager import dataset_manager

async def test_api():
    dataset_manager.load_startup_snapshot()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("Triggering refresh...")
        resp = await ac.post("/api/news/refresh", json={"keyword": ""}, headers={"X-User-Role": "admin"})
        art = resp.json().get("articles", [])
        pin = resp.json().get("pinned_articles", [])
        print(f"Refresh unpinned: {len(art)}, pinned: {len(pin)}")

if __name__ == "__main__":
    asyncio.run(test_api())
