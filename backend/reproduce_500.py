import asyncio
from app.main import get_news_from_cache_or_default, get_news
from app.services.dataset_manager import dataset_manager
from app.models import Article

async def test_get_news():
    dataset = dataset_manager.get_active_dataset()
    dataset["articles"] = [
        Article(
            title="Test",
            url="https://test.com",
            source="Test",
            published_at="Now",
            summary="Test summary"
        )
    ]
    dataset_manager.replace_active_dataset(dataset)
    print("Injected Pydantic Article into ACTIVE_DATASET.")
    try:
        res = await get_news(keyword="Test")
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_news())
