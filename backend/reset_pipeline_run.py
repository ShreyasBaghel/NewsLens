from datetime import datetime, timedelta, timezone
import sys
import os

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.metadata import set_metadata

past_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat().replace("+00:00", "Z")
set_metadata("last_pipeline_run", past_date)
print(f"Set last_pipeline_run to {past_date}")
