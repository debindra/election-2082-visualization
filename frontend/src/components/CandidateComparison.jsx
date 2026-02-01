import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { compareCandidates, searchCandidates } from '../services/api';
import { PartyImage } from './icons';

const DEBOUNCE_MS = 250;
const AUTOCOMPLETE_LIMIT = 5;

// Field config: English uses CSV _en columns, Nepali uses Nepali columns
function getDetailFilterFields(language) {
  const isEn = language === 'en';
  return [
    {
      key: 'party',
      label: isEn ? 'Party' : 'दल',
      getValue: (c) => (isEn ? (c.party_en ?? c.party) : c.party ?? '').trim() || null,
      getDisplayValue: (c) => (isEn ? (c.party_en ?? c.party) : c.party ?? '').trim() || null,
    },
    {
      key: 'district',
      label: isEn ? 'District' : 'जिल्ला',
      getValue: (c) => (isEn ? (c.district_en ?? c.district) : c.district ?? '').trim() || null,
      getDisplayValue: (c) => (isEn ? (c.district_en ?? c.district) : c.district ?? '').trim() || null,
    },
    {
      key: 'nirvachan_chetra',
      label: isEn ? 'Election area' : 'निर्वाचन क्षेत्र',
      getValue: (c) => (c.election_area_display ?? c.constituency ?? '').trim() || null,
      getDisplayValue: (c) => (c.election_area_display ?? c.constituency ?? '').trim() || null,
    },
    {
      key: 'province',
      label: isEn ? 'Province' : 'प्रदेश',
      getValue: (c) => (isEn ? (c.province_en ?? c.province) : (c.province_np ?? c.province ?? '')).trim() || null,
      getDisplayValue: (c) => (isEn ? (c.province_en ?? c.province) : (c.province_np ?? c.province ?? '')).trim() || null,
    },
    {
      key: 'birth_place',
      label: isEn ? 'Birth place' : 'जन्म स्थान',
      getValue: (c) => (isEn ? (c.birth_place_en ?? c.birth_district) : c.birth_district ?? '').trim() || null,
      getDisplayValue: (c) => (isEn ? (c.birth_place_en ?? c.birth_district) : c.birth_district ?? '').trim() || null,
    },
  ];
}

const CandidateComparison = ({ filters = {}, onFiltersChange, onNavigateToElectionAreas, language = 'ne', viewContext = null }) => {
  const DETAIL_FILTER_FIELDS = useMemo(() => getDetailFilterFields(language), [language]);
  const [selectedCandidates, setSelectedCandidates] = useState([]);
  const [currentTyping, setCurrentTyping] = useState('');
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [focused, setFocused] = useState(false);
  const [detailFilter, setDetailFilter] = useState({ field: '', value: '' });
  const containerRef = useRef(null);
  const skipNextSearchRef = useRef(false);

  const query = currentTyping.trim();
  const displayName = (c) => (c.candidate_name ?? c.candidate_id ?? '');

  const fetchSuggestions = useCallback(async () => {
    if (skipNextSearchRef.current) {
      skipNextSearchRef.current = false;
      setSuggestions([]);
      setSearchError(null);
      return;
    }
    if (!query || query.length < 1) {
      setSuggestions([]);
      setSearchError(null);
      return;
    }
    setSearching(true);
    setSearchError(null);
    try {
      const data = await searchCandidates(query, AUTOCOMPLETE_LIMIT);
      setSuggestions(Array.isArray(data) ? data : []);
    } catch (err) {
      setSuggestions([]);
      const msg = err.response?.data?.detail ?? err.message ?? 'Search failed';
      setSearchError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSearching(false);
    }
  }, [query]);

  useEffect(() => {
    const t = setTimeout(fetchSuggestions, DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [fetchSuggestions]);

  useEffect(() => {
    const onBlur = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.relatedTarget)) {
        setFocused(false);
      }
    };
    const el = containerRef.current;
    el?.addEventListener('focusout', onBlur);
    return () => el?.removeEventListener('focusout', onBlur);
  }, []);

  const handleCompare = async () => {
    const ids = selectedCandidates.map((c) => c.candidate_id);

    if (ids.length < 1) {
      setError('Please add at least one candidate (search and select)');
      return;
    }

    if (ids.length > 10) {
      setError('Maximum 10 candidates allowed');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await compareCandidates(ids);
      setComparisonData(data);
    } catch (err) {
      setError(err.message || 'Failed to compare candidates');
      setComparisonData(null);
    } finally {
      setLoading(false);
    }
  };

  const selectSuggestion = (c) => {
    skipNextSearchRef.current = true;
    const key = `${c.candidate_id}-${c.election_year ?? ''}`;
    if (selectedCandidates.some((s) => `${s.candidate_id}-${s.election_year ?? ''}` === key)) {
      setCurrentTyping('');
      setSuggestions([]);
      return;
    }
    setSelectedCandidates((prev) => [
      ...prev,
      {
        candidate_id: c.candidate_id,
        candidate_name: c.candidate_name ?? c.candidate_id,
        candidate_name_en: c.candidate_name_en ?? null,
        party_en: c.party_en ?? null,
        election_year: c.election_year ?? null,
      },
    ]);
    setCurrentTyping('');
    setSuggestions([]);
  };

  const removeSelected = (index) => {
    setSelectedCandidates((prev) => prev.filter((_, i) => i !== index));
  };

  const handleInputChange = (e) => {
    setCurrentTyping(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Backspace' && !currentTyping && selectedCandidates.length > 0) {
      setSelectedCandidates((prev) => prev.slice(0, -1));
    }
  };

  const showList = focused && query.length >= 1;
  const selectedKeys = new Set(selectedCandidates.map((s) => `${s.candidate_id}-${s.election_year ?? ''}`));
  const availableSuggestions = suggestions.filter(
    (c) => !selectedKeys.has(`${c.candidate_id}-${c.election_year ?? ''}`)
  );

  const filteredDetailCandidates = useMemo(() => {
    if (!comparisonData?.candidates) return [];
    const entries = Object.entries(comparisonData.candidates);
    const { field, value } = detailFilter;
    if (!field || !value) return entries;
    const config = DETAIL_FILTER_FIELDS.find((f) => f.key === field);
    if (!config) return entries;
    return entries.filter(([, c]) => config.getValue(c) === value);
  }, [comparisonData?.candidates, detailFilter, DETAIL_FILTER_FIELDS]);

  const applyDetailFilterToMain = useCallback((field, value, candidate = null) => {
    if (!onFiltersChange) return;
    const c = candidate || {};
    const isEn = language === 'en';
    if (field === 'party') {
      const filterValue = (isEn ? (c.party_en ?? c.party) : (c.party ?? c.party_en) ?? value ?? '').trim() || null;
      if (filterValue) onFiltersChange((prev) => ({ ...prev, party: filterValue }));
    } else if (field === 'district') {
      const filterValue = (isEn ? (c.district_en ?? c.district) : (c.district ?? c.district_en) ?? value ?? '').trim() || null;
      if (filterValue) onFiltersChange((prev) => ({ ...prev, district: filterValue, level: 'constituency' }));
    } else if (field === 'province') {
      const filterValue = (isEn ? (c.province_en ?? c.province) : (c.province_np ?? c.province ?? c.province_en) ?? value ?? '').trim() || null;
      if (filterValue) onFiltersChange((prev) => ({ ...prev, province: filterValue, district: null, level: 'district' }));
    } else if (field === 'nirvachan_chetra' && c) {
      const district = (isEn ? (c.district_en ?? c.district) : (c.district ?? c.district_en) ?? '').trim() || (value && String(value).split(/\s*[-–]\s*/)[0]?.trim());
      if (district) onFiltersChange((prev) => ({ ...prev, district, level: 'constituency' }));
      onNavigateToElectionAreas?.(value || null);
      return;
    } else if (field === 'birth_place') {
      const filterValue = (isEn ? (c.birth_place_en ?? c.birth_district) : (c.birth_district ?? c.birth_place_en) ?? value ?? '').trim() || null;
      if (filterValue) onFiltersChange((prev) => ({ ...prev, district: filterValue, level: 'constituency' }));
    }
    if (field !== 'nirvachan_chetra') onNavigateToElectionAreas?.();
  }, [language, onFiltersChange, onNavigateToElectionAreas]);

  const clearDetailFilterFromMain = useCallback((field) => {
    if (!onFiltersChange) return;
    if (field === 'party') {
      onFiltersChange((prev) => ({ ...prev, party: null }));
    } else if (field === 'district' || field === 'nirvachan_chetra' || field === 'birth_place') {
      onFiltersChange((prev) => ({ ...prev, district: null, level: 'district' }));
    } else if (field === 'province') {
      onFiltersChange((prev) => ({ ...prev, province: null, district: null, level: 'province' }));
    }
  }, [onFiltersChange]);

  return (
    <div className="bg-white p-3 sm:p-4 lg:p-6 rounded-xl shadow-lg border border-[#1e3a5f]/15">
      <h2 className="text-lg sm:text-xl font-bold text-[#1e3a5f] mb-3 sm:mb-4">{language === 'en' ? 'Candidate comparison' : 'उम्मेदवार तुलना'}</h2>

      <div className="mb-4" ref={containerRef}>
        {/* Selected candidates card list */}
        <div className="mb-3">
          <label className="block text-sm font-medium text-[#1e3a5f]/90 mb-2">
            Selected candidates <span className="text-xs text-[#1e3a5f]/60">(max 10 — search and add below)</span>
          </label>
          {selectedCandidates.length === 0 ? (
            <p className="text-sm text-[#1e3a5f]/70 py-3 px-4 rounded-lg border border-dashed border-[#1e3a5f]/20 bg-[#1e3a5f]/5">
              No candidates selected. Search by name (English or Nepali) and pick from the list to add.
            </p>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              {selectedCandidates.map((c, idx) => (
                <div
                  key={`${c.candidate_id}-${c.election_year ?? ''}-${idx}`}
                  className="inline-flex items-center gap-2 pl-3 pr-1 py-1.5 rounded-lg border border-[#1e3a5f]/20 bg-[#1e3a5f]/5 hover:bg-[#1e3a5f]/10 text-sm max-w-full min-w-0"
                >
                  <span className="font-medium text-[#1e3a5f] truncate min-w-0" title={displayName(c)}>{displayName(c)}</span>
                  {(language === 'en' ? (c.party_en ?? c.party) : c.party) && (
                    <span className="text-[#1e3a5f]/70 text-xs inline-flex items-center gap-1">
                      <PartyImage partyName={language === 'en' ? (c.party_en ?? c.party) : c.party} className="w-3.5 h-3.5 shrink-0" />
                      ({language === 'en' ? (c.party_en ?? c.party) : c.party})
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => removeSelected(idx)}
                    className="p-1 rounded hover:bg-[#b91c1c]/15 text-[#1e3a5f]/70 hover:text-[#b91c1c]"
                    aria-label={`Remove ${displayName(c)}`}
                  >
                    <span className="sr-only">Remove</span>×
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => setSelectedCandidates([])}
                className="text-xs px-2 py-1 rounded-md border border-[#1e3a5f]/20 text-[#1e3a5f]/70 hover:bg-[#1e3a5f]/10 hover:text-[#1e3a5f]"
              >
                Clear all
              </button>
            </div>
          )}
        </div>

        <label className="block text-sm font-medium text-[#1e3a5f]/90 mb-2">
          Search to add another
        </label>
        <div className="flex flex-col sm:flex-row gap-2 relative">
          <div className="flex-1 relative">
            <input
              type="text"
              value={currentTyping}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setFocused(true)}
              placeholder="e.g. Yogesh, Ram, क्षितिज…"
              className="w-full px-3 py-2 border border-[#1e3a5f]/25 rounded-md focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] text-[#1e3a5f]"
              autoComplete="off"
            />
            {showList && (
              <ul
                className="absolute left-0 right-0 top-full mt-1 z-50 bg-white border border-[#1e3a5f]/20 rounded-md shadow-lg overflow-hidden max-h-60 overflow-y-auto"
                role="listbox"
              >
                {searching ? (
                  <li className="px-3 py-2 text-[#1e3a5f]/70 text-sm">Searching…</li>
                ) : searchError ? (
                  <li className="px-3 py-2 text-[#b91c1c] text-sm">{searchError}</li>
                ) : availableSuggestions.length === 0 ? (
                  <li className="px-3 py-2 text-[#1e3a5f]/70 text-sm">
                    {suggestions.length === 0
                      ? 'No candidates found. Add election CSV files to data/elections to enable search.'
                      : 'All shown candidates already selected. Try a different search.'}
                  </li>
                ) : (
                  availableSuggestions.slice(0, AUTOCOMPLETE_LIMIT).map((c) => (
                    <li
                      key={`${c.candidate_id}-${c.election_year ?? ''}`}
                      role="option"
                      tabIndex={0}
                      className="px-3 py-2 hover:bg-[#1e3a5f]/5 cursor-pointer text-sm border-b border-[#1e3a5f]/10 last:border-0 focus:bg-[#1e3a5f]/5 focus:outline-none focus:ring-1 focus:ring-inset focus:ring-[#1e3a5f]"
                      onClick={() => selectSuggestion(c)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          selectSuggestion(c);
                        }
                      }}
                    >
                      <span className="font-medium text-[#1e3a5f]">{(c.candidate_name ?? c.candidate_id)}</span>
                      {(language === 'en' ? (c.party_en ?? c.party) : c.party) && (
                        <span className="text-[#1e3a5f]/70 ml-2 inline-flex items-center gap-1">
                          <PartyImage partyName={language === 'en' ? (c.party_en ?? c.party) : c.party} className="w-3.5 h-3.5 shrink-0" />
                          ({language === 'en' ? (c.party_en ?? c.party) : c.party})
                        </span>
                      )}
                      {c.election_year && <span className="text-[#1e3a5f]/50 ml-1">· {c.election_year}</span>}
                    </li>
                  ))
                )}
              </ul>
            )}
          </div>
          <button
            onClick={handleCompare}
            disabled={loading || selectedCandidates.length === 0}
            className="px-4 py-2.5 sm:py-2 min-h-[44px] sm:min-h-0 bg-[#b91c1c] text-white rounded-md hover:bg-[#b91c1c]/90 disabled:bg-[#1e3a5f]/30 disabled:cursor-not-allowed touch-manipulation"
          >
            {loading ? 'Comparing...' : 'Compare'}
          </button>
        </div>
        {error && <p className="text-[#b91c1c] text-sm mt-1">{error}</p>}
      </div>

      {comparisonData && (
        <div className="space-y-4">
          {/* Candidate Details */}
          <div className="border-t border-[#1e3a5f]/15 pt-4">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <h3 className="font-bold text-lg text-[#1e3a5f]">Candidate details</h3>
              {detailFilter.field && detailFilter.value && (
                <>
                  <span className="text-sm text-[#1e3a5f]/70">
                    <span className="font-medium text-[#1e3a5f]">
                      {DETAIL_FILTER_FIELDS.find((f) => f.key === detailFilter.field)?.label ?? detailFilter.field}:{' '}
                      {(() => {
                        const config = DETAIL_FILTER_FIELDS.find((f) => f.key === detailFilter.field);
                        const first = filteredDetailCandidates[0]?.[1];
                        const displayVal = first && config?.getDisplayValue ? config.getDisplayValue(first) : null;
                        return displayVal || detailFilter.value;
                      })()}
                    </span>
                    {' '}({filteredDetailCandidates.length} of {Object.keys(comparisonData.candidates).length})
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      clearDetailFilterFromMain(detailFilter.field);
                      setDetailFilter({ field: '', value: '' });
                    }}
                    className="text-xs px-2 py-1 rounded-md border border-[#1e3a5f]/25 text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/10"
                  >
                    {language === 'en' ? 'Clear filter' : 'फिल्टर मेट्नुहोस्'}
                  </button>
                </>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
              {filteredDetailCandidates.map(([id, candidate]) => {
                const name = candidate.candidate_name ?? `Candidate ${id}`;
                return (
                <div key={id} className="border border-[#1e3a5f]/15 rounded-lg p-3 bg-[#1e3a5f]/5 min-w-0">
                  <div className="flex items-start gap-3 mb-2 min-w-0">
                    {candidate.image_url ? (
                      <img
                        src={candidate.image_url}
                        alt={name}
                        className="w-14 h-14 rounded-full object-cover border border-[#1e3a5f]/20 shrink-0"
                      />
                    ) : (
                      <div className="w-14 h-14 rounded-full bg-[#1e3a5f]/15 border border-[#1e3a5f]/20 shrink-0 flex items-center justify-center text-[#1e3a5f]/70 text-lg font-medium" aria-hidden>
                        {(name !== `Candidate ${id}` ? name : '?').charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div className="font-bold text-[#1e3a5f] min-w-0">
                      {name}
                    </div>
                  </div>
                  <div className="space-y-1 text-sm">
                    {DETAIL_FILTER_FIELDS.map(({ key, label, getValue, getDisplayValue }) => {
                      const value = getValue(candidate);
                      if (!value) return null;
                      const displayValue = (getDisplayValue && getDisplayValue(candidate)) || value;
                      const isActive = detailFilter.field === key && detailFilter.value === value;
                      return (
                        <div key={key}>
                          <strong className="text-[#1e3a5f]/80">{label}:</strong>{' '}
                          <button
                            type="button"
                            onClick={() => {
                              if (isActive) {
                                clearDetailFilterFromMain(key);
                                setDetailFilter({ field: '', value: '' });
                              } else {
                                setDetailFilter({ field: key, value });
                                applyDetailFilterToMain(key, value, key === 'nirvachan_chetra' ? candidate : null);
                              }
                            }}
                            className={`
                              text-left font-medium rounded px-0.5 -mx-0.5 mt-0.5
                              focus:outline-none focus:ring-1 focus:ring-[#b91c1c] focus:ring-offset-1
                              ${isActive ? 'bg-[#b91c1c]/15 text-[#b91c1c] ring-1 ring-[#b91c1c]/40' : 'text-[#1e3a5f]/90 hover:bg-[#1e3a5f]/10 hover:text-[#1e3a5f] hover:underline'}
                            `}
                            title={isActive ? (language === 'en' ? 'Click to clear filter' : 'फिल्टर मेट्न क्लिक गर्नुहोस्') : (language === 'en' ? `Go to election area: ${displayValue}` : `${label}: ${displayValue} — इलेक्शन क्षेत्रमा जानुहोस्`)}
                          >
                            {displayValue}
                          </button>
                        </div>
                      );
                    })}
                    {candidate.age != null && (
                      <div><strong>{language === 'en' ? 'Age:' : 'उमेर:'}</strong> {candidate.age}</div>
                    )}
                    {candidate.gender && (
                      <div><strong>{language === 'en' ? 'Gender:' : 'लिङ्ग:'}</strong> {candidate.gender}</div>
                    )}
                    {candidate.education_level && (
                      <div><strong>{language === 'en' ? 'Education:' : 'शिक्षा:'}</strong> {candidate.education_level}</div>
                    )}
                    {candidate.election_year && (
                      <div><strong>{language === 'en' ? 'Election year:' : 'निर्वाचन वर्ष:'}</strong> {candidate.election_year}</div>
                    )}
                  </div>
                </div>
              ); })}
            </div>
          </div>
        </div>
      )}
      {viewContext?.takeaway && (
        <p className="text-sm text-[#1e3a5f]/70 mt-6 pt-4 border-t border-[#1e3a5f]/15" aria-label={language === 'en' ? 'Key takeaway' : 'मुख्य निष्कर्ष'}>
          {viewContext.takeaway}
        </p>
      )}
    </div>
  );
};

export default CandidateComparison;
