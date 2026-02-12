import React, { useState, useMemo } from 'react';
import { PartyImage, ElectionSymbolImage } from './icons';

/**
 * CandidateListDisplay Component
 * Displays candidates in traditional Nepali election list format:
 * 
 * {Index Number}. Candidate Name(Nepali)
 * Party Name(Nepali)
 * Symbol(Nepali)
 * Age | Academic
 */

const CandidateListDisplay = ({ 
  candidates = [], 
  language = 'ne',
  title,
  subtitle,
  showFilters = true
}) => {
  const [filterText, setFilterText] = useState('');
  const [sortBy, setSortBy] = useState('index'); // index, name, age, party
  const [expandedCandidates, setExpandedCandidates] = useState(new Set());

  // Filter and sort candidates
  const filteredCandidates = useMemo(() => {
    let result = [...candidates];
    
    // Filter
    if (filterText.trim()) {
      const search = filterText.toLowerCase();
      result = result.filter(candidate => {
        return (
          candidate.candidate_name?.toLowerCase().includes(search) ||
          candidate.party?.toLowerCase().includes(search) ||
          candidate.election_symbol?.toLowerCase().includes(search) ||
          candidate.district?.toLowerCase().includes(search) ||
          candidate.constituency?.toLowerCase().includes(search)
        );
      });
    }
    
    // Sort
    result.sort((a, b) => {
      if (sortBy === 'name') {
        return (a.candidate_name || '').localeCompare(b.candidate_name || '', 'ne');
      } else if (sortBy === 'age') {
        return (a.age || 0) - (b.age || 0);
      } else if (sortBy === 'party') {
        return (a.party || '').localeCompare(b.party || '', 'ne');
      } else {
        // Default: index/candidate_id
        return (a.candidate_id || 0) - (b.candidate_id || 0);
      }
    });
    
    return result;
  }, [candidates, filterText, sortBy]);

  const toggleExpand = (index) => {
    setExpandedCandidates(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  if (!candidates || candidates.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <p className="text-sm text-gray-500 font-medium">
          {language === 'ne' ? 'कुनै उम्मेदवार फेला परेन' : 'No candidates found'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      {(title || subtitle) && (
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
              <p className="text-sm text-white/80">{subtitle}</p>
            )}
            {candidates.length > 0 && (
              <div className="mt-3 inline-block px-3 py-1 bg-white/10 backdrop-blur rounded-full text-xs">
                {language === 'ne' 
                  ? `कुल ${candidates.length} उम्मेदवार` 
                  : `Total ${candidates.length} candidates`
                }
              </div>
            )}
          </div>
        </div>
      )}

      {/* Controls */}
      {showFilters && candidates.length > 3 && (
        <div className="space-y-3">
          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder={
                language === 'ne' 
                  ? 'उम्मेदवार खोज्नुहोस्...' 
                  : 'Search candidates...'
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
                { value: 'index', label: { ne: 'क्र.सं.', en: 'Index' } },
                { value: 'name', label: { ne: 'नाम', en: 'Name' } },
                { value: 'party', label: { ne: 'दल', en: 'Party' } },
                { value: 'age', label: { ne: 'उमेर', en: 'Age' } },
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

      {/* Candidates List - Traditional Election Format */}
      <div className="space-y-3">
        {filteredCandidates.map((candidate, idx) => (
          <div
            key={candidate.candidate_id || idx}
            className={`bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 ${
              expandedCandidates.has(idx) ? 'ring-2 ring-[#1e3a5f]/20' : ''
            }`}
          >
            {/* Traditional Format Display */}
            <div className="p-4">
              {/* Index Number */}
              <div className="flex items-baseline gap-2 mb-2">
                <span className="flex-shrink-0 px-2.5 py-0.5 text-sm font-bold text-white bg-gradient-to-r from-[#1e3a5f] to-[#2c4a6e] rounded-md">
                  {candidate.candidate_id || idx + 1}.
                </span>
              </div>

              {/* Candidate Name */}
              <div className="mb-1">
                <span className="text-base font-bold text-gray-800">
                  {candidate.candidate_name || `Candidate ${idx + 1}`}
                </span>
              </div>

              {/* Party Name */}
              <div className="mb-2">
                <span className="text-sm text-gray-700">
                  {candidate.party || ''}{candidate.election_symbol ? ` (${candidate.election_symbol})` : ''}
                </span>
              </div>

              {/* Symbol */}
              <div className="flex items-center gap-2 mb-3">
                <div className="w-10 h-10 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-100">
                  <ElectionSymbolImage 
                    symbolName={candidate.election_symbol} 
                    className="w-8 h-8 object-contain"
                  />
                  {!candidate.election_symbol && (
                    <PartyImage 
                      partyName={candidate.party} 
                      className="w-8 h-8 object-contain"
                    />
                  )}
                </div>
                <span className="text-sm text-gray-600">
                  {candidate.election_symbol || candidate.party || ''}
                </span>
              </div>

              {/* Age | Academic */}
              <div className="flex items-center gap-3 pt-2 border-t border-gray-100">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-500">
                    {language === 'ne' ? 'उमेर:' : 'Age:'}
                  </span>
                  <span className="font-medium text-gray-800">
                    {candidate.age || '-'}
                  </span>
                </div>
                <div className="text-gray-300">|</div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-500">
                    {language === 'ne' ? 'शिक्षा:' : 'Education:'}
                  </span>
                  <span className="font-medium text-gray-800">
                    {candidate.education_level || candidate.education || '-'}
                  </span>
                </div>
              </div>

              {/* Expand button for more details */}
              <button
                onClick={() => toggleExpand(idx)}
                className="mt-3 w-full py-2 text-xs text-[#1e3a5f] hover:text-[#b91c1c] flex items-center justify-center gap-1 transition-colors"
              >
                {language === 'ne' ? 'विस्तृत जानकारी' : 'More details'}
                <svg 
                  className={`w-4 h-4 transition-transform ${
                    expandedCandidates.has(idx) ? 'rotate-180' : ''
                  }`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>

            {/* Expanded Details */}
            {expandedCandidates.has(idx) && (
              <div className="px-4 pb-4 pt-2 border-t border-gray-200/50 bg-gray-50/50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Election Area */}
                  {candidate.constituency && (
                    <div className="bg-white rounded-lg p-3 border border-gray-100">
                      <div className="text-xs text-gray-500 mb-1">
                        {language === 'ne' ? 'निर्वाचन क्षेत्र' : 'Election Area'}
                      </div>
                      <div className="text-sm font-medium text-gray-800">
                        {candidate.constituency}
                      </div>
                    </div>
                  )}

                  {/* District */}
                  {candidate.district && (
                    <div className="bg-white rounded-lg p-3 border border-gray-100">
                      <div className="text-xs text-gray-500 mb-1">
                        {language === 'ne' ? 'जिल्ला' : 'District'}
                      </div>
                      <div className="text-sm font-medium text-gray-800">
                        {candidate.district}
                      </div>
                    </div>
                  )}

                  {/* Province */}
                  {(candidate.province || candidate.province_np) && (
                    <div className="bg-white rounded-lg p-3 border border-gray-100">
                      <div className="text-xs text-gray-500 mb-1">
                        {language === 'ne' ? 'प्रदेश' : 'Province'}
                      </div>
                      <div className="text-sm font-medium text-gray-800">
                        {candidate.province_np || candidate.province}
                      </div>
                    </div>
                  )}

                  {/* Election Year */}
                  {candidate.election_year && (
                    <div className="bg-white rounded-lg p-3 border border-gray-100">
                      <div className="text-xs text-gray-500 mb-1">
                        {language === 'ne' ? 'निर्वाचन वर्ष' : 'Election Year'}
                      </div>
                      <div className="text-sm font-medium text-gray-800">
                        {candidate.election_year}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Showing count */}
      {filteredCandidates.length !== candidates.length && (
        <div className="text-center py-3 px-4 bg-gray-50 rounded-lg border border-gray-100">
          <span className="text-xs text-gray-500">
            {language === 'ne' 
              ? `${filteredCandidates.length} मध्य ${candidates.length} उम्मेदवार मध्य देखाइयो`
              : `Showing ${filteredCandidates.length} of ${candidates.length} candidates`
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

export default CandidateListDisplay;
