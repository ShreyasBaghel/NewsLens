import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.dataset_manager import dataset_manager

async def test_api():
    print("Initializing test...")
    dataset_manager.load_startup_snapshot()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test 1: GET /health
        response = await ac.get("/health")
        print(f"GET /health: {response.status_code}")
        print(response.json())
        
        # Test 2: GET /api/news
        response = await ac.get("/api/news")
        print(f"GET /api/news: {response.status_code}")
        
if __name__ == "__main__":
    asyncio.run(test_api())
