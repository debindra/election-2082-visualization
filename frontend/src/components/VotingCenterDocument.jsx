import React, { useState, useMemo } from 'react';

/**
 * VotingCenterDocument Component
 * Displays voting centers in traditional Nepali election list format:
 * 
 * {Index Number}: Palika Name (Nepali)
 * {#}. Sub-center   | Total voter
 *       serial Number
 */

const VotingCenterDocument = ({ 
  centers = [], 
  language = 'ne',
  title,
  subtitle,
  showFilters = true
}) => {
  const [filterText, setFilterText] = useState('');
  const [sortBy, setSortBy] = useState('palika'); // palika, voters, code
  const [expandedPalikas, setExpandedPalikas] = useState(new Set());

  // Group centers by palika
  const groupedCenters = useMemo(() => {
    let result = centers.reduce((acc, center, idx) => {
      const palikaName = center.palika_name || 'Unknown';
      if (!acc[palikaName]) {
        acc[palikaName] = {
          palikaName,
          district: center.district,
          palikaType: center.palika_type,
          centers: []
        };
      }
      acc[palikaName].centers.push({ ...center, originalIndex: idx });
      return acc;
    }, {});

    return Object.values(result);
  }, [centers]);

  // Filter and sort palikas
  const filteredGroupedCenters = useMemo(() => {
    let result = [...groupedCenters];
    
    // Filter
    if (filterText.trim()) {
      const search = filterText.toLowerCase();
      result = result.filter(group => {
        return (
          group.palikaName?.toLowerCase().includes(search) ||
          group.district?.toLowerCase().includes(search) ||
          group.centers.some(center =>
            center.center_name?.toLowerCase().includes(search) ||
            center.polling_center_name?.toLowerCase().includes(search) ||
            String(center.polling_center_code)?.includes(search)
          )
        );
      });
    }
    
    // Sort
    result.sort((a, b) => {
      if (sortBy === 'voters') {
        const aVoters = a.centers.reduce((sum, c) => sum + (c.voter_count || 0), 0);
        const bVoters = b.centers.reduce((sum, c) => sum + (c.voter_count || 0), 0);
        return bVoters - aVoters;
      } else if (sortBy === 'code') {
        const aCode = a.centers[0]?.polling_center_code || '';
        const bCode = b.centers[0]?.polling_center_code || '';
        return String(aCode).localeCompare(String(bCode));
      } else {
        return (a.palikaName || '').localeCompare(b.palikaName || '', 'ne');
      }
    });
    
    return result;
  }, [groupedCenters, filterText, sortBy]);

  const toggleExpand = (palikaName) => {
    setExpandedPalikas(prev => {
      const newSet = new Set(prev);
      if (newSet.has(palikaName)) {
        newSet.delete(palikaName);
      } else {
        newSet.add(palikaName);
      }
      return newSet;
    });
  };

  // Calculate total voters
  const totalVoters = centers.reduce((sum, center) => sum + (center.voter_count || 0), 0);
  const maleVoters = centers.reduce((sum, center) => sum + (center.male_voters || 0), 0);
  const femaleVoters = centers.reduce((sum, center) => sum + (center.female_voters || 0), 0);

  if (!centers || centers.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <p className="text-sm text-gray-500 font-medium">
          {language === 'ne' ? 'कुनै मतदान केन्द्र फेला परेन' : 'No voting centers found'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Header */}
      <div className="bg-gradient-to-br from-[#1e3a5f] via-[#2c4a6e] to-[#1e3a5f] text-white rounded-2xl p-5 shadow-lg relative overflow-hidden">
        {/* Decorative background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-white rounded-full translate-y-1/2 -translate-x-1/2" />
        </div>
        
        <div className="relative">
          {title && (
            <h2 className="text-xl font-bold mb-1">{title}</h2>
          )}
          {subtitle && (
            <p className="text-sm text-white/80 mb-3">{subtitle}</p>
          )}
          
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white/10 backdrop-blur rounded-xl p-3">
              <div className="text-2xl font-bold">{centers.length.toLocaleString()}</div>
              <div className="text-xs text-white/80 mt-1">
                {language === 'ne' ? 'कुल केन्द्र' : 'Total Centers'}
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-xl p-3">
              <div className="text-2xl font-bold">{totalVoters.toLocaleString()}</div>
              <div className="text-xs text-white/80 mt-1">
                {language === 'ne' ? 'कुल मतदाता' : 'Total Voters'}
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-xl p-3">
              <div className="text-2xl font-bold text-blue-200">{maleVoters.toLocaleString()}</div>
              <div className="text-xs text-white/80 mt-1">
                {language === 'ne' ? 'पुरुष मतदाता' : 'Male Voters'}
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-xl p-3">
              <div className="text-2xl font-bold text-pink-200">{femaleVoters.toLocaleString()}</div>
              <div className="text-xs text-white/80 mt-1">
                {language === 'ne' ? 'महिला मतदाता' : 'Female Voters'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      {showFilters && centers.length > 3 && (
        <div className="space-y-3">
          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder={
                language === 'ne' 
                  ? 'पालिका वा केन्द्र खोज्नुहोस्...' 
                  : 'Search palika or centers...'
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

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              {language === 'ne' ? 'क्रमबद्ध:' : 'Sort by:'}
            </span>
            <div className="flex gap-1 flex-wrap">
              {[
                { value: 'palika', label: { ne: 'पालिका', en: 'Palika' } },
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
        </div>
      )}

      {/* Palika List - Traditional Document Format */}
      <div className="space-y-3">
        {filteredGroupedCenters.map((group, groupIdx) => {
          const palikaVoters = group.centers.reduce((sum, c) => sum + (c.voter_count || 0), 0);
          const isExpanded = expandedPalikas.has(group.palikaName);
          
          return (
            <div
              key={group.palikaName}
              className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
            >
              {/* Palika Header - Always Visible */}
              <div
                className="px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleExpand(group.palikaName)}
              >
                {/* Index Number and Palika Name */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    <span className="flex-shrink-0 px-2 py-0.5 text-sm font-bold text-white bg-gradient-to-r from-[#1e3a5f] to-[#2c4a6e] rounded-md">
                      {groupIdx + 1}:
                    </span>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-800 text-base mb-1 truncate">
                        {group.palikaName}
                      </h3>
                      <div className="flex items-center gap-2 text-xs text-gray-600">
                        <span className="truncate">{group.district}</span>
                        {group.palikaType && (
                          <>
                            <span className="text-gray-300">•</span>
                            <span className="text-gray-500">{group.palikaType}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 ml-2 flex-shrink-0">
                    {/* Voter count badge */}
                    <div className="text-right">
                      <div className="text-sm font-semibold text-[#1e3a5f]">
                        {palikaVoters.toLocaleString()}
                      </div>
                      <div className="text-[10px] text-gray-500">
                        {language === 'ne' ? 'मतदाता' : 'Voters'}
                      </div>
                    </div>
                    <svg
                      className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
                        isExpanded ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Expanded Sub-centers List */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-2 border-t border-gray-200/50 bg-gray-50/50">
                  <div className="space-y-2">
                    {group.centers.map((center, centerIdx) => (
                      <div
                        key={center.polling_center_code || centerIdx}
                        className="bg-white rounded-lg p-3 border border-gray-100"
                      >
                        {/* Sub-center Header */}
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 text-xs font-semibold text-[#1e3a5f] bg-[#1e3a5f]/10 rounded-md">
                              {centerIdx + 1}.
                            </span>
                            <span className="text-sm font-bold text-gray-800">
                              {center.center_name || center.polling_center_name || language === 'ne' ? 'मतदान केन्द्र' : 'Polling Center'}
                            </span>
                          </div>
                          <div className="text-sm font-semibold text-[#1e3a5f]">
                            {(center.voter_count || 0).toLocaleString()}
                          </div>
                        </div>

                        {/* Serial Number and Details */}
                        <div className="ml-6 mt-2 space-y-1">
                          {/* Serial Number Row */}
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-500">
                              {language === 'ne' ? 'सिरियल नम्बर:' : 'Serial No:'}
                            </span>
                            <span className="font-mono font-medium text-[#1e3a5f] bg-[#1e3a5f]/5 px-2 py-0.5 rounded">
                              {center.polling_center_code || '-'}
                            </span>
                          </div>

                          {/* Additional Details Row */}
                          <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                            {center.ward_no && (
                              <div>
                                <span className="text-gray-500">
                                  {language === 'ne' ? 'वार्ड नं.:' : 'Ward:'}
                                </span>
                                <span className="ml-1">{center.ward_no}</span>
                              </div>
                            )}
                            {center.area_no && (
                              <div>
                                <span className="text-gray-500">
                                  {language === 'ne' ? 'क्षेत्र:' : 'Area:'}
                                </span>
                                <span className="ml-1">{center.area_no}</span>
                              </div>
                            )}
                          </div>

                          {/* Gender Breakdown */}
                          {(center.male_voters || center.female_voters) && (
                            <div className="flex items-center gap-3 text-xs pt-2 border-t border-gray-50">
                              <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                                {language === 'ne' ? 'पुरुष:' : 'Male:'}
                                <span className="font-medium text-gray-700">
                                  {(center.male_voters || 0).toLocaleString()}
                                </span>
                              </span>
                              <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-pink-500"></span>
                                {language === 'ne' ? 'महिला:' : 'Female:'}
                                <span className="font-medium text-gray-700">
                                  {(center.female_voters || 0).toLocaleString()}
                                </span>
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Showing count */}
      {filteredGroupedCenters.length !== groupedCenters.length && (
        <div className="text-center py-3 px-4 bg-gray-50 rounded-lg border border-gray-100">
          <span className="text-xs text-gray-500">
            {language === 'ne' 
              ? `${filteredGroupedCenters.length} मध्य ${groupedCenters.length} पालिका मध्य देखाइयो`
              : `Showing ${filteredGroupedCenters.length} of ${groupedCenters.length} palikas`
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

export default VotingCenterDocument;
