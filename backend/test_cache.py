import json
with open("d:/News_Dashboard/backend/cache.json") as f:
    data = json.load(f)

# count how many unique articles
print(len(data.keys()))
