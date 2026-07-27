import sys
from app.database import SessionLocal, CachedPipelineResult

db = SessionLocal()
try:
    results = db.query(CachedPipelineResult).all()
    for row in results:
        print(f"Row keyword: {row.keyword}")
        if row.keyword == 'dummy_keyword' or 'test' in row.keyword.lower():
            print(f"Deleting test row: {row.keyword}")
            db.delete(row)
    db.commit()
    print("Cleanup done.")
except Exception as e:
    print(e)
finally:
    db.close()
