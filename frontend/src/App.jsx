import React, { useState, useEffect } from 'react';
import { 
  fetchDashboardData, 
  forceRefreshDashboard, 
  pinArticle, 
  unpinArticle,
  fetchMonitoredKeywords,
  addMonitoredKeyword,
  removeMonitoredKeyword,
  runPipelineInBackground,
  runIncrementalPipeline,
  fetchPipelineStatus
} from './api/newsApi';
import KeywordAutocomplete from './components/KeywordAutocomplete';
import RefreshTimer from './components/RefreshTimer';
import PinnedSection from './components/PinnedSection';
import ArticleGrid from './components/ArticleGrid';
import ArticleCard from './components/ArticleCard';
import DalmiaLogo from './components/DalmiaLogo';
import Sidebar from './components/Sidebar';
import { 
  Newspaper, 
  AlertCircle, 
  Building2, 
  Terminal, 
  Sun, 
  Moon, 
  Search, 
  Zap, 
  Menu,
  Trash2,
  Play,
  RefreshCw,
  LogOut,
  Sliders,
  CheckCircle2
} from 'lucide-react';
// Debug trace removed
const LoadingSkeleton = () => (
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem', width: '100%' }}>
    {[1, 2, 3, 4, 5, 6].map(i => (
      <div 
        key={i} 
        className="glass-panel shimmer" 
        style={{ 
          height: '240px', 
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)'
        }}
      />
    ))}
  </div>
);

export default function App() {
  const loadAbortControllerRef = React.useRef(null);
  const bgAbortControllerRef = React.useRef(null);
  const searchAbortControllerRef = React.useRef(null);
  const searchBgAbortControllerRef = React.useRef(null);

  const [userRole, setUserRole] = useState(() => localStorage.getItem('user_role') || null);
  const [normalFeed, setNormalFeed] = useState([]);
  
  const [pinnedArticles, setPinnedArticles] = useState([]);
  const [filterText, setFilterText] = useState('');
  const [activeView, setActiveView] = useState('feed'); // 'feed', 'search', 'admin'
  const [lastUpdated, setLastUpdated] = useState('');
  const [nextUpdate, setNextUpdate] = useState('');

  const [visibleFeedCount, setVisibleFeedCount] = useState(10);
  const [visibleSearchCount, setVisibleSearchCount] = useState(10);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  
  // Sidebar & search state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chips, setChips] = useState([]);
  const [appliedChips, setAppliedChips] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  
  // Admin dashboard state
  const [monitoredKeywords, setMonitoredKeywords] = useState([]);
  const [newKeywordInput, setNewKeywordInput] = useState('');
  const [isAddingKeyword, setIsAddingKeyword] = useState(false);
  const [pipelineRunStatus, setPipelineRunStatus] = useState({ status: 'idle', progress: 0, message: '' });

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light';
  });

  useEffect(() => {
    // Empty mount effect, debug trace removed
  }, []);

  useEffect(() => {
    document.body.className = `${theme}-theme`;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  const loadInitialData = async (reason = 'unknown') => {
    if (!userRole) return;
    setIsLoading(true);
    setError(null);
    setVisibleFeedCount(10); // Reset pagination state

    // Abort any pending requests to prevent race conditions
    if (loadAbortControllerRef.current) {
      loadAbortControllerRef.current.abort();
    }
    if (bgAbortControllerRef.current) {
      bgAbortControllerRef.current.abort();
    }

    const loadController = new AbortController();
    loadAbortControllerRef.current = loadController;

    try {
      // Fetch initial batch of articles for fast First Paint
      const data = await fetchDashboardData('', 20, 0, 'initial load - ' + reason, loadController.signal);
      setNormalFeed(data.articles || []);
      setPinnedArticles(data.pinned_articles || []);
      setLastUpdated(data.last_updated || '');
      setNextUpdate(data.next_update || '');
      
      // Stop loading early so user sees content immediately
      setIsLoading(false);
      
      // Delay background fetches to prioritize browser rendering of the first batch
      setTimeout(() => {
        if (loadController.signal.aborted) return;

        // Parallelize admin requests
        if (userRole === 'admin') {
          Promise.all([
            fetchMonitoredKeywords(),
            fetchPipelineStatus()
          ]).then(([adminData, pipeRes]) => {
            setMonitoredKeywords(adminData.keywords || []);
            setPipelineRunStatus(pipeRes.status);
          }).catch(err => console.error("Admin fetch error:", err));
        }
        
        const bgController = new AbortController();
        bgAbortControllerRef.current = bgController;

        // Background fetch remaining articles
        fetchDashboardData('', 1000, 20, 'background load', bgController.signal).then(restData => {
          if (bgController.signal.aborted) return;
          
          setNormalFeed(prev => {
            const prevIds = new Set(prev.map(a => a.id || a.url));
            const newArticles = (restData.articles || []).filter(a => !prevIds.has(a.id || a.url));
            return [...prev, ...newArticles];
          });
        }).catch(err => {
          if (err.name !== 'AbortError') console.error("Background fetch error:", err);
        });
      }, 100);

    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to load news dashboard payload.');
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    if (userRole) {
      loadInitialData('useEffect(userRole)');
    }
  }, [userRole]);

  useEffect(() => {
    const handleSearchEvent = (e) => {
      const tag = e.detail;
      setChips(prev => {
         const newChips = prev.includes(tag) ? prev : [...prev, tag];
         return newChips;
      });
      setAppliedChips(prev => {
         const newChips = prev.includes(tag) ? prev : [...prev, tag];
         handleApplySearch(newChips.join(','));
         return newChips;
      });
    };
    window.addEventListener('search-keyword', handleSearchEvent);
    return () => window.removeEventListener('search-keyword', handleSearchEvent);
  }, []);

  // Poll pipeline progress status when it's running
  useEffect(() => {
    let intervalId;
    if (pipelineRunStatus.status === 'running' && userRole === 'admin') {
      intervalId = setInterval(async () => {
        try {
          const res = await fetchPipelineStatus();
          setPipelineRunStatus(res.status);
          if (res.status.status !== 'running') {
            console.log(`[POLLING] Pipeline finished, triggering loadInitialData`);
            // Reload news items on complete
            loadInitialData('pipeline polling complete');
          }
        } catch (err) {
          console.error('Error polling status:', err);
        }
      }, 2000);
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [pipelineRunStatus.status, userRole]);

  const handleForceRefresh = async () => {
    if (userRole !== 'admin') return;
    setIsRefreshing(true);
    setError(null);
    setVisibleFeedCount(10);
    setVisibleSearchCount(20);
    try {
      const data = await forceRefreshDashboard('');
      setNormalFeed(data.articles || []);
      if (data.pinned_articles) {
        setPinnedArticles(data.pinned_articles);
      }
      setLastUpdated(data.last_updated || '');
      setNextUpdate(data.next_update || '');
    } catch (err) {
      setError('Refresh failed. Showing previous dataset. (' + (err.message || 'Unknown error') + ')');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSearch = async (term) => {
    // left for legacy
  };

  const handleApplySearch = (term) => {
    setAppliedChips(chips);
    if (term || chips.length > 0) {
      setActiveView('search');
      setVisibleSearchCount(20);
    } else {
      setActiveView('feed');
    }
  };

  const handleClear = () => {
    setChips([]);
    setAppliedChips([]);
    setSelectedSource(null);
    setFilterText('');
    setActiveView('feed');
    setVisibleFeedCount(10);
  };

  const handleSelectSidebarSource = (source) => {
    if (selectedSource === source) {
      setSelectedSource(null);
    } else {
      setSelectedSource(source);
      // Clear keyword filters
      setChips([]);
      setAppliedChips([]);
      setFilterText('');
      setActiveView('feed');
      setVisibleFeedCount(10);
    }
  };

  const handleTogglePin = async (article) => {
    // Optimistic UI update - prevent whole feed replacement
    const updateFeed = (feed) => feed.map(a => 
      ((a.id && article.id && a.id === article.id) || (a.url && article.url && a.url === article.url)) 
        ? { ...a, is_pinned: !article.is_pinned } 
        : a
    );
    
    setNormalFeed(prev => updateFeed(prev));

    try {
      let data;
      if (article.is_pinned) {
        data = await unpinArticle(article.url, '');
      } else {
        data = await pinArticle(article, '');
      }
      
      if (data.pinned_articles) {
        setPinnedArticles(data.pinned_articles);
      }
      if (data.articles) {
        setNormalFeed(data.articles);
      }
      if (data.last_updated) setLastUpdated(data.last_updated);
      if (data.next_update) setNextUpdate(data.next_update);
    } catch (err) {
      // Revert optimistic update
      const revertFeed = (feed) => feed.map(a => 
        ((a.id && article.id && a.id === article.id) || (a.url && article.url && a.url === article.url)) 
          ? { ...a, is_pinned: article.is_pinned } 
          : a
      );
      setNormalFeed(prev => revertFeed(prev));
      setError(err.message || 'Failed to toggle pin state.');
    }
  };

  const handleLogin = (role) => {
    localStorage.setItem('user_role', role);
    setUserRole(role);
  };

  const handleLogout = () => {
    localStorage.removeItem('user_role');
    setUserRole(null);
    handleClear();
  };

  const handleAddKeyword = async () => {
    const kw = newKeywordInput.trim();
    if (!kw) return;
    setIsAddingKeyword(true);
    try {
      const res = await addMonitoredKeyword(kw);
      setMonitoredKeywords(res.keywords);
      setNewKeywordInput('');
    } catch (err) {
      setError(err.message || 'Failed to add keyword.');
    } finally {
      setIsAddingKeyword(false);
    }
  };

  const handleRemoveKeyword = async (kw) => {
    try {
      const res = await removeMonitoredKeyword(kw);
      setMonitoredKeywords(res.keywords);
    } catch (err) {
      setError(err.message || 'Failed to remove keyword.');
    }
  };

  const handleTriggerPipeline = async () => {
    try {
      const res = await runPipelineInBackground();
      setPipelineRunStatus(res.status);
    } catch (err) {
      setError(err.message || 'Failed to trigger pipeline execution.');
    }
  };

  const handleTriggerIncrementalPipeline = async () => {
    try {
      const res = await runIncrementalPipeline();
      setPipelineRunStatus(res.status);
    } catch (err) {
      setError(err.message || 'Failed to trigger incremental pipeline execution.');
    }
  };

  const renderAdminPanel = () => {
    return (
      <div className="admin-section animate-fade-in">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
          <Sliders size={20} style={{ color: 'var(--color-primary)' }} />
          <h2 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-title)' }}>
            Admin Dashboard
          </h2>
        </div>
        
        <div className="admin-grid">
          {/* Monitored Keywords Management */}
          <div className="glass-panel admin-card">
            <h3 style={{ fontSize: '1.1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontFamily: 'var(--font-title)' }}>
              <Zap size={16} style={{ color: 'var(--color-secondary)' }} />
              Monitored Keywords
            </h3>
            
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              <input 
                type="text" 
                value={newKeywordInput}
                onChange={(e) => setNewKeywordInput(e.target.value)}
                placeholder="Add new search keyword..."
                style={{
                  flexGrow: 1,
                  padding: '0.65rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface-hover)',
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem',
                  outline: 'none'
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddKeyword();
                }}
              />
              <button
                onClick={handleAddKeyword}
                disabled={isAddingKeyword || !newKeywordInput.trim() || isLoading || isRefreshing || pipelineRunStatus.status === 'running'}
                style={{
                  background: 'var(--gradient-tech)',
                  color: '#ffffff',
                  border: 'none',
                  padding: '0.65rem 1.5rem',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px var(--glow-primary)'
                }}
              >
                {isAddingKeyword ? 'Adding...' : 'Add'}
              </button>
            </div>

            <div style={{ maxHeight: '320px', overflowY: 'auto', marginTop: '0.5rem', paddingRight: '0.25rem' }}>
              {monitoredKeywords.length > 0 ? (
                monitoredKeywords.map((kw, idx) => (
                  <div key={idx} className="monitored-keyword-row">
                    <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{kw}</span>
                    <button
                      onClick={() => handleRemoveKeyword(kw)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '0.25rem',
                        borderRadius: '50%'
                      }}
                      title="Remove Keyword"
                    >
                      <Trash2 size={16} style={{ color: 'var(--color-accent)' }} />
                    </button>
                  </div>
                ))
              ) : (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  No monitored keywords configured.
                </div>
              )}
            </div>
          </div>

          {/* Pipeline controls and Status */}
          <div className="glass-panel admin-card">
            <h3 style={{ fontSize: '1.1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontFamily: 'var(--font-title)' }}>
              <Play size={16} style={{ color: 'var(--color-primary)' }} />
              Scraping Pipeline Controls
            </h3>
            
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
              Manage news ingestion. Scraping processes websites, performs LLM reasoning, extracts article details, generates 3 search tags, and updates the cache.
            </p>

            {/* Section A: Incremental Pipeline */}
            <div style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>Run Pipeline for New Keywords Only</span>
              <button
                onClick={handleTriggerIncrementalPipeline}
                disabled={pipelineRunStatus.status === 'running' || isLoading || isRefreshing}
                style={{
                  background: 'var(--gradient-tech)',
                  color: '#ffffff',
                  border: 'none',
                  padding: '0.65rem 1.25rem',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  width: 'fit-content',
                  boxShadow: '0 4px 12px var(--glow-primary)',
                  opacity: pipelineRunStatus.status === 'running' ? 0.6 : 1,
                  cursor: pipelineRunStatus.status === 'running' ? 'not-allowed' : 'pointer'
                }}
              >
                <RefreshCw size={16} className={pipelineRunStatus.status === 'running' ? 'animate-spin' : ''} />
                Run Incremental Pipeline
              </button>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Processes only newly added keywords that have not been scraped yet.
              </span>
            </div>

            {/* Visual Divider */}
            <div style={{ display: 'flex', alignItems: 'center', margin: '1.25rem 0', color: 'var(--text-muted)' }}>
              <div style={{ flexGrow: 1, height: '1px', background: 'var(--border-color)' }}></div>
              <span style={{ padding: '0 1rem', fontSize: '0.75rem', fontWeight: 600 }}>OR</span>
              <div style={{ flexGrow: 1, height: '1px', background: 'var(--border-color)' }}></div>
            </div>

            {/* Section B: Full Pipeline */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>Run Full Pipeline</span>
              <button
                onClick={handleTriggerPipeline}
                disabled={pipelineRunStatus.status === 'running' || isLoading || isRefreshing}
                style={{
                  background: 'var(--gradient-tech)',
                  color: '#ffffff',
                  border: 'none',
                  padding: '0.65rem 1.25rem',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  width: 'fit-content',
                  boxShadow: '0 4px 12px var(--glow-primary)',
                  opacity: pipelineRunStatus.status === 'running' ? 0.6 : 1,
                  cursor: pipelineRunStatus.status === 'running' ? 'not-allowed' : 'pointer'
                }}
              >
                <Play size={16} />
                Run Full Pipeline (All Keywords)
              </button>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Re-runs the entire pipeline for all monitored keywords. May take several minutes.
              </span>
            </div>

            {pipelineRunStatus.status === 'running' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: 600 }}>
                  <span style={{ color: 'var(--text-primary)' }}>{pipelineRunStatus.message}</span>
                  <span style={{ color: 'var(--color-secondary)' }}>{pipelineRunStatus.progress}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill" style={{ width: `${pipelineRunStatus.progress}%` }}></div>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Started: {pipelineRunStatus.started_at ? new Date(pipelineRunStatus.started_at).toLocaleTimeString() : '--:--'}
                </span>
              </div>
            )}

            {pipelineRunStatus.status === 'completed' && (
              <div style={{ color: '#10b981', fontSize: '0.85rem', marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(16, 185, 129, 0.05)', padding: '0.75rem', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                <CheckCircle2 size={16} />
                <span>Aggregator completed successfully. Dashboard is updated!</span>
              </div>
            )}

            {pipelineRunStatus.status === 'failed' && (
              <div style={{ color: 'var(--color-accent)', fontSize: '0.85rem', marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(239, 68, 68, 0.05)', padding: '0.75rem', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                <AlertCircle size={16} />
                <span>Error: {pipelineRunStatus.message}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // --- Optimized Memoized Selectors ---
  const draftDataset = React.useMemo(() => {
    let unfiltered = [...normalFeed];
    if (selectedSource) {
      unfiltered = unfiltered.filter(a => (a.source || 'Unknown') === selectedSource);
    }
    if (chips.length > 0) {
      unfiltered = unfiltered.filter(a => 
        chips.every(chip => 
          a.keywords && a.keywords.map(k => k.toLowerCase()).includes(chip.toLowerCase())
        )
      );
    }
    return filterText 
      ? unfiltered.filter(a => 
          a.title?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.summary?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.company?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.keywords?.some(k => k.toLowerCase().includes(filterText.toLowerCase()))
        )
      : unfiltered;
  }, [normalFeed, selectedSource, chips, filterText]);

  const currentDataset = React.useMemo(() => {
    let unfiltered = [...normalFeed];
    if (selectedSource) {
      unfiltered = unfiltered.filter(a => (a.source || 'Unknown') === selectedSource);
    }
    if (appliedChips.length > 0) {
      unfiltered = unfiltered.filter(a => 
        appliedChips.every(chip => 
          a.keywords && a.keywords.map(k => k.toLowerCase()).includes(chip.toLowerCase())
        )
      );
    }
    return filterText 
      ? unfiltered.filter(a => 
          a.title?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.summary?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.company?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.keywords?.some(k => k.toLowerCase().includes(filterText.toLowerCase()))
        )
      : unfiltered;
  }, [normalFeed, selectedSource, appliedChips, filterText]);

  const filteredPinnedArticles = React.useMemo(() => {
    let unfiltered = [...pinnedArticles];
    if (selectedSource) {
      unfiltered = unfiltered.filter(a => (a.source || 'Unknown') === selectedSource);
    }
    if (appliedChips.length > 0) {
      unfiltered = unfiltered.filter(a => 
        appliedChips.every(chip => 
          a.keywords && a.keywords.map(k => k.toLowerCase()).includes(chip.toLowerCase())
        )
      );
    }
    return filterText 
      ? unfiltered.filter(a => 
          a.title?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.summary?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.company?.toLowerCase().includes(filterText.toLowerCase()) || 
          a.keywords?.some(k => k.toLowerCase().includes(filterText.toLowerCase()))
        )
      : unfiltered;
  }, [pinnedArticles, selectedSource, appliedChips, filterText]);

  const sourceCounts = React.useMemo(() => {
    const counts = {};
    currentDataset.forEach(art => {
      const src = art.source || 'Unknown';
      counts[src] = (counts[src] || 0) + 1;
    });
    return counts;
  }, [currentDataset]);

  const keywordCounts = React.useMemo(() => {
    const counts = {};
    draftDataset.forEach(art => {
      if (art.keywords && Array.isArray(art.keywords)) {
        art.keywords.forEach(kw => {
          counts[kw] = (counts[kw] || 0) + 1;
        });
      }
    });
    return counts;
  }, [draftDataset]);

  const paginatedFeed = React.useMemo(() => {
    return currentDataset.slice(0, visibleFeedCount);
  }, [currentDataset, visibleFeedCount]);

  const paginatedSearch = React.useMemo(() => {
    return currentDataset.slice(0, visibleSearchCount);
  }, [currentDataset, visibleSearchCount]);
  // ------------------------------------

  return (
    <div className="app-container">
      {/* Login Screen Gateway */}
      {!userRole && (
        <div className="login-gateway-overlay">
          <div className="glass-panel login-gateway-card animate-fade-in">
            <DalmiaLogo height="48px" />
            <h2 style={{ fontSize: '1.75rem', color: 'var(--text-primary)', fontFamily: 'var(--font-title)' }}>
              Dalmia Cement <span style={{ color: '#e2a02b' }}>Intel Hub</span>
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.5 }}>
              Select your authorization role profile to access the news dashboard:
            </p>
            <div className="role-cards-container">
              <div className="role-card" onClick={() => handleLogin('employee')}>
                <Building2 size={36} style={{ color: '#1a3a5c' }} />
                <h3 style={{ fontSize: '1.15rem' }}>Employee Profile</h3>
                <p style={{ fontSize: '0.8rem', textAlign: 'center', lineHeight: 1.4 }}>
                  Browse dynamic feeds, search cache, pin competitor reports and read news.
                </p>
              </div>
              <div className="role-card" onClick={() => handleLogin('admin')}>
                <Terminal size={36} style={{ color: '#e2a02b' }} />
                <h3 style={{ fontSize: '1.15rem' }}>Administrator Profile</h3>
                <p style={{ fontSize: '0.8rem', textAlign: 'center', lineHeight: 1.4 }}>
                  Manage search keywords, manual scraper trigger, view progress and refresh cache.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Premium Header */}
      <header 
        className="glass-panel animate-fade-in"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.25rem 2rem',
          borderRadius: 'var(--radius-lg)',
          background: 'linear-gradient(90deg, #1a3a5c 0%, #254a75 100%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#ffffff'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div 
            style={{
              background: '#ffffff',
              padding: '0.4rem 0.8rem',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <DalmiaLogo height="32px" />
          </div>

          <div>
            <h1 style={{ fontSize: '1.45rem', lineHeight: 1.1, fontFamily: 'var(--font-title)', color: '#ffffff' }}>
              Dalmia Cement <span style={{ color: '#e2a02b' }}>News Intel Hub</span>
            </h1>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#ffffff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0.5rem',
              borderRadius: '50%',
              transition: 'var(--transition-bounce)',
            }}
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>

          {/* User profile toggle */}
          {userRole && (
            <button
              onClick={handleLogout}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#ffffff',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 1rem',
                borderRadius: '100px',
                fontSize: '0.8rem',
                fontWeight: 600,
                fontFamily: 'var(--font-title)',
                transition: 'var(--transition-smooth)'
              }}
            >
              <LogOut size={12} />
              <span>Log out ({userRole === 'admin' ? 'Admin' : 'Employee'})</span>
            </button>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'rgba(255, 255, 255, 0.7)' }}>
            <Terminal size={14} style={{ color: '#e2a02b' }} />
            <span style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>POC Build v1.1.0</span>
          </div>
        </div>
      </header>

      {/* Main Search Panel & Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '100%', position: 'relative', zIndex: 95 }}>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="glass-panel"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0.6rem 1.25rem',
            borderRadius: '100px',
            gap: '0.5rem',
            fontWeight: 600,
            fontSize: '0.9rem',
            transition: 'var(--transition-bounce)',
            flexShrink: 0,
            height: '45px'
          }}
          title={sidebarOpen ? "Hide Topics" : "Show Topics"}
        >
          <Menu size={16} style={{ color: 'var(--color-secondary)' }} />
          <span className="sidebar-toggle-text">{sidebarOpen ? "Hide Topics" : "Show Topics"}</span>
        </button>

        <KeywordAutocomplete 
          onSearch={handleSearch} 
          onApplySearch={handleApplySearch}
          onClear={handleClear} 
          onInputChange={setFilterText}
          isLoading={isLoading || isRefreshing} 
          chips={chips}
          setChips={setChips}
          keywordCounts={keywordCounts}
        />
      </div>

      {/* Mobile Sidebar Backdrop Overlay */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          className="mobile-sidebar-backdrop"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.4)',
            backdropFilter: 'blur(4px)',
            zIndex: 95,
            transition: 'all 0.3s ease'
          }}
        />
      )}

      {/* Split layout: Sidebar + Main feed */}
      <div style={{ display: 'flex', gap: sidebarOpen ? '2rem' : '0', width: '100%', alignItems: 'stretch', position: 'relative', flexGrow: 1, minHeight: 0, overflow: 'hidden', transition: 'gap 0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}>
        
        {(() => {
          return (
            <Sidebar 
              sourceCounts={sourceCounts}
              selectedSource={selectedSource}
              onSelectSource={handleSelectSidebarSource}
              isOpen={sidebarOpen}
              onToggle={() => setSidebarOpen(!sidebarOpen)}
            />
          );
        })()}

        {/* Main Feed Content Area */}
        <div className="article-scroll-container" style={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '2.5rem', overflowY: 'auto', height: '100%', paddingRight: '0.5rem' }}>
          
          {/* Navigation Tabs */}
          <div className="nav-tabs-container glass-panel animate-fade-in">
            {[
              { id: 'feed', label: 'Home Feed', icon: Newspaper, count: normalFeed.length + pinnedArticles.length },
              { id: 'search', label: 'Search Results', icon: Search, count: (chips.length > 0 || filterText) ? currentDataset.length + filteredPinnedArticles.length : null },
              // Admin tab visible only to administrators
              ...(userRole === 'admin' ? [{ id: 'admin', label: 'Admin Dashboard', icon: Sliders, count: null }] : [])
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeView === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveView(tab.id)}
                  className={`nav-tab-button ${isActive ? 'active' : ''}`}
                >
                  <Icon size={18} style={{ color: isActive ? '#ffffff' : 'var(--color-primary)', flexShrink: 0 }} />
                  <span>{tab.label}</span>
                  {tab.count !== null && (
                    <span className="nav-tab-badge">
                      {tab.count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Refresh Scheduler Status */}
          {nextUpdate && activeView !== 'admin' && (
            <RefreshTimer 
              nextUpdate={nextUpdate}
            />
          )}

          {/* Errors display */}
          {error && (() => {
            const isConnError = error.startsWith("ConnectionError:");
            const displayError = isConnError ? error.replace("ConnectionError:", "").trim() : error;
            return (
              <div 
                className="glass-panel animate-fade-in"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '1rem 1.5rem',
                  borderColor: isConnError 
                    ? (theme === 'light' ? '#fee2e2' : 'rgba(239, 68, 68, 0.3)')
                    : (theme === 'light' ? '#fde68a' : 'rgba(245, 158, 11, 0.3)'),
                  background: isConnError
                    ? (theme === 'light' ? '#fef2f2' : 'rgba(239, 68, 68, 0.1)')
                    : (theme === 'light' ? '#fffbeb' : 'rgba(245, 158, 11, 0.05)'),
                  color: isConnError
                    ? (theme === 'light' ? '#991b1b' : '#fca5a5')
                    : (theme === 'light' ? '#b45309' : '#fcd34d'),
                  borderRadius: 'var(--radius-md)'
                }}
              >
                <AlertCircle size={20} style={{ flexShrink: 0 }} />
                <div style={{ fontSize: '0.9rem' }}>
                  <strong>{isConnError ? 'Connection Error:' : 'Pipeline Sync Warning:'}</strong> {displayError}
                </div>
              </div>
            );
          })()}

          {/* Loading Skeleton / Main View Content */}
          {isLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="glass-panel shimmer" style={{ height: '30px', width: '200px', borderRadius: '4px' }} />
                <LoadingSkeleton />
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
              
              {/* Feed View */}
              {activeView === 'feed' && (() => {
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {filteredPinnedArticles.length > 0 && (
                      <div style={{ marginBottom: '1.5rem' }}>
                        <PinnedSection 
                          articles={filteredPinnedArticles} 
                          onTogglePin={handleTogglePin} 
                        />
                      </div>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                      <Newspaper size={18} style={{ color: 'var(--color-primary)' }} />
                      <h2 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-title)' }}>
                        General Manufacturing & Industry Feed
                      </h2>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', marginLeft: 'auto' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          Showing {currentDataset.length} articles
                        </span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontStyle: 'italic', opacity: 0.8 }}>
                          Articles are deduplicated over the previous 7 days.
                        </span>
                      </div>
                    </div>

                    {currentDataset.length > 0 ? (
                      <>
                        <ArticleGrid>
                          {paginatedFeed.map((article, idx) => (
                            <ArticleCard 
                              key={`general-${idx}`} 
                              article={article} 
                              onTogglePin={handleTogglePin} 
                            />
                          ))}
                        </ArticleGrid>
                        {currentDataset.length > paginatedFeed.length && (
                          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '2rem' }}>
                            <button
                              onClick={() => setVisibleFeedCount(prev => prev + 10)}
                              style={{
                                background: 'var(--bg-surface)',
                                border: '1px solid var(--border-color)',
                                color: 'var(--text-primary)',
                                padding: '0.75rem 2rem',
                                borderRadius: '100px',
                                fontWeight: 600,
                                cursor: 'pointer',
                                boxShadow: 'var(--shadow-panel)',
                                transition: 'var(--transition-bounce)'
                              }}
                            >
                              Load More Articles
                            </button>
                          </div>
                        )}
                      </>
                    ) : (
                      <div 
                        className="glass-panel"
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: '4rem 2rem',
                          textAlign: 'center',
                          color: 'var(--text-secondary)',
                          gap: '0.75rem'
                        }}
                      >
                        <Newspaper size={48} style={{ color: 'var(--text-muted)' }} />
                        <h3 style={{ fontSize: '1.15rem', color: 'var(--text-primary)' }}>No articles found</h3>
                        <p style={{ fontSize: '0.9rem', maxWidth: '400px' }}>
                          The industry feed is currently empty.
                        </p>
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Search View */}
              {activeView === 'search' && (() => {
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {filteredPinnedArticles.length > 0 && (
                      <div style={{ marginBottom: '1.5rem' }}>
                        <PinnedSection 
                          articles={filteredPinnedArticles} 
                          onTogglePin={handleTogglePin} 
                        />
                      </div>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                      <Search size={18} style={{ color: 'var(--color-primary)' }} />
                      <h2 style={{ fontSize: '1.25rem', fontFamily: 'var(--font-title)' }}>
                        {chips.length > 0 ? `Topic Intelligence: "${chips.join(', ')}"` : (filterText ? `Topic Intelligence: "${filterText}"` : 'Search Results')}
                      </h2>
                      {(chips.length > 0 || filterText) && (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', marginLeft: 'auto' }}>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            Showing {currentDataset.length + filteredPinnedArticles.length} articles
                          </span>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontStyle: 'italic', opacity: 0.8 }}>
                            Articles are deduplicated over the previous 7 days.
                          </span>
                        </div>
                      )}
                    </div>

                    {(!chips.length && !filterText) ? (
                      <div className="glass-panel welcome-panel animate-fade-in">
                        <Search size={48} style={{ color: 'var(--text-muted)' }} />
                        <h3 style={{ fontSize: '1.25rem', color: 'var(--text-primary)', fontFamily: 'var(--font-title)' }}>
                          AI Search Desk
                        </h3>
                        <p style={{ fontSize: '0.95rem', maxWidth: '450px', lineHeight: 1.6 }}>
                          Enter industry, technology, or competitor keywords in the search bar above to fetch targeted real-time intelligence reports.
                        </p>
                      </div>
                    ) : currentDataset.length > 0 ? (
                      <>
                        <ArticleGrid>
                          {paginatedSearch.map((article, idx) => (
                            <ArticleCard 
                              key={`search-${idx}`} 
                              article={article} 
                              onTogglePin={handleTogglePin} 
                            />
                          ))}
                        </ArticleGrid>
                        {currentDataset.length > paginatedSearch.length && (
                          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '2rem' }}>
                            <button
                              onClick={() => setVisibleSearchCount(prev => prev + 10)}
                              style={{
                                background: 'var(--bg-surface)',
                                border: '1px solid var(--border-color)',
                                color: 'var(--text-primary)',
                                padding: '0.75rem 2rem',
                                borderRadius: '100px',
                                fontWeight: 600,
                                cursor: 'pointer',
                                boxShadow: 'var(--shadow-panel)',
                                transition: 'var(--transition-bounce)'
                              }}
                            >
                              Load More Articles
                            </button>
                          </div>
                        )}
                      </>
                    ) : (
                      <div 
                        className="glass-panel"
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: '4rem 2rem',
                          textAlign: 'center',
                          color: 'var(--text-secondary)',
                          gap: '0.75rem'
                        }}
                      >
                        <Newspaper size={48} style={{ color: 'var(--text-muted)' }} />
                        <h3 style={{ fontSize: '1.15rem', color: 'var(--text-primary)' }}>No matching articles found</h3>
                        <p style={{ fontSize: '0.9rem', maxWidth: '400px' }}>
                          All raw articles for this topic were either filtered due to the 7-day de-duplication rules, or search results were empty.
                        </p>
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Admin Panel View */}
              {activeView === 'admin' && userRole === 'admin' && renderAdminPanel()}

            </div>
          )}
        </div>
      </div>

      {isRefreshing && (
        <div 
          className="animate-fade-in glass-panel" 
          style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            zIndex: 999,
            padding: '0.75rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'var(--color-primary)',
            color: 'white',
            borderRadius: '100px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.2)'
          }}
        >
          <RefreshCw size={16} className="animate-spin" />
          <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Refreshing...</span>
        </div>
      )}
    </div>
  );
}
