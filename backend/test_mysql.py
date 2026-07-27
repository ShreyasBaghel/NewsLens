from app.database import SessionLocal
from app.database import SeenArticleHash, ArticleKeyword
from sqlalchemy import text

def test_db():
    print("Testing MySQL connection and tables...")
    with SessionLocal() as db:
        # Check tables
        result = db.execute(text("SHOW TABLES"))
        tables = [r[0] for r in result]
        print("Tables:", tables)
        
        # Check rows in SeenArticleHash
        hash_count = db.query(SeenArticleHash).count()
        print("SeenArticleHash row count:", hash_count)
        
        # Check cache table
        result = db.execute(text("SELECT COUNT(*) FROM cached_pipeline_results"))
        cache_count = result.scalar()
        print("cached_pipeline_results row count:", cache_count)

if __name__ == "__main__":
    test_db()
