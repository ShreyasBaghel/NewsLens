import asyncio
import sys
import os

# Add the backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.scheduler import scheduled_pipeline_run

async def main():
    await scheduled_pipeline_run()

if __name__ == "__main__":
    asyncio.run(main())
