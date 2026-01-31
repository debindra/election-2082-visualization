import React, { useState, useEffect, useCallback } from 'react';
import MapView from './components/MapView';
import FiltersPanel from './components/FiltersPanel';
import CandidateComparison from './components/CandidateComparison';
import InsightsDashboard from './components/InsightsDashboard';
import Footer from './components/Footer';
import LegalPage from './components/LegalPage';
import { getMapData, getElectionSummary } from './services/api';

const ELECTION_YEAR = 2082;
import { getViewContext } from './config/viewContext';
import {
  IconBallot,
  IconBuildingColumns,
  IconMapPin,
  IconUsers,
} from './components/icons';

const LANG_KEY = 'election-viz-lang';

/** Hash to legal page key: #data-sources -> dataSources */
const HASH_TO_PAGE = {
  disclaimer: 'disclaimer',
  privacy: 'privacy',
  terms: 'terms',
  'data-sources': 'dataSources',
};

function App() {
  const [language, setLanguage] = useState(() => {
    try {
      const stored = localStorage.getItem(LANG_KEY);
      return stored === 'en' || stored === 'ne' ? stored : 'ne';
    } catch {
      return 'ne';
    }
  });
  const [mapData, setMapData] = useState(null);
  const [filters, setFilters] = useState({
    electionYear: ELECTION_YEAR,
    level: 'province', // province -> district -> constituency
    province: null,
    district: null,
    party: null,
    independent: null,
    ageMin: null,
    ageMax: null,
    gender: null,
    educationLevel: null,
  });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('areas');
  const [filtersVisible, setFiltersVisible] = useState(true);
  const [breadcrumb, setBreadcrumb] = useState([{ level: 'province', name: 'Nepal' }]);
  const [focusConstituency, setFocusConstituency] = useState(null);
  const [electionSummary, setElectionSummary] = useState(null);
  const [legalPage, setLegalPage] = useState(null);
  const [apiErrorMessage, setApiErrorMessage] = useState(null);

  const syncLegalFromHash = useCallback(() => {
    const hash = window.location.hash.slice(1);
    setLegalPage(HASH_TO_PAGE[hash] || null);
  }, []);

  useEffect(() => {
    syncLegalFromHash();
    window.addEventListener('hashchange', syncLegalFromHash);
    return () => window.removeEventListener('hashchange', syncLegalFromHash);
  }, [syncLegalFromHash]);

  const handleLegalLinkClick = useCallback((hashName) => {
    const pageKey = HASH_TO_PAGE[hashName];
    if (pageKey) setLegalPage(pageKey);
  }, []);

  const closeLegalPage = useCallback(() => {
    setLegalPage(null);
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
  }, []);

  useEffect(() => {
    const onApiError = (e) => setApiErrorMessage(e.detail?.message || 'Network error');
    window.addEventListener('api-error', onApiError);
    return () => window.removeEventListener('api-error', onApiError);
  }, []);

  useEffect(() => {
    if (!filters.electionYear) {
      setElectionSummary(null);
      return;
    }
    let cancelled = false;
    getElectionSummary(filters.electionYear)
      .then((data) => {
        if (!cancelled) setElectionSummary(data);
      })
      .catch(() => {
        if (!cancelled) setElectionSummary(null);
      });
    return () => { cancelled = true; };
  }, [filters.electionYear]);

  useEffect(() => {
    if (filters.electionYear) {
      loadMapData();
    }
  }, [filters]);

  const loadMapData = async () => {
    if (!filters.electionYear) return;

    setLoading(true);
    try {
      const data = await getMapData(filters);
      setMapData(data);
    } catch (error) {
      console.error('Failed to load map data:', error);
    } finally {
      setLoading(false);
    }
  };

  const setLanguageAndStore = (lang) => {
    setLanguage(lang);
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch (_) {}
  };

  const handleFeatureClick = (feature) => {
    console.log('Feature clicked:', feature.properties);
  };

  // Handle drill-down from province -> district -> constituency
  const handleDrillDown = useCallback((properties) => {
    const currentLevel = properties.geography_level;
    const name = properties.name;
    const nextLevel = properties.drilldown_to;

    if (!nextLevel || nextLevel === 'null') return;

    if (currentLevel === 'province') {
      // Drill down to districts
      setFilters(prev => ({
        ...prev,
        level: 'district',
        province: name,
        district: null,
      }));
      setBreadcrumb([
        { level: 'province', name: 'Nepal' },
        { level: 'district', name: name }
      ]);
    } else if (currentLevel === 'district') {
      // Drill down to constituencies
      setFilters(prev => ({
        ...prev,
        level: 'constituency',
        district: name,
      }));
      setBreadcrumb(prev => [
        ...prev,
        { level: 'constituency', name: name }
      ]);
    }
  }, []);

  // Handle breadcrumb navigation (go back up)
  const handleBreadcrumbClick = (index) => {
    const item = breadcrumb[index];
    
    if (item.level === 'province') {
      // Reset to province view
      setFilters(prev => ({
        ...prev,
        level: 'province',
        province: null,
        district: null,
      }));
      setBreadcrumb([{ level: 'province', name: 'Nepal' }]);
    } else if (item.level === 'district') {
      // Go back to district view
      setFilters(prev => ({
        ...prev,
        level: 'district',
        district: null,
      }));
      setBreadcrumb(breadcrumb.slice(0, index + 1));
    }
  };

  return (
    <div className="min-h-screen min-h-dvh flex flex-col bg-gradient-to-br from-[#1e3a5f]/5 to-[#b91c1c]/5 overflow-x-hidden">
      {/* Header — theme: slate blue #1e3a5f, muted red #b91c1c */}
      <header className="bg-white/95 backdrop-blur border-b-2 border-[#1e3a5f] shadow-sm">
        <div className="bg-gradient-to-r from-[#b91c1c]/5 via-transparent to-[#1e3a5f]/5">
          <div className="px-4 lg:px-6 py-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                <img
                  src="/Flag_of_Nepal.png"
                  alt="Nepal"
                  className="w-9 h-9 sm:w-10 sm:h-10 object-contain shrink-0 drop-shadow-sm"
                />
                <div className="min-w-0 flex-1">
                  <h1 className="text-base sm:text-xl lg:text-2xl font-semibold tracking-tight text-[#1e3a5f] truncate">
                    {language === 'en' ? `House of Representatives Election ${filters.electionYear || ''}` : `प्रतिनिधिसभा निर्वाचन ${filters.electionYear || ''}`}
                  </h1>
                  <p className="text-xs lg:text-sm text-[#1e3a5f]/70 truncate hidden sm:block">
                    {electionSummary && filters.electionYear
                      ? language === 'en'
                        ? `Election ${filters.electionYear}: ${(electionSummary.total_candidates ?? 0).toLocaleString()} candidates, ${electionSummary.total_constituencies ?? 0} constituencies`
                        : `निर्वाचन ${filters.electionYear}: ${(electionSummary.total_candidates ?? 0).toLocaleString()} उम्मेदवार, ${electionSummary.total_constituencies ?? 0} निर्वाचन क्षेत्र`
                      : language === 'en'
                        ? 'Nepal election data, mapped and explained'
                        : 'नेपाल प्रतिनिधिसभा निर्वाचन डाटा'}
                  </p>
                </div>
              </div>
              <div className="hidden md:flex items-center gap-4 lg:gap-6 text-xs lg:text-sm">
                <div className="text-center">
                  <div className="text-base lg:text-lg font-semibold text-[#b91c1c]">७</div>
                  <div className="text-[#1e3a5f]/70">{language === 'en' ? 'Provinces' : 'प्रदेश'}</div>
                </div>
                <div className="h-8 w-px bg-[#1e3a5f]/30" />
                <div className="text-center">
                  <div className="text-base lg:text-lg font-semibold text-[#b91c1c]">७७</div>
                  <div className="text-[#1e3a5f]/70">{language === 'en' ? 'Districts' : 'जिल्ला'}</div>
                </div>
                <div className="h-8 w-px bg-[#1e3a5f]/30" />
                <div className="text-center">
                  <div className="text-base lg:text-lg font-semibold text-[#b91c1c]">१६५</div>
                  <div className="text-[#1e3a5f]/70">{language === 'en' ? 'Constituencies' : 'निर्वाचन क्षेत्र'}</div>
                </div>
              </div>
              {/* Language toggle: English / नेपाली */}
              <div className="flex items-center gap-1 rounded-full bg-[#1e3a5f]/10 p-1 shrink-0">
                <button
                  type="button"
                  onClick={() => setLanguageAndStore('en')}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${language === 'en' ? 'bg-[#1e3a5f] text-white' : 'text-[#1e3a5f]/70 hover:text-[#1e3a5f]'}`}
                >
                  English
                </button>
                <button
                  type="button"
                  onClick={() => setLanguageAndStore('ne')}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${language === 'ne' ? 'bg-[#1e3a5f] text-white' : 'text-[#1e3a5f]/70 hover:text-[#1e3a5f]'}`}
                >
                  नेपाली
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="px-2 sm:px-3 lg:px-6 pb-2 pt-0.5 overflow-x-auto">
          <div className="inline-flex gap-1 rounded-full bg-[#1e3a5f]/10 p-1 text-xs lg:text-sm min-w-0">
            <button
              onClick={() => setActiveTab('areas')}
              className={`inline-flex items-center gap-1.5 px-3 lg:px-4 py-1.5 rounded-full font-medium transition-all ${
                activeTab === 'areas'
                  ? 'bg-[#b91c1c] text-white shadow-sm'
                  : 'text-[#1e3a5f]/80 hover:text-[#1e3a5f] hover:bg-white/80'
              }`}
            >
              <IconBuildingColumns className="w-4 h-4" />
              <span className="hidden sm:inline">{language === 'en' ? 'Election areas' : 'निर्वाचन क्षेत्र'}</span>
              <span className="sm:hidden">{language === 'en' ? 'Areas' : 'क्षेत्र'}</span>
            </button>
            <button
              onClick={() => setActiveTab('insights')}
              className={`inline-flex items-center gap-1.5 px-3 lg:px-4 py-1.5 rounded-full font-medium transition-all ${
                activeTab === 'insights'
                  ? 'bg-[#b91c1c] text-white shadow-sm'
                  : 'text-[#1e3a5f]/80 hover:text-[#1e3a5f] hover:bg-white/80'
              }`}
            >
              <IconBallot className="w-4 h-4" />
              <span className="hidden sm:inline">{language === 'en' ? 'Insights' : 'अन्तर्दृष्टि'}</span>
              <span className="sm:hidden">{language === 'en' ? 'Insights' : 'अन्तर्दृष्टि'}</span>
            </button>
            <button
              onClick={() => setActiveTab('compare')}
              className={`inline-flex items-center gap-1.5 px-3 lg:px-4 py-1.5 rounded-full font-medium transition-all ${
                activeTab === 'compare'
                  ? 'bg-[#b91c1c] text-white shadow-sm'
                  : 'text-[#1e3a5f]/80 hover:text-[#1e3a5f] hover:bg-white/80'
              }`}
            >
              <IconUsers className="w-4 h-4" />
              <span className="hidden sm:inline">{language === 'en' ? 'Compare candidates' : 'उम्मेदवार तुलना'}</span>
              <span className="sm:hidden">{language === 'en' ? 'Compare' : 'तुलना'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Mobile: filter toggle only on Election areas tab — filters are map-specific */}
        {activeTab === 'areas' && (
          <button
            onClick={() => {
              document.getElementById('filters-sidebar').classList.toggle('-translate-x-full');
              document.getElementById('mobile-overlay').classList.toggle('hidden');
            }}
            className="lg:hidden fixed top-[4.5rem] left-[max(0.75rem,env(safe-area-inset-left))] sm:left-4 z-50 p-3 min-w-[44px] min-h-[44px] flex items-center justify-center bg-[#1e3a5f] text-white rounded-full shadow-lg hover:bg-[#1e3a5f]/90 active:scale-95 transition-all touch-manipulation"
            aria-label={language === 'en' ? 'Toggle area filters' : 'क्षेत्र फिल्टर खोल्नुहोस्'}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}

        {/* Desktop: show filters button when sidebar is hidden — gives map more space */}
        {activeTab === 'areas' && !filtersVisible && (
          <button
            onClick={() => setFiltersVisible(true)}
            className="hidden lg:flex fixed left-0 top-1/2 -translate-y-1/2 z-30 pl-2 pr-3 py-2 rounded-r-full bg-[#1e3a5f] text-white text-sm font-medium shadow-lg hover:bg-[#1e3a5f]/90 hover:pl-3 transition-all items-center gap-2"
            aria-label={language === 'en' ? 'Show filters' : 'फिल्टर देखाउनुहोस्'}
          >
            <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <span>{language === 'en' ? 'Filters' : 'फिल्टर'}</span>
          </button>
        )}

        {/* Sidebar with Filters — only for Election areas. On mobile the sidebar is fixed/overlay so the wrapper must not take layout space (w-0); on lg+ it reserves width when visible. */}
        {activeTab === 'areas' && (
          <div
            className={`flex-shrink-0 overflow-hidden transition-[width] duration-300 ease-out w-0 min-w-0 ${
              filtersVisible ? 'lg:w-80' : ''
            }`}
          >
            <aside
              id="filters-sidebar"
              className="fixed lg:relative h-full bg-white p-4 overflow-y-auto border-r border-[#1e3a5f]/20 shadow-xl lg:shadow-lg z-40 transition-transform duration-300 ease-out lg:translate-x-0 -translate-x-full w-[min(85vw,20rem)] lg:w-80"
            >
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-[#1e3a5f]">{language === 'en' ? 'Area filters' : 'क्षेत्र फिल्टर'}</h2>
                <div className="flex items-center gap-1">
                  {/* Desktop: hide filters to get more map space */}
                  <button
                    onClick={() => setFiltersVisible(false)}
                    className="hidden lg:flex p-2 hover:bg-[#1e3a5f]/10 rounded-lg text-[#1e3a5f]/80"
                    aria-label={language === 'en' ? 'Hide filters' : 'फिल्टर लुकाउनुहोस्'}
                    title={language === 'en' ? 'Hide filters' : 'फिल्टर लुकाउनुहोस्'}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  {/* Mobile: close drawer */}
                  <button
                    onClick={() => {
                      document.getElementById('filters-sidebar').classList.add('-translate-x-full');
                      document.getElementById('mobile-overlay').classList.add('hidden');
                    }}
                    className="lg:hidden p-2 hover:bg-[#1e3a5f]/10 rounded-lg text-[#1e3a5f]/80"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <FiltersPanel
                filters={filters}
                onFiltersChange={setFilters}
                language={language}
              />
            </aside>
          </div>
        )}

        {/* Mobile overlay — only when filters exist (Election areas tab) */}
        {activeTab === 'areas' && (
          <div
            id="mobile-overlay"
            className="lg:hidden fixed inset-0 bg-black/50 z-30 hidden"
            onClick={() => {
              document.getElementById('filters-sidebar').classList.add('-translate-x-full');
              document.getElementById('mobile-overlay').classList.add('hidden');
            }}
          />
        )}

        {/* Main Content Area — expands to full width on Insights & Compare */}
        <main className="flex-1 flex flex-col overflow-hidden min-w-0 transition-[flex-basis] duration-300 ease-out">
          {/* Breadcrumb Navigation */}
          {activeTab === 'areas' && (
            <div className="flex-none bg-white border-b border-[#1e3a5f]/20 px-2 sm:px-3 lg:px-4 py-2 lg:py-3 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 min-h-0">
              <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap min-w-0">
                <span className="text-sm text-[#1e3a5f]/70">
                  <IconMapPin className="w-4 h-4" />
                </span>
                {breadcrumb.map((item, index) => (
                  <React.Fragment key={index}>
                    {index > 0 && <span className="text-[#1e3a5f]/40 shrink-0">›</span>}
                    <button
                      onClick={() => handleBreadcrumbClick(index)}
                      className={`max-w-[100px] sm:max-w-[140px] lg:max-w-[180px] truncate px-2 lg:px-3 py-1 lg:py-1.5 rounded-full text-xs lg:text-sm font-medium transition-all text-left ${
                        index === breadcrumb.length - 1
                          ? 'bg-[#b91c1c] text-white shadow-sm'
                          : 'text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/10'
                      }`}
                      title={item.name}
                    >
                      {item.name}
                    </button>
                  </React.Fragment>
                ))}
              </div>
              
              {/* Quick level buttons */}
              <div className="flex gap-1 lg:gap-2 sm:ml-auto flex-shrink-0">
                <button
                  onClick={() => {
                    setFilters(prev => ({ ...prev, level: 'province', province: null, district: null }));
                    setBreadcrumb([{ level: 'province', name: 'Nepal' }]);
                  }}
                  className={`px-2 lg:px-3 py-1 lg:py-1.5 rounded-full text-xs font-medium transition-all ${
                    filters.level === 'province' ? 'bg-[#b91c1c] text-white' : 'bg-[#1e3a5f]/10 text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/20'
                  }`}
                  aria-current={filters.level === 'province' ? 'true' : undefined}
                  aria-label={language === 'en' ? 'View provinces' : 'प्रदेश हेर्नुहोस्'}
                >
                  {language === 'en' ? 'Provinces' : 'प्रदेश'}
                </button>
                <button
                  onClick={() => {
                    setFilters(prev => ({ ...prev, level: 'district', district: null }));
                  }}
                  className={`px-2 lg:px-3 py-1 lg:py-1.5 rounded-full text-xs font-medium transition-all ${
                    filters.level === 'district' ? 'bg-[#b91c1c] text-white' : 'bg-[#1e3a5f]/10 text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/20'
                  }`}
                  aria-current={filters.level === 'district' ? 'true' : undefined}
                  aria-label={language === 'en' ? 'View districts' : 'जिल्ला हेर्नुहोस्'}
                >
                  {language === 'en' ? 'Districts' : 'जिल्ला'}
                </button>
                <button
                  onClick={() => {
                    setFilters(prev => ({ ...prev, level: 'constituency' }));
                  }}
                  className={`px-2 lg:px-3 py-1 lg:py-1.5 rounded-full text-xs font-medium transition-all ${
                    filters.level === 'constituency' ? 'bg-[#b91c1c] text-white' : 'bg-[#1e3a5f]/10 text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/20'
                  }`}
                  aria-current={filters.level === 'constituency' ? 'true' : undefined}
                  aria-label={language === 'en' ? 'View constituencies' : 'निर्वाचन क्षेत्र हेर्नुहोस्'}
                >
                  {language === 'en' ? 'Constituencies' : 'नि.क्षे.'}
                </button>
              </div>
            </div>
          )}

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden p-2 sm:p-3 lg:p-4 min-h-0" aria-label={getViewContext(activeTab, language)?.headline ?? (language === 'en' ? 'Main content' : 'मुख्य सामग्री')}>
            {activeTab === 'areas' && (
              <div className="h-full min-h-0 flex flex-col" aria-label={language === 'en' ? 'Election areas map' : 'निर्वाचन क्षेत्र नक्शा'}>
                {loading ? (
                  <div className="flex items-center justify-center h-full bg-white rounded-xl">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-16 w-16 border-4 border-[#1e3a5f]/20 border-t-[#b91c1c] mx-auto"></div>
                      <p className="mt-6 text-[#1e3a5f] font-medium">Loading election data...</p>
                      <p className="text-sm text-[#1e3a5f]/70">कृपया प्रतीक्षा गर्नुहोस्</p>
                    </div>
                  </div>
                ) : mapData ? (
                  <MapView 
                    mapData={mapData} 
                    onFeatureClick={handleFeatureClick}
                    currentLevel={filters.level}
                    onDrillDown={handleDrillDown}
                    electionYear={filters.electionYear}
                    focusConstituency={focusConstituency}
                    onClearFocusConstituency={() => setFocusConstituency(null)}
                    language={language}
                    viewContext={getViewContext('areas', language)}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full bg-white rounded-xl text-[#1e3a5f]/70">
                    <div className="text-center">
                      <IconBallot className="w-16 h-16 mx-auto mb-4 text-[#1e3a5f]/60" />
                      <p className="text-xl font-medium text-[#1e3a5f]">{language === 'en' ? 'No map data available' : 'नक्शा डाटा उपलब्ध छैन'}</p>
                      {language === 'ne' && <p className="text-sm mt-2 text-[#1e3a5f]/60">No map data available</p>}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'insights' && (
              <div className="h-full min-h-0 bg-white rounded-xl p-3 sm:p-4 lg:p-6 border border-[#1e3a5f]/10 overflow-hidden" aria-label={language === 'en' ? 'Insights and year demographics' : 'अन्तर्दृष्टि र वर्ष जनसांख्यिकी'}>
                <InsightsDashboard language={language} viewContext={getViewContext('insights', language)} />
              </div>
            )}

            {activeTab === 'compare' && (
              <div className="h-full min-h-0 bg-white rounded-xl p-3 sm:p-4 lg:p-6 border border-[#1e3a5f]/10 overflow-auto" aria-label={language === 'en' ? 'Compare candidates' : 'उम्मेदवार तुलना गर्नुहोस्'}>
                <CandidateComparison
                  filters={filters}
                  onFiltersChange={setFilters}
                  onNavigateToElectionAreas={(constituencyDisplayName) => {
                    setFocusConstituency(constituencyDisplayName || null);
                    setActiveTab('areas');
                  }}
                  language={language}
                  viewContext={getViewContext('compare', language)}
                />
              </div>
            )}
          </div>
        </main>
      </div>

      {apiErrorMessage && (
        <div className="fixed bottom-20 left-4 right-4 sm:left-auto sm:right-4 sm:max-w-md z-50 flex items-center gap-2 px-4 py-3 bg-[#b91c1c] text-white text-sm rounded-lg shadow-lg" role="alert">
          <span className="flex-1">{apiErrorMessage}</span>
          <button type="button" onClick={() => setApiErrorMessage(null)} className="shrink-0 underline" aria-label={language === 'en' ? 'Dismiss' : 'खारेज गर्नुहोस्'}>
            {language === 'en' ? 'Dismiss' : 'खारेज'}
          </button>
        </div>
      )}

      {legalPage && (
        <LegalPage pageKey={legalPage} language={language} onClose={closeLegalPage} />
      )}

      <Footer language={language} onLegalLinkClick={handleLegalLinkClick} />
    </div>
  );
}

export default App;
