import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import engine
from sqlalchemy import text

def update_schema():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE article_keywords ADD COLUMN is_mock BOOLEAN DEFAULT FALSE;"))
            print("Added is_mock column.")
        except Exception as e:
            print(f"Column is_mock might exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE article_keywords ADD COLUMN relevance_score FLOAT DEFAULT 0.0;"))
            print("Added relevance_score column.")
        except Exception as e:
            print(f"Column relevance_score might exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE article_keywords ADD COLUMN published_at VARCHAR(255);"))
            print("Added published_at column.")
        except Exception as e:
            print(f"Column published_at might exist: {e}")
            
        try:
            conn.execute(text("CREATE INDEX ix_article_keywords_rank ON article_keywords (is_mock, relevance_score, published_at);"))
            print("Added index ix_article_keywords_rank.")
        except Exception as e:
            print(f"Index might exist: {e}")

if __name__ == '__main__':
    update_schema()
