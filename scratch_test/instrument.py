import os
import re

def main():
    frontend_dir = r"d:\News_Dashboard\frontend\src"
    backend_dir = r"d:\News_Dashboard\backend\app"
    
    # 1. Modify newsApi.js
    news_api_path = os.path.join(frontend_dir, "api", "newsApi.js")
    with open(news_api_path, "r", encoding="utf-8") as f:
        news_api_code = f.read()

    # Add source to fetchDashboardData signature
    news_api_code = news_api_code.replace(
        "export async function fetchDashboardData(keyword = '', limit = null, offset = null) {",
        "export async function fetchDashboardData(keyword = '', limit = null, offset = null, source = 'unknown') {"
    )
    news_api_code = news_api_code.replace(
        "console.log(`[API] Request #${reqId} Start | time: ${startTime} | limit=${limit} | offset=${offset} | keyword=${keyword}`);",
        "console.log(`[API] Request #${reqId} Start | time: ${startTime} | limit=${limit} | offset=${offset} | keyword=${keyword} | source=${source}`);\n  if (window.DEBUG_FEED_TRACE) {\n    const elapsed = window.performance ? window.performance.now().toFixed(3) : 0;\n    console.log(`${elapsed} Request #${reqId} (source: ${source}) started | limit=${limit} | offset=${offset} | keyword=${keyword}`);\n  }"
    )
    news_api_code = news_api_code.replace(
        "console.log(`[API] Request #${reqId} Finish | time: ${endTime} | duration: ${endTime - startTime}ms\\n      Returned ${count} articles\\n      First ID: ${firstId}\\n      Last ID: ${lastId}`);",
        "console.log(`[API] Request #${reqId} Finish | time: ${endTime} | duration: ${endTime - startTime}ms\\n      Returned ${count} articles\\n      First ID: ${firstId}\\n      Last ID: ${lastId}`);\n  if (window.DEBUG_FEED_TRACE) {\n    const elapsed = window.performance ? window.performance.now().toFixed(3) : 0;\n    console.log(`${elapsed} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles. First 5 IDs: ${articles.slice(0, 5).map(a => a.id || a.url).join(', ')}. Last 5 IDs: ${articles.slice(-5).map(a => a.id || a.url).join(', ')}`);\n  }"
    )
    
    # pinArticle and unpinArticle
    news_api_code = news_api_code.replace(
        "export async function pinArticle(article, keyword = '') {",
        "export async function pinArticle(article, keyword = '') {\n  const reqId = ++requestCounter;\n  if (window.DEBUG_FEED_TRACE) console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} (Pin) started`);\n  const startTime = Date.now();"
    )
    news_api_code = news_api_code.replace(
        "return await response.json();",
        "const data = await response.json();\n    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {\n      const endTime = Date.now();\n      const count = data.articles ? data.articles.length : 0;\n      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;\n      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;\n      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';\n      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';\n      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);\n    }\n    return data;"
    )
    
    news_api_code = news_api_code.replace(
        "export async function unpinArticle(url, keyword = '') {",
        "export async function unpinArticle(url, keyword = '') {\n  const reqId = ++requestCounter;\n  if (window.DEBUG_FEED_TRACE) console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} (Unpin) started`);\n  const startTime = Date.now();"
    )

    with open(news_api_path, "w", encoding="utf-8") as f:
        f.write(news_api_code)


    # 2. Modify App.jsx
    app_path = os.path.join(frontend_dir, "App.jsx")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # Add DEBUG_FEED_TRACE at top
    debug_code = """
window.DEBUG_FEED_TRACE = true;
const START_TIME = Date.now();
window.logEvent = (message, details = '') => {
  if (!window.DEBUG_FEED_TRACE) return;
  const elapsed = (window.performance ? window.performance.now() : Date.now() - START_TIME).toFixed(3);
  console.log(`${elapsed} ${message}`);
  if (details) console.log(details);
};
if (window.DEBUG_FEED_TRACE) window.logEvent('Page refresh');

// Timer override
const originalSetTimeout = window.setTimeout;
const originalClearTimeout = window.clearTimeout;
let timerIdCounter = 0;
window.setTimeout = function(callback, delay, ...args) {
  const tId = ++timerIdCounter;
  const err = new Error();
  const creator = err.stack ? err.stack.split('\\n')[2] : 'unknown';
  if (window.DEBUG_FEED_TRACE) window.logEvent(`Timer created: ID ${tId} | delay: ${delay}ms | creator: ${creator.trim()}`);
  
  return originalSetTimeout((...cbArgs) => {
    if (window.DEBUG_FEED_TRACE) window.logEvent(`Timer fired: ID ${tId} | delay: ${delay}ms`);
    callback(...cbArgs);
  }, delay, ...args);
};
window.clearTimeout = function(id) {
  if (window.DEBUG_FEED_TRACE) window.logEvent(`Timer cleared: ID ${id}`);
  return originalClearTimeout(id);
};
"""
    app_code = app_code.replace("const LoadingSkeleton = () => (", debug_code + "\nconst LoadingSkeleton = () => (")

    # Instrument state updates
    state_instrument_code = """
      let updateType = 'replacement';
      if (nextValue.length > prev.length && typeof newValueOrUpdater === 'function') {
        updateType = 'append';
      } else if (nextValue.length !== prev.length) {
        updateType = 'replacement';
      } else {
        updateType = 'merge';
      }
      
      if (window.DEBUG_FEED_TRACE) {
        let details = `[STATE] setNormalFeed | Previous = ${prev.length} | New = ${nextValue.length} | Type = ${updateType}`;
        if (updateType === 'append') {
          const prevIds = new Set(prev.map(a => a.id || a.url));
          const appended = nextValue.slice(prev.length);
          const dups = appended.filter(a => prevIds.has(a.id || a.url));
          details += `\\nAppended: ${appended.length} | Duplicates: ${dups.length} | New: ${appended.length - dups.length}`;
        }
        window.logEvent(`normalFeed = ${nextValue.length} (${updateType})`, details);
        
        // Check duplicates in entire new feed
        const allIds = nextValue.map(a => a.id || a.url);
        const uniqueIds = new Set(allIds);
        if (allIds.length !== uniqueIds.size) {
           const counts = {};
           allIds.forEach(id => counts[id] = (counts[id] || 0) + 1);
           const dups = Object.entries(counts).filter(([id, c]) => c > 1);
           let dupStr = `Duplicate article detected\\n`;
           dups.forEach(([id, c]) => {
             dupStr += `URL: ${id}\\nAppears ${c} times\\n`;
           });
           window.logEvent(`DUPLICATES FOUND`, dupStr);
        }
      }
      
      console.log(`[STATE] setNormalFeed | Previous = ${prev.length} | New = ${nextValue.length} | Type = ${updateType}`);
"""
    app_code = app_code.replace(
        """      let updateType = 'replacement';
      if (nextValue.length > prev.length && typeof newValueOrUpdater === 'function') {
        updateType = 'append';
      } else if (nextValue.length !== prev.length) {
        updateType = 'replacement';
      }
      
      console.log(`[STATE] setNormalFeed | Previous = ${prev.length} | New = ${nextValue.length} | Type = ${updateType}`);""",
        state_instrument_code
    )

    # loadInitialData instrumentation
    load_inst_replacement = """    if (window.DEBUG_FEED_TRACE) {
      window.logEvent(`loadInitialData #${invNum}`, `[LOAD #${invNum}]\\nsource = ${reason}\\ntime = ${Date.now()}\\nstack = ${stack}\\nnormalFeed = ${normalFeed.length}\\npinned = ${pinnedArticles.length}\\nsearchResults = ${searchResults.length}\\nrender count = ${renderCountRef.current}`);
    }"""
    app_code = app_code.replace(
        "console.log(`[LOAD] loadInitialData #${invNum}",
        load_inst_replacement + "\n    console.log(`[LOAD] loadInitialData #${invNum}"
    )

    # loadInitialData source tracking
    app_code = app_code.replace("fetchDashboardData('', 20, 0)", "fetchDashboardData('', 20, 0, 'initial load - ' + reason)")
    app_code = app_code.replace("fetchDashboardData('', 1000, 20)", "fetchDashboardData('', 1000, 20, 'background load')")

    # React lifecycle
    app_code = app_code.replace("renderCountRef.current += 1;", "renderCountRef.current += 1;\n  if (window.DEBUG_FEED_TRACE) window.logEvent(`Component render #${renderCountRef.current}`);")
    
    app_code = app_code.replace(
        "useEffect(() => {\n    document.body.className = `${theme}-theme`;",
        "useEffect(() => {\n    if (window.DEBUG_FEED_TRACE) window.logEvent(`Component mounted`);\n    return () => { if (window.DEBUG_FEED_TRACE) window.logEvent(`Component unmounted`); };\n  }, []);\n\n  useEffect(() => {\n    document.body.className = `${theme}-theme`;"
    )

    app_code = app_code.replace(
        "console.log(`[EFFECT] useEffect(userRole) triggered | userRole=${userRole}`);",
        "console.log(`[EFFECT] useEffect(userRole) triggered | userRole=${userRole}`);\n    if (window.DEBUG_FEED_TRACE) window.logEvent(`useEffect(userRole) executed`);"
    )
    app_code = app_code.replace(
        "console.log(`[EFFECT] useEffect(userRole) cleanup executed | userRole=${userRole}`);",
        "console.log(`[EFFECT] useEffect(userRole) cleanup executed | userRole=${userRole}`);\n      if (window.DEBUG_FEED_TRACE) window.logEvent(`useEffect(userRole) cleanup executed`);"
    )

    # Pin/Unpin logging
    app_code = app_code.replace(
        "const handleTogglePin = async (article) => {",
        "const handleTogglePin = async (article) => {\n    if (window.DEBUG_FEED_TRACE) window.logEvent(`User clicked ${article.is_pinned ? 'Unpin' : 'Pin'}`, `Clicked article ID: ${article.id || article.url}\\nCurrent feed size: ${normalFeed.length}\\nCurrent pinned count: ${pinnedArticles.length}`);"
    )

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_code)


    # 3. Modify backend/app/main.py
    main_py_path = os.path.join(backend_dir, "main.py")
    with open(main_py_path, "r", encoding="utf-8") as f:
        main_py_code = f.read()

    # Add DEBUG_FEED_TRACE variable
    if "DEBUG_FEED_TRACE = True" not in main_py_code:
        main_py_code = main_py_code.replace("class PinRequest(BaseModel):", "DEBUG_FEED_TRACE = True\n\nclass PinRequest(BaseModel):")

    # Instrument prepare_dashboard_response
    prep_dash = """def prepare_dashboard_response(payload: dict, limit: Optional[int] = None, offset: int = 0) -> dict:
    if DEBUG_FEED_TRACE:
        logger.info(f"[DEBUG_FEED_TRACE] prepare_dashboard_response | limit={limit}, offset={offset}, keyword={payload.get('keyword')}")
        logger.info(f"[DEBUG_FEED_TRACE] BEFORE: articles={len(payload.get('articles', []))}, pinned={len(payload.get('pinned_articles', []))}")

    from app.config import settings"""
    main_py_code = main_py_code.replace("def prepare_dashboard_response(payload: dict, limit: Optional[int] = None, offset: int = 0) -> dict:\n    \"\"\"\n    Single source of truth for preparing a dashboard response payload.", prep_dash + "\n    \"\"\"\n    # Single source of truth for preparing a dashboard response payload.")

    main_py_code = main_py_code.replace(
        "final_payload[\"articles\"] = final_payload[\"articles\"][:max_unpinned]",
        "final_payload[\"articles\"] = final_payload[\"articles\"][:max_unpinned]\n        if DEBUG_FEED_TRACE: logger.info(f\"[DEBUG_FEED_TRACE] HOME_FEED_COUNT applied, max_unpinned={max_unpinned}\")"
    )

    main_py_code = main_py_code.replace(
        "final_payload[\"articles\"] = final_payload[\"articles\"][offset:offset+limit]",
        "final_payload[\"articles\"] = final_payload[\"articles\"][offset:offset+limit]\n        if DEBUG_FEED_TRACE: logger.info(f\"[DEBUG_FEED_TRACE] Pagination applied, offset={offset}, limit={limit}\")"
    )

    prep_dash_end = """
    if DEBUG_FEED_TRACE:
        logger.info(f"[DEBUG_FEED_TRACE] AFTER: articles={len(final_payload.get('articles', []))}, pinned={len(final_payload.get('pinned_articles', []))}")
    return final_payload"""
    main_py_code = main_py_code.replace("return final_payload", prep_dash_end)
    
    # Endpoints logging
    # Dashboard route
    main_py_code = main_py_code.replace(
        "def get_news(limit: Optional[int] = Query(None, description=\"Max articles to return\"),",
        "def get_news(\n    limit: Optional[int] = Query(None, description=\"Max articles to return\"),"
    )
    main_py_code = main_py_code.replace(
        "dataset = dataset_manager.get_active_dataset()",
        "if DEBUG_FEED_TRACE:\n        logger.info(f\"[DEBUG_FEED_TRACE] Endpoint /news | limit={limit}, offset={offset}, keyword={keyword}\")\n    dataset = dataset_manager.get_active_dataset()"
    )
    
    # Pin route
    main_py_code = main_py_code.replace(
        "def pin_article_endpoint(request: PinRequest):",
        "def pin_article_endpoint(request: PinRequest):\n    if DEBUG_FEED_TRACE:\n        logger.info(f\"[DEBUG_FEED_TRACE] Endpoint /news/pin | article url={request.article.url}, keyword={request.keyword}\")"
    )
    
    # Unpin route
    main_py_code = main_py_code.replace(
        "def unpin_article_endpoint(request: UnpinRequest):",
        "def unpin_article_endpoint(request: UnpinRequest):\n    if DEBUG_FEED_TRACE:\n        logger.info(f\"[DEBUG_FEED_TRACE] Endpoint /news/unpin | url={request.url}, keyword={request.keyword}\")"
    )
    
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.write(main_py_code)
        
    print("Instrumentation complete.")

if __name__ == "__main__":
    main()
