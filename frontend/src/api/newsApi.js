const API_BASE_URL = 
  (import.meta.env && (import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL)) || 
  'http://localhost:8000/api';

/**
 * Gets the authorization role header from localStorage.
 * @returns {object} headers object containing X-User-Role
 */
function getAuthHeaders() {
  const role = localStorage.getItem('user_role') || 'employee';
  return {
    'X-User-Role': role
  };
}

export async function fetchDashboardData(keyword = '', limit = null, offset = null, source = 'unknown', signal = null) {
  const url = new URL(`${API_BASE_URL}/news`);
  if (keyword) {
    url.searchParams.append('keyword', keyword);
  }
  if (limit !== null) {
    url.searchParams.append('limit', limit);
  }
  if (offset !== null) {
    url.searchParams.append('offset', offset);
  }
  
  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...getAuthHeaders()
      },
      signal
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to fetch news feed (Status ${response.status})`);
    }
    
    return await response.json();
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Force manual pipeline execution, bypassing database cache (Admin only)
 * @param {string} [keyword] Optional keyword search term to refresh
 * @returns {Promise<object>} Refreshed dashboard payload object
 */
export async function forceRefreshDashboard(keyword = '') {
  try {
    const response = await fetch(`${API_BASE_URL}/news/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ keyword: keyword || null }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to refresh news feed (Status ${response.status})`);
    }
    
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Pin an article to the pinned-articles store
 * @param {object} article The article object to pin
 * @param {string} [keyword] The currently active search keyword
 * @returns {Promise<object>} Updated dashboard payload
 */
export async function pinArticle(article, keyword = '') {
  const reqId = ++requestCounter;
  if (window.DEBUG_FEED_TRACE) console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} (Pin) started`);
  const startTime = Date.now();
  try {
    const response = await fetch(`${API_BASE_URL}/news/pin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ article, keyword: keyword || null }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to pin article (Status ${response.status})`);
    }
    
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Unpin an article from the pinned-articles store
 * @param {string} url The URL of the article to unpin
 * @param {string} [keyword] The currently active search keyword
 * @returns {Promise<object>} Updated dashboard payload
 */
export async function unpinArticle(url, keyword = '') {
  const reqId = ++requestCounter;
  if (window.DEBUG_FEED_TRACE) console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} (Unpin) started`);
  const startTime = Date.now();
  try {
    const response = await fetch(`${API_BASE_URL}/news/unpin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ url, keyword: keyword || null }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to unpin article (Status ${response.status})`);
    }
    
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Fetch list of monitored search keywords (Admin only)
 * @returns {Promise<object>} list of monitored keywords
 */
export async function fetchMonitoredKeywords() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/keywords`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...getAuthHeaders()
      }
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch monitored keywords');
    }
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Add a new keyword to the monitored list (Admin only)
 * @param {string} keyword The keyword to add
 * @returns {Promise<object>} Update response
 */
export async function addMonitoredKeyword(keyword) {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/keywords`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ keyword })
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to add monitored keyword');
    }
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Remove a keyword from the monitored list (Admin only)
 * @param {string} keyword The keyword to remove
 * @returns {Promise<object>} Update response
 */
export async function removeMonitoredKeyword(keyword) {
  try {
    const url = new URL(`${API_BASE_URL}/admin/keywords`);
    url.searchParams.append('keyword', keyword);
    
    const response = await fetch(url.toString(), {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
        ...getAuthHeaders()
      }
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to remove monitored keyword');
    }
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Manually trigger pipeline execution in the background (Admin only)
 * @returns {Promise<object>} Execution status
 */
export async function runPipelineInBackground() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/pipeline/run`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        ...getAuthHeaders()
      }
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to trigger pipeline run');
    }
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Manually trigger incremental pipeline execution (Admin only)
 * @returns {Promise<object>} Execution status
 */
export async function runIncrementalPipeline() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/pipeline/run/incremental`, {
      method: 'POST',
      headers: { 
        'Accept': 'application/json',
        ...getAuthHeaders() 
      },
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to trigger incremental pipeline run');
    }
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}

/**
 * Fetch current status of pipeline execution (Admin only)
 * @returns {Promise<object>} status
 */
export async function fetchPipelineStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/admin/pipeline/status`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...getAuthHeaders()
      }
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch pipeline status');
    }
    const data = await response.json();
    if (window.DEBUG_FEED_TRACE && (response.url.includes('pin') || response.url.includes('unpin'))) {
      const endTime = Date.now();
      const count = data.articles ? data.articles.length : 0;
      const pinnedCount = data.pinned_articles ? data.pinned_articles.length : 0;
      const kwCount = data.keyword_counts ? Object.keys(data.keyword_counts).length : 0;
      const firstId = count > 0 ? (data.articles[0].id || data.articles[0].url) : 'none';
      const lastId = count > 0 ? (data.articles[count - 1].id || data.articles[count - 1].url) : 'none';
      console.log(`${window.performance ? window.performance.now().toFixed(3) : 0} Request #${reqId} finished. Duration: ${endTime - startTime}ms. Returned ${count} articles, ${pinnedCount} pinned, ${kwCount} keywords. First ID: ${firstId}, Last ID: ${lastId}`);
    }
    return data;
  } catch (err) {
    if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
      throw new Error("ConnectionError: Backend unreachable");
    }
    throw err;
  }
}
