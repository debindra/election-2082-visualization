import React, { useState, useEffect, useCallback } from 'react';
import MapView from './components/MapView';
import FiltersPanel from './components/FiltersPanel';
import CandidateComparison from './components/CandidateComparison';
import InsightsDashboard from './components/InsightsDashboard';
import { getMapData, listElections } from './services/api';
import {
  IconBallot,
  IconBuildingColumns,
  IconMapPin,
  IconUsers,
} from './components/icons';

const LANG_KEY = 'election-viz-lang';

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
  const [availableElections, setAvailableElections] = useState([]);
  const [filters, setFilters] = useState({
    electionYear: null,
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
  const [breadcrumb, setBreadcrumb] = useState([{ level: 'province', name: 'Nepal' }]);
  const [focusConstituency, setFocusConstituency] = useState(null);

  useEffect(() => {
    loadElections();
  }, []);

  useEffect(() => {
    if (filters.electionYear) {
      loadMapData();
    }
  }, [filters]);

  const loadElections = async () => {
    try {
      const elections = await listElections();
      setAvailableElections(elections);
      if (elections.length > 0) {
        setFilters((prev) => ({ ...prev, electionYear: elections[0] }));
      }
    } catch (error) {
      console.error('Failed to load elections:', error);
    }
  };

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
    <div className="h-screen flex flex-col bg-gradient-to-br from-[#1e3a5f]/5 to-[#b91c1c]/5">
      {/* Header — theme: slate blue #1e3a5f, muted red #b91c1c */}
      <header className="bg-white/95 backdrop-blur border-b-2 border-[#1e3a5f] shadow-sm">
        <div className="bg-gradient-to-r from-[#b91c1c]/5 via-transparent to-[#1e3a5f]/5">
          <div className="px-4 lg:px-6 py-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <img
                  src="/Flag_of_Nepal.png"
                  alt=""
                  className="w-10 h-10 object-contain shrink-0 drop-shadow-sm"
                  aria-hidden
                />
                <div>
                  <h1 className="text-xl lg:text-2xl font-semibold tracking-tight text-[#1e3a5f]">
                    {language === 'en' ? `House of Representatives Election ${filters.electionYear || ''}` : `प्रतिनिधिसभा निर्वाचन ${filters.electionYear || ''}`}
                  </h1>
                  <p className="text-xs lg:text-sm text-[#1e3a5f]/70">
                    {language === 'en' ? 'Nepal election data, mapped and explained' : 'नेपाल प्रतिनिधिसभा निर्वाचन डाटा'}
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
              <div className="flex items-center gap-1 rounded-full bg-[#1e3a5f]/10 p-1">
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
        <div className="px-3 lg:px-6 pb-2 pt-0.5">
          <div className="inline-flex gap-1 rounded-full bg-[#1e3a5f]/10 p-1 text-xs lg:text-sm">
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
        {/* Mobile Menu Toggle */}
        <button
          onClick={() => {
            document.getElementById('filters-sidebar').classList.toggle('-translate-x-full');
            document.getElementById('mobile-overlay').classList.toggle('hidden');
          }}
          className="lg:hidden fixed top-20 left-4 z-50 p-3 bg-[#1e3a5f] text-white rounded-full shadow-lg hover:bg-[#1e3a5f]/90 transition-colors"
          aria-label="Toggle filters"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Sidebar with Filters */}
        <aside 
          id="filters-sidebar"
          className="fixed lg:relative lg:translate-x-0 -translate-x-full w-80 h-full lg:w-80 bg-white p-4 overflow-y-auto border-r border-[#1e3a5f]/20 shadow-lg z-40 transition-transform duration-300"
        >
          <div className="lg:hidden flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-[#1e3a5f]">{language === 'en' ? 'Filters' : 'फिल्टर'}</h2>
            <button
              onClick={() => {
                document.getElementById('filters-sidebar').classList.add('-translate-x-full');
                document.getElementById('mobile-overlay').classList.add('hidden');
              }}
              className="p-2 hover:bg-[#1e3a5f]/10 rounded-lg text-[#1e3a5f]/80"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <FiltersPanel
            filters={filters}
            onFiltersChange={setFilters}
            availableElections={availableElections}
            language={language}
          />
        </aside>

        {/* Mobile Overlay */}
        <div 
          id="mobile-overlay"
          className="lg:hidden fixed inset-0 bg-black/50 z-30 hidden"
          onClick={() => {
            document.getElementById('filters-sidebar').classList.add('-translate-x-full');
            document.getElementById('mobile-overlay').classList.add('hidden');
          }}
        />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden min-w-0">
          {/* Breadcrumb Navigation */}
          {activeTab === 'areas' && (
            <div className="bg-white border-b border-[#1e3a5f]/20 px-3 lg:px-4 py-2 lg:py-3 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-[#1e3a5f]/70">
                  <IconMapPin className="w-4 h-4" />
                </span>
                {breadcrumb.map((item, index) => (
                  <React.Fragment key={index}>
                    {index > 0 && <span className="text-[#1e3a5f]/40">›</span>}
                    <button
                      onClick={() => handleBreadcrumbClick(index)}
                      className={`px-2 lg:px-3 py-1 lg:py-1.5 rounded-full text-xs lg:text-sm font-medium transition-all ${
                        index === breadcrumb.length - 1
                          ? 'bg-[#b91c1c] text-white shadow-sm'
                          : 'text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/10'
                      }`}
                    >
                      {item.name.length > 15 ? item.name.substring(0, 15) + '...' : item.name}
                    </button>
                  </React.Fragment>
                ))}
              </div>
              
              {/* Quick level buttons */}
              <div className="flex gap-1 lg:gap-2 ml-auto">
                <button
                  onClick={() => {
                    setFilters(prev => ({ ...prev, level: 'province', province: null, district: null }));
                    setBreadcrumb([{ level: 'province', name: 'Nepal' }]);
                  }}
                  className={`px-2 lg:px-3 py-1 lg:py-1.5 rounded-full text-xs font-medium transition-all ${
                    filters.level === 'province' ? 'bg-[#b91c1c] text-white' : 'bg-[#1e3a5f]/10 text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/20'
                  }`}
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
                >
                  {language === 'en' ? 'Constituencies' : 'नि.क्षे.'}
                </button>
              </div>
            </div>
          )}

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden p-2 lg:p-4">
            {activeTab === 'areas' && (
              <div className="h-full">
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
                  />
                ) : (
                  <div className="flex items-center justify-center h-full bg-white rounded-xl text-[#1e3a5f]/70">
                    <div className="text-center">
                      <IconBallot className="w-16 h-16 mx-auto mb-4 text-[#1e3a5f]/60" />
                      <p className="text-xl font-medium text-[#1e3a5f]">{language === 'en' ? 'Select an election year to view data' : 'निर्वाचन वर्ष छान्नुहोस्'}</p>
                      {language === 'ne' && <p className="text-sm mt-2 text-[#1e3a5f]/60">Select an election year to view data</p>}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'insights' && (
              <div className="h-full bg-white rounded-xl p-4 lg:p-6 border border-[#1e3a5f]/10">
                <InsightsDashboard language={language} />
              </div>
            )}

            {activeTab === 'compare' && (
              <div className="h-full bg-white rounded-xl p-6 border border-[#1e3a5f]/10">
                <CandidateComparison
                  filters={filters}
                  onFiltersChange={setFilters}
                  onNavigateToElectionAreas={(constituencyDisplayName) => {
                    setFocusConstituency(constituencyDisplayName || null);
                    setActiveTab('areas');
                  }}
                  language={language}
                />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
