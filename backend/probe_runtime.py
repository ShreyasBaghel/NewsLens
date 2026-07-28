"""
Runtime Evidence Probe — Feed State Verification
Runs entirely within the backend Python environment (no HTTP).
Prints structured evidence for every claim in the previous analysis.
"""
import sys
import copy
import json

sys.path.insert(0, 'd:/News_Dashboard/backend')

SEP = "=" * 70

# ─────────────────────────────────────────────────────────────────────────────
# 0. Bootstrap the app (same as lifespan startup)
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("STEP 0 — Bootstrap: load DB, caches, dataset_manager")
print(SEP)

from app.database import init_db
init_db()

from pool.keyword_extractor import load_keywords_cache
load_keywords_cache()

from app.services.cache import build_in_memory_index, get_global_keyword_counts, migrate_caches
migrate_caches()
build_in_memory_index()

from app.services.dataset_manager import dataset_manager
dataset_manager.load_startup_snapshot()

import app.services.cache as cache_mod

print("Bootstrap complete.\n")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Raw Active Dataset — before any request processing
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 1 — Active Dataset (raw, before prepare_dashboard_response)")
print(SEP)

ds = dataset_manager.get_active_dataset()
raw_articles        = ds.get("articles", [])
raw_pinned          = ds.get("pinned_articles", [])
raw_kw_counts       = ds.get("keyword_counts", {})
raw_keyword_field   = ds.get("keyword", "")

print(f"  ds['articles'].length          = {len(raw_articles)}")
print(f"  ds['pinned_articles'].length   = {len(raw_pinned)}")
print(f"  ds['keyword_counts'] entries   = {len(raw_kw_counts)}")
print(f"  ds['keyword'] field            = {repr(raw_keyword_field)}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 2. overlay_pinned_articles — what happens to pinned/unpinned split
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 2 — overlay_pinned_articles result")
print(SEP)

from app.main import overlay_pinned_articles, prepare_dashboard_response

payload_for_overlay = copy.deepcopy(ds)
after_overlay = overlay_pinned_articles(payload_for_overlay)

print(f"  After overlay articles (unpinned)  = {len(after_overlay['articles'])}")
print(f"  After overlay pinned_articles      = {len(after_overlay['pinned_articles'])}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 3. HOME_FEED_COUNT cap inspection
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 3 — HOME_FEED_COUNT cap (prepare_dashboard_response internals)")
print(SEP)

from app.config import settings

kw_field    = after_overlay.get("keyword", "")
cap_applies = not kw_field or kw_field in ("Default Dashboard", "General Manufacturing & Industry")

print(f"  keyword field for cap check = {repr(kw_field)}")
print(f"  HOME_FEED_COUNT value       = {settings.HOME_FEED_COUNT}")
print(f"  Cap applies                 = {cap_applies}")

if cap_applies:
    n_pinned      = len(after_overlay.get("pinned_articles", []))
    max_unpinned  = max(0, settings.HOME_FEED_COUNT - n_pinned)
    capped_len    = len(after_overlay["articles"][:max_unpinned])
    print(f"  n_pinned (from overlay)     = {n_pinned}")
    print(f"  max_unpinned computed       = {max_unpinned}")
    print(f"  articles after cap          = {capped_len}")
    print(f"  combinedFeed math: {n_pinned} + {capped_len} = {n_pinned + capped_len}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 4. Phase-1 response: GET /api/news?limit=20&offset=0
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 4 — Phase-1 Response: GET /api/news?limit=20&offset=0")
print(SEP)

resp_p1 = prepare_dashboard_response(copy.deepcopy(ds), limit=20, offset=0)
p1_articles = len(resp_p1.get("articles", []))
p1_pinned   = len(resp_p1.get("pinned_articles", []))
p1_kw       = len(resp_p1.get("keyword_counts", {}))

print(f"  articles returned        = {p1_articles}")
print(f"  pinned_articles returned = {p1_pinned}")
print(f"  keyword_counts returned  = {p1_kw}")
print(f"  -> setNormalFeed([{p1_articles}])")
print(f"  -> setPinnedArticles([{p1_pinned}])")
print(f"  -> combinedFeed at Phase-1: {p1_pinned} + {p1_articles} = {p1_pinned + p1_articles}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 5. Phase-2 response: GET /api/news?limit=1000&offset=20
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 5 — Phase-2 Response: GET /api/news?limit=1000&offset=20")
print(SEP)

resp_p2 = prepare_dashboard_response(copy.deepcopy(ds), limit=1000, offset=20)
p2_articles = len(resp_p2.get("articles", []))

print(f"  articles returned        = {p2_articles}")
print(f"  -> setNormalFeed(prev => [...prev, ...{p2_articles}])")

normal_feed_after_load = p1_articles + p2_articles
combined_after_load    = normal_feed_after_load + p1_pinned

print(f"  normalFeed AFTER load    = {p1_articles} + {p2_articles} = {normal_feed_after_load}")
print(f"  pinnedArticles AFTER load= {p1_pinned}")
print(f"  combinedFeed AFTER load  = {combined_after_load}")
print(f"  IS THIS 179?             = {combined_after_load}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 6. Pin/Unpin response: POST /api/news/pin (no limit/offset)
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 6 — Pin/Unpin Response: POST /api/news/pin (limit=None, offset=0)")
print(SEP)

resp_pin = prepare_dashboard_response(copy.deepcopy(ds), limit=None, offset=0)
pin_articles = len(resp_pin.get("articles", []))
pin_pinned   = len(resp_pin.get("pinned_articles", []))
pin_kw       = len(resp_pin.get("keyword_counts", {}))

print(f"  articles returned        = {pin_articles}")
print(f"  pinned_articles returned = {pin_pinned}")
print(f"  keyword_counts returned  = {pin_kw}")
print(f"  -> setNormalFeed([{pin_articles}])  <-- REPLACES previous {normal_feed_after_load}")
print(f"  -> setPinnedArticles([{pin_pinned}])")
combined_after_pin = pin_articles + pin_pinned
print(f"  combinedFeed AFTER pin   = {pin_articles} + {pin_pinned} = {combined_after_pin}")
print(f"  DROP from {combined_after_load} to {combined_after_pin}  = {combined_after_pin == 100}")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 7. Verify keyword counts source
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 7 — Keyword Counts Source Verification")
print(SEP)

total_cached_arts = len(cache_mod._all_cached_articles)
kw_global         = get_global_keyword_counts()

print(f"  _all_cached_articles (from cache.json) = {total_cached_arts}")
print(f"  get_global_keyword_counts() entries    = {len(kw_global)}")
print(f"  active_dataset keyword_counts entries  = {len(raw_kw_counts)}")
print(f"  Phase-1 response keyword_counts        = {p1_kw}")
print(f"  Pin response keyword_counts            = {pin_kw}")

# Are keyword_counts same in API responses?
same_in_p1_and_pin = (resp_p1.get("keyword_counts", {}) == resp_pin.get("keyword_counts", {}))
print(f"  keyword_counts identical in p1 and pin = {same_in_p1_and_pin}")

# handleTogglePin — does it call setKeywordCounts? (static code fact)
print()
print("  handleTogglePin in App.jsx (lines 267-288):")
print("    Calls setNormalFeed?        YES (line 278)")
print("    Calls setPinnedArticles?    YES (line 281)")
print("    Calls setKeywordCounts?     NO  (missing — confirmed by code read)")
print()

# ─────────────────────────────────────────────────────────────────────────────
# 8. State store scan — React Context, Redux, Zustand, SWR, React Query?
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 8 — Alternate State Store Scan (grep results)")
print(SEP)

import subprocess
fe_src = "d:/News_Dashboard/frontend/src"

def grep(pattern, path):
    try:
        result = subprocess.run(
            ["grep", "-r", "--include=*.js", "--include=*.jsx", "--include=*.ts", "--include=*.tsx",
             "-l", pattern, path],
            capture_output=True, text=True
        )
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        return files
    except Exception as e:
        return [f"ERROR: {e}"]

for store in ["createStore", "useSelector", "createSlice", "useReducer",
              "createContext", "useContext", "zustand", "useSWR", "useQuery",
              "QueryClient", "ReactQueryProvider"]:
    hits = grep(store, fe_src)
    print(f"  {store:30s} -> {len(hits)} file(s): {hits}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# 9. Pinned articles JSON — actual count
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 9 — Pinned Articles JSON file (actual runtime count)")
print(SEP)

from app.services.pinned_store import load_pinned_articles, PINNED_JSON_PATH
import os

print(f"  PINNED_JSON_PATH         = {PINNED_JSON_PATH}")
print(f"  File exists              = {os.path.exists(PINNED_JSON_PATH)}")

if os.path.exists(PINNED_JSON_PATH):
    pinned_from_store = load_pinned_articles()
    print(f"  Pinned articles in store = {len(pinned_from_store)}")
    if pinned_from_store:
        sample = pinned_from_store[0]
        print(f"  First pinned article     = {sample.get('title', 'N/A')[:60]}")
        print(f"  First pinned is_pinned   = {sample.get('is_pinned')}")
else:
    print("  [No pinned articles JSON file found]")

print()

# ─────────────────────────────────────────────────────────────────────────────
# 10. Summary Table
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("SECTION 10 — Evidence Summary")
print(SEP)

print(f"""
  Raw active_dataset:
    articles         = {len(raw_articles)}
    pinned_articles  = {len(raw_pinned)}

  After overlay_pinned_articles:
    unpinned articles= {len(after_overlay['articles'])}
    pinned_articles  = {len(after_overlay['pinned_articles'])}

  Phase-1 (limit=20, offset=0):
    articles         = {p1_articles}     [-> normalFeed initial]
    pinned_articles  = {p1_pinned}

  Phase-2 (limit=1000, offset=20):
    articles         = {p2_articles}     [-> appended to normalFeed]

  After full page load:
    normalFeed       = {normal_feed_after_load}
    pinnedArticles   = {p1_pinned}
    combinedFeed     = {combined_after_load}

  Pin/Unpin (limit=None, offset=0):
    articles         = {pin_articles}
    pinned_articles  = {pin_pinned}
    combinedFeed     = {combined_after_pin}   <-- collapse

  Keyword counts:
    cache.json total = {total_cached_arts} articles
    keyword entries  = {len(kw_global)}
    handleTogglePin calls setKeywordCounts? NO
""")
