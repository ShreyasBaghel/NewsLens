import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.dataset_manager import dataset_manager

async def test_api():
    dataset_manager.load_startup_snapshot()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("Test 1: limit=20, offset=0")
        resp1 = await ac.get("/api/news?limit=20&offset=0")
        art1 = resp1.json().get("articles", [])
        pin1 = resp1.json().get("pinned_articles", [])
        print(f"Resp1 unpinned: {len(art1)}, pinned: {len(pin1)}")
        
        print("Test 2: limit=1000, offset=20")
        resp2 = await ac.get("/api/news?limit=1000&offset=20")
        art2 = resp2.json().get("articles", [])
        pin2 = resp2.json().get("pinned_articles", [])
        print(f"Resp2 unpinned: {len(art2)}, pinned: {len(pin2)}")
        
        total = len(art1) + len(art2) + len(pin1)
        print(f"Total unpinned combined: {len(art1) + len(art2)}")
        print(f"Total items in frontend normalFeed: {total}")

if __name__ == "__main__":
    asyncio.run(test_api())
