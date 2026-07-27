import json
import traceback
from sqlalchemy import create_engine, text
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse
import hashlib
import re
from difflib import SequenceMatcher

def normalize_url(url: str) -> str:
    if not url: return ''
    url = url.strip().lower()
    if url.startswith('http://'): url = 'https://' + url[7:]
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        ignored_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'fbclid', 'gclid', 'yclid', 'mc_cid', 'mc_eid', 'sessionid', 'sid', 'jsessionid', 'phpsessid', 'aspsessionid'}
        query_params = parse_qsl(parsed.query)
        filtered_query = [(k, v) for k, v in query_params if k not in ignored_params]
        filtered_query.sort()
        new_query = urlencode(filtered_query)
        return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, new_query, ''))
    except: return url
    
def are_titles_similar(t1, t2):
    s1 = re.sub(r'\W+', '', t1.lower())
    s2 = re.sub(r'\W+', '', t2.lower())
    if not s1 or not s2: return False
    if s1 == s2: return True
    return SequenceMatcher(None, s1, s2).ratio() >= 0.95
    
def get_content_hash(content):
    if not content: return ''
    clean = re.sub(r'\W+', '', content.lower())
    return hashlib.sha256(clean[:400].encode('utf-8')).hexdigest()

engine = create_engine('mysql+pymysql://root:shreyas@localhost:3306/ai_news_dashboard')
try:
    with engine.connect() as conn:
        print('--- 1. Count Total Articles ---')
        # From cached_pipeline_results
        result = conn.execute(text('SELECT keyword, payload FROM cached_pipeline_results'))
        all_articles = []
        default_dashboard = None
        for row in result:
            payload = json.loads(row[1])
            arts = payload.get('articles', []) + payload.get('pinned_articles', [])
            all_articles.extend(arts)
            if row[0] == 'default_dashboard':
                default_dashboard = arts
        
        print(f'Total raw articles inside cached_pipeline_results: {len(all_articles)}')
        
        unique_articles = {}
        for a in all_articles:
            if a.get('url'):
                unique_articles[a['url']] = a
        print(f'Total unique raw articles (by URL): {len(unique_articles)}')
        
        # From article_keywords
        ak_count = conn.execute(text('SELECT COUNT(*) FROM article_keywords')).scalar()
        print(f'Total articles in article_keywords: {ak_count}')

        print('\n--- 2. Count Only Displayable Articles (Overall Pool) ---')
        articles = list(unique_articles.values())
        print(f'Starting with: {len(articles)}')
        
        non_mock = [a for a in articles if '-mock.com' not in a.get('url', '')]
        print(f'After mock filtering: {len(non_mock)}')
        
        valid_urls = [a for a in non_mock if a.get('url') and a.get('url').startswith('http')]
        print(f'After invalid URL filtering: {len(valid_urls)}')
        
        valid_fields = [a for a in valid_urls if a.get('title') and a.get('summary')]
        print(f'After missing fields filtering: {len(valid_fields)}')
        
        seen_canonicals = set()
        seen_norm_urls = set()
        seen_titles = set()
        seen_hashes = set()
        deduped = []
        
        for art in valid_fields:
            url = art.get('url', '')
            canonical = art.get('canonical_url', '')
            title = art.get('title', '')
            content = art.get('scraped_content', '')
            
            norm_url = normalize_url(url)
            norm_canonical = normalize_url(canonical) if canonical else ''
            
            if norm_canonical and norm_canonical in seen_canonicals: continue
            if norm_url in seen_norm_urls: continue
            
            is_dup = False
            for t in seen_titles:
                if are_titles_similar(title, t):
                    is_dup = True
                    break
            if is_dup: continue
            
            h = get_content_hash(content)
            if h and h in seen_hashes: continue
            
            deduped.append(art)
            if norm_canonical: seen_canonicals.add(norm_canonical)
            seen_norm_urls.add(norm_url)
            seen_titles.add(title)
            if h: seen_hashes.add(h)
            
        print(f'After duplicate filtering: {len(deduped)}')
        
        print('\n--- 3 & 4. Default Dashboard Dataset ---')
        print(f'Total in default dashboard dataset: {len(default_dashboard) if default_dashboard else 0}')
        
        if default_dashboard:
            dd_non_mock = [a for a in default_dashboard if '-mock.com' not in a.get('url', '')]
            print(f'Default dashboard non-mock: {len(dd_non_mock)}')
            dd_valid = [a for a in dd_non_mock if a.get('url') and a.get('url').startswith('http')]
            dd_valid = [a for a in dd_valid if a.get('title') and a.get('summary')]
            print(f'Default dashboard after field check: {len(dd_valid)}')
            
            # The backend dataset_manager serves the cached snapshot directly to the frontend.
            # Does the frontend do any deduplication? Let's assume the cached_pipeline_results already has deduplicated data
            # because the pipeline deduplicates before saving. But let's see how many survive a re-deduplication just in case.
            
            dd_seen_canonicals = set()
            dd_seen_norm_urls = set()
            dd_seen_titles = set()
            dd_seen_hashes = set()
            dd_deduped = []
            
            for art in dd_valid:
                url = art.get('url', '')
                canonical = art.get('canonical_url', '')
                title = art.get('title', '')
                content = art.get('scraped_content', '')
                
                norm_url = normalize_url(url)
                norm_canonical = normalize_url(canonical) if canonical else ''
                
                if norm_canonical and norm_canonical in dd_seen_canonicals: continue
                if norm_url in dd_seen_norm_urls: continue
                
                is_dup = False
                for t in dd_seen_titles:
                    if are_titles_similar(title, t):
                        is_dup = True
                        break
                if is_dup: continue
                
                h = get_content_hash(content)
                if h and h in dd_seen_hashes: continue
                
                dd_deduped.append(art)
                if norm_canonical: dd_seen_canonicals.add(norm_canonical)
                dd_seen_norm_urls.add(norm_url)
                dd_seen_titles.add(title)
                if h: dd_seen_hashes.add(h)
                
            print(f'Default dashboard displayable (if re-deduped): {len(dd_deduped)}')
            
        print('\n--- 5. Verify the 49 Articles Issue ---')
        # We know TARGET_ARTICLE_COUNT is 50. Wait, in pipeline.py:
        # The pipeline loop stops when len(summarized_articles) == 50.
        # But wait, what if pinned articles replace some?
        # In main.py:
        # get_news_from_cache_or_default returns the payload.
        # overlay_pinned_articles does:
        # final_unpinned ignores articles if their URL is in pinned.
        
except Exception as e:
    print('Error:', e)
    traceback.print_exc()
