import React, { useState, useMemo } from 'react';

/**
 * PollingCentersList Component
 * Displays polling centers in a structured, visually appealing card-based layout
 * Used within ChatBot to show polling center query results
 */
const PollingCentersList = ({ centers, summary, language = 'ne' }) => {
  const [filterText, setFilterText] = useState('');
  const [expandedCenter, setExpandedCenter] = useState(null);
  const [sortBy, setSortBy] = useState('name'); // name, voters, code

  if (!centers || centers.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <p className="text-sm text-gray-500 font-medium">
          {language === 'ne' ? 'कुनै मतदान केन्द्र फेला परेन' : 'No polling centers found'}
        </p>
      </div>
    );
  }

  // Filter and sort centers
  const filteredCenters = useMemo(() => {
    let result = [...centers];
    
    // Filter
    if (filterText.trim()) {
      const search = filterText.toLowerCase();
      result = result.filter(center => {
        return (
          center.district?.toLowerCase().includes(search) ||
          center.palika_name?.toLowerCase().includes(search) ||
          center.center_name?.toLowerCase().includes(search) ||
          center.polling_center_name?.toLowerCase().includes(search) ||
          String(center.polling_center_code)?.includes(search) ||
          String(center.area_no)?.includes(search)
        );
      });
    }
    
    // Sort
    result.sort((a, b) => {
      if (sortBy === 'voters') {
        return (b.voter_count || 0) - (a.voter_count || 0);
      } else if (sortBy === 'code') {
        return String(a.polling_center_code || '').localeCompare(String(b.polling_center_code || ''));
      } else {
        return (a.center_name || a.polling_center_name || a.palika_name || '').localeCompare(b.center_name || b.polling_center_name || b.palika_name || '');
      }
    });
    
    return result;
  }, [centers, filterText, sortBy]);

  const toggleExpand = (centerId) => {
    setExpandedCenter(expandedCenter === centerId ? null : centerId);
  };

  const getGenderRatioColor = (ratio) => {
    if (ratio > 1.2) return 'text-blue-600';
    if (ratio < 0.8) return 'text-pink-600';
    return 'text-gray-600';
  };

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      {summary && (
        <div className="bg-gradient-to-br from-[#1e3a5f] via-[#2c4a6e] to-[#1e3a5f] text-white rounded-2xl p-5 shadow-lg relative overflow-hidden">
          {/* Decorative background pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-white rounded-full translate-y-1/2 -translate-x-1/2" />
          </div>
          
          <div className="relative">
            <h3 className="text-sm font-medium text-white/80 mb-4">
              {language === 'ne' ? 'समरी' : 'Summary'}
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="bg-white/10 backdrop-blur rounded-xl p-3">
                <div className="text-2xl font-bold">{summary.total_centers?.toLocaleString()}</div>
                <div className="text-xs text-white/80 mt-1">
                  {language === 'ne' ? 'कुल केन्द्र' : 'Total Centers'}
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-xl p-3">
                <div className="text-2xl font-bold">{summary.total_voters?.toLocaleString()}</div>
                <div className="text-xs text-white/80 mt-1">
                  {language === 'ne' ? 'कुल मतदाता' : 'Total Voters'}
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-xl p-3">
                <div className="text-2xl font-bold text-blue-200">{summary.male_voters?.toLocaleString()}</div>
                <div className="text-xs text-white/80 mt-1">
                  {language === 'ne' ? 'पुरुष मतदाता' : 'Male Voters'}
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-xl p-3">
                <div className="text-2xl font-bold text-pink-200">{summary.female_voters?.toLocaleString()}</div>
                <div className="text-xs text-white/80 mt-1">
                  {language === 'ne' ? 'महिला मतदाता' : 'Female Voters'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="space-y-3">
        {/* Search Input */}
        {centers.length > 5 && (
          <div className="relative">
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder={
                language === 'ne' 
                  ? 'मतदान केन्द्र खोज्नुहोस्...' 
                  : 'Search polling centers...'
              }
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1e3a5f]/20 focus:border-[#1e3a5f] transition-all text-sm"
            />
            <svg 
              className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 11 14m0 0v8" />
            </svg>
            {filterText && (
              <button
                type="button"
                onClick={() => setFilterText('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* Sort Dropdown */}
        {centers.length > 1 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              {language === 'ne' ? 'क्रमबद्ध' : 'Sort by:'}
            </span>
            <div className="flex gap-1">
              {[
                { value: 'name', label: { ne: 'नाम', en: 'Name' } },
                { value: 'voters', label: { ne: 'मतदाता', en: 'Voters' } },
                { value: 'code', label: { ne: 'कोड', en: 'Code' } },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSortBy(option.value)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                    sortBy === option.value
                      ? 'bg-[#1e3a5f] text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {option.label[language]}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Centers List */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto">
        {filteredCenters.map((center, idx) => (
          <div
            key={idx}
            className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden group"
          >
            {/* Header - Always Visible */}
            <div
              className="px-4 py-3.5 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => toggleExpand(idx)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2.5 mb-1">
                  <span className="flex-shrink-0 px-2 py-0.5 text-xs font-semibold text-white bg-gradient-to-r from-[#1e3a5f] to-[#2c4a6e] rounded-md">
                    {center.area_no || '-'}
                  </span>
                  <span className="font-bold text-gray-800 truncate text-sm">
                    {center.center_name || center.polling_center_name || center.palika_name}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <span className="truncate">{center.district}</span>
                  <span className="text-gray-300">•</span>
                  <span className="truncate">{center.palika_name}</span>
                  {center.palika_type && (
                    <>
                      <span className="text-gray-300">•</span>
                      <span className="text-xs text-gray-500">{center.palika_type}</span>
                    </>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 ml-2 flex-shrink-0">
                {/* Voter count badge */}
                <div className="text-right">
                  <div className="text-xs font-semibold text-[#1e3a5f]">
                    {(center.voter_count || 0).toLocaleString()}
                  </div>
                  <div className="text-[10px] text-gray-500">
                    {language === 'ne' ? 'मतदाता' : 'Voters'}
                  </div>
                </div>
                <svg
                  className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
                    expandedCenter === idx ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedCenter === idx && (
              <div className="px-4 pb-4 pt-3 border-t border-gray-200/50 bg-gray-50/50 animate-fadeIn">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Voter Counts */}
                  <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
                    <h4 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      {language === 'ne' ? 'मतदाता संख्या' : 'Voter Counts'}
                    </h4>
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
                        <span className="text-sm text-gray-600">
                          {language === 'ne' ? 'कुल' : 'Total'}
                        </span>
                        <span className="font-semibold text-gray-800">
                          {(center.voter_count || 0).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
                        <span className="text-sm text-gray-600">
                          {language === 'ne' ? 'पुरुष' : 'Male'}
                        </span>
                        <span className="font-semibold text-blue-600">
                          {(center.male_voters || 0).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
                        <span className="text-sm text-gray-600">
                          {language === 'ne' ? 'महिला' : 'Female'}
                        </span>
                        <span className="font-semibold text-pink-600">
                          {(center.female_voters || 0).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5">
                        <span className="text-sm text-gray-600">
                          {language === 'ne' ? 'अन्य' : 'Other'}
                        </span>
                        <span className="font-semibold text-gray-600">
                          {Math.max(0, (center.voter_count || 0) - (center.male_voters || 0) - (center.female_voters || 0)).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Location Info */}
                  <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
                    <h4 className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {language === 'ne' ? 'स्थान जानकारी' : 'Location Info'}
                    </h4>
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
                        <span className="text-sm text-gray-600">
                          {language === 'ne' ? 'वार्ड नं.' : 'Ward No.'}
                        </span>
                        <span className="font-semibold text-gray-800">
                          {center.ward_no || '-'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5 border-b border-gray-100">
                        <span className="text-sm text-gray-600">
                          {language === 'ne' ? 'केन्द्र कोड' : 'Center Code'}
                        </span>
                        <span className="font-mono font-semibold text-[#1e3a5f] bg-[#1e3a5f]/5 px-2 py-0.5 rounded">
                          {center.polling_center_code || '-'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between py-1.5">
                        <span className="text-sm text-gray-600">
                          {language === 'ne' ? 'क्षेत्र' : 'Area'}
                        </span>
                        <span className="font-semibold text-gray-800">
                          {center.area_no || '-'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Showing count */}
      {filteredCenters.length !== centers.length && (
        <div className="text-center py-3 px-4 bg-gray-50 rounded-lg border border-gray-100">
          <span className="text-xs text-gray-500">
            {language === 'ne' 
              ? `${filteredCenters.length} मध्य ${centers.length} केन्द्र मध्य देखाइयो`
              : `Showing ${filteredCenters.length} of ${centers.length} centers`
            }
          </span>
          <button
            onClick={() => setFilterText('')}
            className="ml-2 text-xs text-[#1e3a5f] hover:text-[#b91c1c] font-medium underline"
          >
            {language === 'ne' ? 'सबै देखाउनुहोस्' : 'Show all'}
          </button>
        </div>
      )}
    </div>
  );
};

export default PollingCentersList;
