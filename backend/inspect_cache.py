import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

cache_path = 'cache.json'
with open(cache_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

has_summary = [e for e in data.values() if e.get('summary')]
has_kws = [e for e in data.values() if e.get('keywords')]
has_url = [e for e in data.values() if e.get('url')]
print(f'cache.json total entries: {len(data)}')
print(f'  with summary: {len(has_summary)}')
print(f'  with keywords: {len(has_kws)}')
print(f'  with url: {len(has_url)}')
print()
print('Sample entries with summaries (top 3):')
for e in has_summary[:3]:
    t = str(e.get('title', ''))[:60].encode('ascii', 'replace').decode()
    u = str(e.get('url', ''))[:60]
    print(f'  title: {t}')
    print(f'  url: {u}')
    print()
