import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  IconBallot,
  IconBuildingColumns,
  IconChartBar,
  IconMapPin,
  IconClose,
  ElectionSymbolImage,
  PartyImage,
} from './icons';
import { compareCandidates } from '../services/api';

/** Parse gender distribution from feature props (handles object and JSON string). Returns { M, F, total, femalePct } or null. */
function getGenderFromProps(props) {
  const raw = props?.gender_distribution;
  if (!raw) return null;
  const dist = typeof raw === 'string' ? (() => { try { return JSON.parse(raw); } catch { return {}; } })() : raw;
  const M = Number(dist.M ?? dist.Male ?? 0) || 0;
  const F = Number(dist.F ?? dist.Female ?? 0) || 0;
  const total = M + F;
  if (total === 0) return null;
  const femalePct = Math.round((F / total) * 1000) / 10;
  return { M, F, total, femalePct };
}

/**
 * Interactive Election Visualization Component
 * 
 * Displays election data in a card-based grid layout similar to election.onlinekhabar.com
 * Supports drill-down from Province → District → Election Area
 */
const MapView = ({ mapData, onFeatureClick, currentLevel, onDrillDown, electionYear, focusConstituency, onClearFocusConstituency, language = 'ne', viewContext = null }) => {
  const [selectedItem, setSelectedItem] = useState(null);
  const [candidateDetails, setCandidateDetails] = useState(null);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [candidatesError, setCandidatesError] = useState(null);
  const [candidatesJustLoaded, setCandidatesJustLoaded] = useState(false);
  // Filter for candidate list in selected card: { field: 'party'|'district'|..., value: selected value }
  const [candidateListFilter, setCandidateListFilter] = useState({ field: '', value: '' });
  const detailPanelRef = useRef(null);

  // Parse constituency number from display name (e.g. "सुनसरी - ४" → 4, "सुनसरी - १" → 1)
  const DEVANAGARI_TO_NUM = { '०': 0, '१': 1, '२': 2, '३': 3, '४': 4, '५': 5, '६': 6, '७': 7, '८': 8, '९': 9 };
  const getConstituencyNumber = (displayName) => {
    const name = String(displayName || '').trim();
    const match = name.match(/\s*[-–—]\s*([०१२३४५६७८९\d]+)\s*$/);
    if (!match) return 0;
    const part = match[1];
    if (/^\d+$/.test(part)) return parseInt(part, 10);
    return part.split('').reduce((n, c) => n * 10 + (DEVANAGARI_TO_NUM[c] ?? 0), 0);
  };

  // Map province names to fixed order: Koshi, Madhesh, Bagmati, Gandaki, Lumbini, Karnali, Sudurpashchim
  const provinceOrderRank = useMemo(() => {
    const rank = {};
    const order = ['Koshi', 'Madhesh', 'Bagmati', 'Gandaki', 'Lumbini', 'Karnali', 'Sudurpashchim'];
    order.forEach((name, i) => { rank[name.toLowerCase()] = i; });
    rank['sudurpachim'] = 6;
    ['कोशी', 'मधेश', 'बागमती', 'गण्डकी', 'लुम्बिनी', 'कर्णाली', 'सुदूरपश्चिम'].forEach((name, i) => {
      rank[name] = i;
    });
    return rank;
  }, []);
  const getProvinceSortKeyStable = (name) => {
    const s = String(name || '').trim();
    const lower = s.toLowerCase();
    if (provinceOrderRank[lower] !== undefined) return provinceOrderRank[lower];
    for (const [key, idx] of Object.entries(provinceOrderRank)) {
      if (s.includes(key) || (key.length > 2 && lower.includes(key))) return idx;
    }
    return 99;
  };

  // Process and sort features: province = fixed order; constituency = by constituency number; district = by candidate count
  const features = useMemo(() => {
    if (!mapData?.features) return [];
    const list = [...mapData.features];
    if (currentLevel === 'constituency') {
      return list.sort((a, b) => {
        const numA = getConstituencyNumber(a.properties.display_name || a.properties.name);
        const numB = getConstituencyNumber(b.properties.display_name || b.properties.name);
        return numA - numB;
      });
    }
    if (currentLevel === 'province') {
      return list.sort((a, b) => {
        const nameA = a.properties.display_name || a.properties.name || '';
        const nameB = b.properties.display_name || b.properties.name || '';
        return getProvinceSortKeyStable(nameA) - getProvinceSortKeyStable(nameB);
      });
    }
    return list.sort((a, b) =>
      (b.properties.total_candidates || 0) - (a.properties.total_candidates || 0)
    );
  }, [mapData, currentLevel, provinceOrderRank]);

  // Count independents for a feature: use independent_count when set, else from party_distribution (exact स्वतन्त्र / independent)
  const getIndependentCount = (props) => {
    if (props.independent_count != null && props.independent_count > 0) return props.independent_count;
    const dist = props.party_distribution;
    if (!dist) return 0;
    const parsed = typeof dist === 'string' ? (() => { try { return JSON.parse(dist); } catch { return {}; } })() : dist;
    return Object.entries(parsed).reduce((sum, [party, count]) => {
      const p = (party || '').trim();
      const lower = p.toLowerCase();

      // Only treat true independents as स्वतन्त्र: exact Nepali labels or exact English "independent"
      const isIndependentParty =
        p === 'स्वतन्त्र' ||
        p === 'स्वतंत्र' ||
        lower === 'independent' ||
        lower === 'independent candidate' ||
        lower === 'independent (no party)';

      if (!isIndependentParty) return sum;
      return sum + (Number(count) || 0);
    }, 0);
  };

  // Calculate summary stats
  const stats = useMemo(() => {
    if (!features.length) return null;
    
    const totalCandidates = features.reduce((sum, f) => sum + (f.properties.total_candidates || 0), 0);
    const totalParties = new Set(features.flatMap(f => {
      const dist = f.properties.party_distribution;
      return dist ? Object.keys(typeof dist === 'string' ? JSON.parse(dist) : dist) : [];
    })).size;
    const totalIndependents = features.reduce((sum, f) => sum + getIndependentCount(f.properties), 0);
    const totalIndependentsPercentage =
      totalCandidates > 0 ? Math.round((totalIndependents / totalCandidates) * 1000) / 10 : 0;
    const avgAge = features.reduce((sum, f) => sum + (f.properties.average_age || 0), 0) / features.filter(f => f.properties.average_age).length;
    const genderAgg = features.reduce(
      (acc, f) => {
        const g = getGenderFromProps(f.properties);
        if (g) {
          acc.totalFemale += g.F;
          acc.totalWithGender += g.total;
        }
        return acc;
      },
      { totalFemale: 0, totalWithGender: 0 }
    );
    const femalePercentage =
      genderAgg.totalWithGender > 0
        ? Math.round((genderAgg.totalFemale / genderAgg.totalWithGender) * 1000) / 10
        : null;

    return {
      totalCandidates,
      totalParties,
      totalIndependents,
      totalIndependentsPercentage,
      avgAge: avgAge || 0,
      totalFemale: genderAgg.totalFemale,
      totalWithGender: genderAgg.totalWithGender,
      femalePercentage,
    };
  }, [features]);

  // Get level label (English / Nepali)
  const getLevelInfo = () => {
    const isEn = language === 'en';
    switch (currentLevel) {
      case 'province':
        return { label: isEn ? 'Provinces' : 'प्रदेश', sublabel: isEn ? 'Provinces' : 'प्रदेश', icon: IconBuildingColumns, count: 7 };
      case 'district':
        return { label: isEn ? 'Districts' : 'जिल्ला', sublabel: isEn ? 'Districts' : 'जिल्ला', icon: IconMapPin, count: 77 };
      case 'constituency':
        return { label: isEn ? 'Election areas' : 'निर्वाचन क्षेत्र', sublabel: isEn ? 'Election areas' : 'निर्वाचन क्षेत्र', icon: IconBallot, count: 165 };
      default:
        return { label: isEn ? 'Areas' : 'क्षेत्र', sublabel: '', icon: IconChartBar, count: 0 };
    }
  };

  const levelInfo = getLevelInfo();
  const labels = language === 'en'
    ? { candidates: 'Candidates', parties: 'Parties', independents: 'Independents', avgAge: 'Avg age', female: 'Female' }
    : { candidates: 'उम्मेदवार', parties: 'दलहरू', independents: 'स्वतन्त्र', avgAge: 'औसत उमेर', female: 'महिला' };
  const LevelIcon = levelInfo.icon;

  // When navigating from Compare with a निर्वाचन क्षेत्र click, auto-select that constituency and show all its candidates
  useEffect(() => {
    if (!mapData?.features?.length || currentLevel !== 'constituency' || !focusConstituency || !onClearFocusConstituency) return;
    const normalized = String(focusConstituency).trim();
    const feature = mapData.features.find((f) => {
      const name = (f.properties.display_name || f.properties.name || '').trim();
      return name === normalized || name.includes(normalized) || normalized.includes(name);
    });
    if (feature) {
      setSelectedItem(feature);
      setCandidateListFilter({ field: '', value: '' });
      loadCandidatesForFeature(feature);
      onClearFocusConstituency();
    } else {
      onClearFocusConstituency();
    }
  }, [mapData, currentLevel, focusConstituency, onClearFocusConstituency]);

  const loadCandidatesForFeature = async (feature) => {
    const props = feature.properties || {};
    const ids = props.candidate_ids;

    if (!ids || !Array.isArray(ids) || ids.length === 0) {
      setCandidateDetails(null);
      return;
    }

    setCandidatesLoading(true);
    setCandidatesError(null);
    setCandidatesJustLoaded(false);
    try {
      const data = await compareCandidates(ids, electionYear);
      setCandidateDetails(data);
      setCandidatesJustLoaded(true);
    } catch (err) {
      setCandidateDetails(null);
      setCandidatesError(err?.message || 'Failed to load candidates for this area');
    } finally {
      setCandidatesLoading(false);
    }
  };

  // Scroll detail panel into view when it opens
  useEffect(() => {
    if (!selectedItem || !detailPanelRef.current) return;
    const timer = requestAnimationFrame(() => {
      detailPanelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    });
    return () => cancelAnimationFrame(timer);
  }, [selectedItem]);

  // Clear "just loaded" highlight after brief delay
  useEffect(() => {
    if (!candidatesJustLoaded) return;
    const t = setTimeout(() => setCandidatesJustLoaded(false), 1500);
    return () => clearTimeout(t);
  }, [candidatesJustLoaded]);

  // Consistent header color (slate blue)
  const CARD_HEADER_BG = 'bg-[#1e3a5f]';

  const handleCardClick = (feature) => {
    setSelectedItem(feature);
    setCandidateDetails(null);
    setCandidatesError(null);
    setCandidateListFilter({ field: '', value: '' });

    if (onFeatureClick) {
      onFeatureClick(feature);
    }

    if (currentLevel === 'constituency') {
      loadCandidatesForFeature(feature);
    }
  };

  const handleDrillDown = (feature) => {
    if (onDrillDown && feature.properties.drilldown_to) {
      onDrillDown(feature.properties);
    }
  };

  // Filter config for candidate list: English (from CSV _en columns) or Nepali
  const CANDIDATE_FILTER_FIELDS = useMemo(() => {
    const isEn = language === 'en';
    return [
      {
        key: 'party',
        label: isEn ? 'Party' : 'दल',
        getValue: (c) => (isEn ? (c.party_en ?? c.party) : c.party ?? '').trim() || null,
      },
      {
        key: 'birth_place',
        label: isEn ? 'Birth place' : 'जन्म स्थान',
        getValue: (c) => (isEn ? (c.birth_place_en ?? c.birth_district) : c.birth_district ?? '').trim() || null,
      },
    ];
  }, [language]);

  const { filterOptionsByField, filteredCandidates } = useMemo(() => {
    const candidates = candidateDetails?.candidates ? Object.values(candidateDetails.candidates) : [];
    const optionsByField = {};
    CANDIDATE_FILTER_FIELDS.forEach(({ key, getValue }) => {
      const set = new Set();
      candidates.forEach((c) => {
        const v = getValue(c);
        if (v) set.add(v);
      });
      optionsByField[key] = [...set].sort((a, b) => String(a).localeCompare(String(b), language === 'en' ? 'en' : 'ne'));
    });
    const { field, value } = candidateListFilter;
    let filtered = candidates;
    if (field && value) {
      const config = CANDIDATE_FILTER_FIELDS.find((f) => f.key === field);
      if (config) {
        filtered = candidates.filter((c) => config.getValue(c) === value);
      }
    }
    return { filterOptionsByField: optionsByField, filteredCandidates: filtered };
  }, [candidateDetails, candidateListFilter, CANDIDATE_FILTER_FIELDS]);

  if (!mapData || !mapData.features || mapData.features.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-[#1e3a5f]/5 to-[#b91c1c]/5 rounded-xl">
        <div className="text-center">
          <IconBallot className="w-16 h-16 mx-auto mb-4 text-[#1e3a5f]/60" />
          <p className="text-xl text-[#1e3a5f]">{language === 'en' ? 'No election data available' : 'निर्वाचन डाटा उपलब्ध छैन'}</p>
          <p className="text-sm text-[#1e3a5f]/60 mt-2">{language === 'en' ? 'No map data for this view' : 'यो दृश्यको लागि नक्शा डाटा छैन'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full min-h-0 flex flex-col bg-gradient-to-br from-[#1e3a5f]/5 to-[#b91c1c]/5 rounded-xl overflow-hidden fade-in">
      {/* Header — compact on mobile, full on larger screens */}
      <div className="flex-none bg-gradient-to-br from-[#1e3a5f] via-[#1e3a5f] to-[#0f172a] text-white shadow-lg">
        <div className="p-2 sm:p-4 lg:p-5">
          <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2 sm:gap-4 lg:gap-6">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <div className="flex items-center justify-center w-9 h-9 sm:w-12 sm:h-12 lg:w-14 lg:h-14 rounded-lg sm:rounded-xl bg-white/10 backdrop-blur border border-white/20 shrink-0">
                <LevelIcon className="w-5 h-5 sm:w-6 sm:h-6 lg:w-8 lg:h-8 text-white/90" />
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="text-base sm:text-xl lg:text-2xl font-bold tracking-tight truncate">{levelInfo.label}</h2>
                <p className="text-white/80 text-xs sm:text-sm mt-0.5 truncate">
                  {levelInfo.sublabel} · {features.length} {levelInfo.sublabel.toLowerCase()}
                </p>
                {viewContext?.focusLine && (
                  <p className="text-white/70 text-xs mt-0.5 sm:mt-1 hidden sm:block" aria-hidden="true">
                    {viewContext.focusLine}
                  </p>
                )}
              </div>
            </div>

            {/* Quick Stats — horizontal scroll on mobile, single compact row */}
            {stats && (
              <div className="flex items-center gap-2 sm:gap-4 lg:gap-8 ml-0 lg:ml-4 pl-0 lg:pl-6 border-l-0 lg:border-l border-white/30 overflow-x-auto pb-0.5 -mb-0.5 scrollbar-thin sm:overflow-visible sm:pb-0 sm:mb-0 min-h-0">
                <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                  <span className="text-base sm:text-2xl lg:text-3xl font-bold tabular-nums text-white">
                    {stats.totalCandidates.toLocaleString()}
                  </span>
                  <span className="text-white/80 text-xs sm:text-sm whitespace-nowrap">{labels.candidates}</span>
                </div>
                <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                  <span className="text-base sm:text-2xl lg:text-3xl font-bold tabular-nums text-white">
                    {stats.totalParties}
                  </span>
                  <span className="text-white/80 text-xs sm:text-sm whitespace-nowrap">{labels.parties}</span>
                </div>
                <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                  <span className="text-base sm:text-2xl lg:text-3xl font-bold tabular-nums text-[#fbbf24]">
                    {stats.totalIndependents}
                  </span>
                  <span className="text-white/80 text-xs sm:text-sm whitespace-nowrap">
                    {labels.independents}{stats.totalIndependentsPercentage > 0 && ` (${stats.totalIndependentsPercentage}%)`}
                  </span>
                </div>
                {stats.avgAge > 0 && (
                  <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                    <span className="text-base sm:text-2xl lg:text-3xl font-bold tabular-nums text-white/90">
                      {stats.avgAge.toFixed(0)}
                    </span>
                    <span className="text-white/80 text-xs sm:text-sm whitespace-nowrap">{labels.avgAge}</span>
                  </div>
                )}
                {stats.femalePercentage != null && (
                  <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                    <span className="text-base sm:text-2xl lg:text-3xl font-bold tabular-nums text-[#ec4899]/90">
                      {stats.totalFemale.toLocaleString()}
                    </span>
                    <span className="text-white/80 text-xs sm:text-sm whitespace-nowrap">
                      {labels.female} ({stats.femalePercentage}%)
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Cards Grid — takes remaining space, scrolls on mobile */}
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-2 sm:p-4 overscroll-behavior-contain">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-4">
          {features.map((feature, index) => {
            const props = feature.properties;
            const name = language === 'en'
              ? (props.display_name_en || props.name_en || props.display_name || props.name || 'Unknown')
              : (props.display_name || props.name || 'Unknown');
            const cardDistrict = language === 'en' ? (props.district_en || props.district) : props.district;
            const cardProvince = language === 'en' ? (props.province_en || props.province) : props.province;
            const canDrillDown = props.drilldown_to && props.drilldown_to !== 'null';
            const isSelected = selectedItem === feature;

            // Parse party distribution (use English when language is en)
            let partyDist = language === 'en' && props.party_distribution_en
              ? props.party_distribution_en
              : props.party_distribution;
            if (typeof partyDist === 'string') {
              try { partyDist = JSON.parse(partyDist); } catch { partyDist = {}; }
            }
            const isIndependentParty = (p) => {
              const s = (p || '').trim();
              const lower = s.toLowerCase();
              return s === 'स्वतन्त्र' || s === 'स्वतंत्र' || lower === 'independent' || lower === 'independent candidate';
            };
            const topParties = partyDist && typeof partyDist === 'object'
              ? Object.entries(partyDist)
                  .filter(([party]) => !isIndependentParty(party))
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 3)
              : [];

            return (
              <div
                key={index}
                onClick={() => handleCardClick(feature)}
                className={`
                  relative overflow-hidden rounded-xl cursor-pointer transition-all duration-300 slide-up
                  ${
                    isSelected
                      ? 'ring-2 ring-[#b91c1c] scale-[1.02]'
                      : 'hover:scale-[1.02] hover:shadow-xl'
                  }
                  bg-white shadow-lg
                `}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {/* Card Header */}
                <div className={`${CARD_HEADER_BG} px-3 py-2 sm:px-4 sm:py-3 text-white`}>
                  <h3 className="font-semibold text-sm sm:text-base truncate" title={name}>
                    {name}
                  </h3>
                  {(() => {
                    const parts = [];
                    if (currentLevel === 'constituency') {
                      if (cardDistrict) parts.push(cardDistrict);
                      if (cardProvince) parts.push(cardProvince);
                    } else if (currentLevel === 'district' && cardProvince) {
                      parts.push(cardProvince);
                    }
                    if ((currentLevel === 'province' || currentLevel === 'district') && props.constituency_count != null && props.constituency_count > 0) {
                      parts.push(`${props.constituency_count} ${language === 'en' ? 'election areas' : 'निर्वाचन क्षेत्र'}`);
                    }
                    if (parts.length === 0) return null;
                    return (
                      <p className="text-white/75 text-xs mt-0.5 truncate">
                        {parts.join(' · ')}
                      </p>
                    );
                  })()}
                </div>

                {/* Card Body */}
                <div className="p-3 sm:p-4">
                  {/* Hero stat */}
                  <div className="mb-2 sm:mb-3">
                    <div className="text-xl sm:text-2xl font-bold text-[#1e3a5f] tabular-nums">
                      {(props.total_candidates || 0).toLocaleString()}
                    </div>
                    <div className="text-xs text-[#1e3a5f]/60">{labels.candidates}</div>
                  </div>

                  {/* Secondary pills */}
                  <div className="flex flex-wrap gap-1 sm:gap-1.5 mb-2 sm:mb-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-[#1e3a5f]/10 text-[#1e3a5f] text-xs font-medium">
                      {props.unique_parties || 0} {labels.parties}
                    </span>
                    {props.independent_count > 0 && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-[#fbbf24]/20 text-[#fbbf24] text-xs font-medium">
                        {props.independent_count} {labels.independents}
                      </span>
                    )}
                    {props.average_age && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-[#1e3a5f]/8 text-[#1e3a5f]/80 text-xs">
                        {props.average_age.toFixed(0)} {labels.avgAge}
                      </span>
                    )}
                  </div>

                  {/* Gender bar */}
                  {(() => {
                    const g = getGenderFromProps(props);
                    if (!g) return null;
                    const pct = g.femalePct ?? 0;
                    return (
                      <div className="mb-2 sm:mb-3">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-[11px] text-[#1e3a5f]/60">{labels.female}</span>
                          <span className="text-[11px] font-medium text-[#ec4899]">{pct}%</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-[#1e3a5f]/15 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-[#ec4899]/70 transition-all"
                            style={{ width: `${Math.min(100, pct)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })()}

                  {/* Top parties (compact) */}
                  {topParties.length > 0 && (
                    <div className="pt-2 sm:pt-3 border-t border-[#1e3a5f]/12">
                      <div className="text-[11px] text-[#1e3a5f]/50 uppercase tracking-wide mb-1.5">
                        {language === 'en' ? 'Top parties' : 'शीर्ष दलहरू'}
                      </div>
                      <div className="space-y-1">
                        {topParties.map(([party, count], i) => (
                          <div key={i} className="flex items-center gap-2 min-w-0">
                            <PartyImage partyName={party} className="w-3.5 h-3.5 shrink-0" />
                            <span className="text-xs text-[#1e3a5f]/85 truncate flex-1" title={party}>
                              {party.length > 18 ? party.substring(0, 18) + '…' : party}
                            </span>
                            <span className="text-xs font-medium text-[#1e3a5f] shrink-0 tabular-nums">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Drill down CTA */}
                  {canDrillDown && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDrillDown(feature);
                      }}
                      className="mt-3 sm:mt-4 w-full py-2 px-3 sm:px-4 bg-[#1e3a5f]/10 text-[#1e3a5f] rounded-lg font-medium text-xs sm:text-sm hover:bg-[#1e3a5f]/20 border border-[#1e3a5f]/20 transition-all flex items-center justify-center gap-2 touch-manipulation min-h-[44px]"
                    >
                      {props.drilldown_to === 'district'
                        ? (language === 'en' ? 'View districts' : 'जिल्लाहरू हेर्नुहोस्')
                        : (language === 'en' ? 'View election areas' : 'निर्वाचन क्षेत्र हेर्नुहोस्')}
                      <span aria-hidden>→</span>
                    </button>
                  )}
                </div>

              </div>
            );
          })}
        </div>

      </div>

      {/* Mobile: tap-to-close overlay when detail panel is open (panel has z-40 so it stays on top) */}
      {selectedItem && (
        <div
          className="sm:hidden fixed inset-0 z-30 bg-black/40"
          onClick={() => {
            setSelectedItem(null);
            setCandidateDetails(null);
            setCandidatesError(null);
            setCandidateListFilter({ field: '', value: '' });
          }}
          aria-hidden="true"
        />
      )}

      {/* Selected item detail panel — on mobile: fixed bottom sheet overlay so cards area stays full height; on sm+: inline */}
      {selectedItem && (
        <div
          ref={detailPanelRef}
          className={`
            bg-white border-t-2 shadow-[0_-4px_16px_rgba(30,58,95,0.06)] transition-all duration-300
            sm:flex-none sm:shrink-0
            fixed sm:relative inset-x-0 bottom-0 z-40 sm:z-auto rounded-t-xl sm:rounded-none
            max-h-[85vh] sm:max-h-none
            ${candidatesJustLoaded ? 'border-[#16a34a] ring-2 ring-[#16a34a]/20' : 'border-[#1e3a5f]/20'}
          `}
          aria-live="polite"
          aria-label={candidatesLoading
            ? (language === 'en' ? 'Loading candidates' : 'उम्मेदवार लोड हुँदैछ')
            : candidateDetails
              ? (language === 'en' ? `${Object.values(candidateDetails.candidates || {}).length} candidates loaded` : `${Object.values(candidateDetails.candidates || {}).length} उम्मेदवार लोड भयो`)
              : undefined
          }
        >
          <div className="flex items-start justify-between gap-2 sm:gap-4 p-3 sm:p-4 max-h-[75vh] sm:max-h-80 overflow-y-auto overscroll-contain">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-base text-[#1e3a5f]">
                {language === 'en'
                  ? (selectedItem.properties.display_name_en || selectedItem.properties.name_en || selectedItem.properties.display_name || selectedItem.properties.name)
                  : (selectedItem.properties.display_name || selectedItem.properties.name)}
              </h3>
              {currentLevel === 'constituency' && (
                <p className="text-xs text-[#1e3a5f]/60 mt-0.5">
                  {language === 'en' ? 'Candidates in this election area' : 'यस निर्वाचन क्षेत्रका उम्मेदवार'}
                </p>
              )}

              {currentLevel === 'constituency' && (
                <div className="mt-3">
                  {candidatesLoading && (
                    <div className="flex flex-col items-center gap-4 py-6" role="status" aria-label={language === 'en' ? 'Loading candidates' : 'उम्मेदवार लोड हुँदैछ'}>
                      <div className="animate-spin rounded-full h-10 w-10 border-2 border-[#1e3a5f]/20 border-t-[#b91c1c]" />
                      <p className="text-sm font-medium text-[#1e3a5f]/80">{language === 'en' ? 'Loading candidates…' : 'उम्मेदवार लोड हुँदैछ…'}</p>
                      <div className="w-full space-y-2 max-w-sm">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="flex gap-3 p-2.5 rounded-lg border border-[#1e3a5f]/12 bg-[#1e3a5f]/5 animate-pulse">
                            <div className="w-9 h-9 rounded-full bg-[#1e3a5f]/20 shrink-0" />
                            <div className="flex-1 space-y-1.5">
                              <div className="h-4 w-3/4 rounded bg-[#1e3a5f]/15" />
                              <div className="h-3 w-1/2 rounded bg-[#1e3a5f]/10" />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {candidatesError && (
                    <p className="text-sm text-[#b91c1c]">{candidatesError}</p>
                  )}

                  {!candidatesLoading && candidateDetails && (
                    <>
                      {candidatesJustLoaded && (
                        <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-[#16a34a]/10 text-[#16a34a] border border-[#16a34a]/20 animate-pulse-slow" role="status">
                          <svg className="w-5 h-5 shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          <span className="text-sm font-medium">
                            {Object.values(candidateDetails.candidates || {}).length} {language === 'en' ? 'candidates loaded' : 'उम्मेदवार लोड भयो'}
                          </span>
                        </div>
                      )}
                      {/* Filter row */}
                      <div className="flex flex-wrap items-center gap-2 mb-3">
                        <select
                          value={candidateListFilter.field}
                          onChange={(e) => setCandidateListFilter({ field: e.target.value, value: '' })}
                          className="text-xs border border-[#1e3a5f]/20 rounded-md pl-2.5 pr-10 py-1.5 bg-[#1e3a5f]/5 text-[#1e3a5f] focus:outline-none focus:ring-1 focus:ring-[#1e3a5f]/40"
                        >
                          <option value="">{language === 'en' ? 'Filter by' : 'फिल्टर'}</option>
                          {CANDIDATE_FILTER_FIELDS.map((f) => (
                            <option key={f.key} value={f.key}>{f.label}</option>
                          ))}
                        </select>
                        {candidateListFilter.field && (
                          <>
                            <select
                              value={candidateListFilter.value}
                              onChange={(e) => setCandidateListFilter((prev) => ({ ...prev, value: e.target.value }))}
                              className="text-xs border border-[#1e3a5f]/20 rounded-md pl-2.5 pr-10 py-1.5 bg-white text-[#1e3a5f] focus:outline-none focus:ring-1 focus:ring-[#1e3a5f]/40 min-w-[100px]"
                            >
                              <option value="">All</option>
                              {(filterOptionsByField[candidateListFilter.field] || []).map((opt) => (
                                <option key={opt} value={opt}>{opt}</option>
                              ))}
                            </select>
                            <button
                              type="button"
                              onClick={() => setCandidateListFilter({ field: '', value: '' })}
                              className="text-xs text-[#1e3a5f]/70 hover:text-[#b91c1c]"
                            >
                              {language === 'en' ? 'Clear' : 'मेट्नुहोस्'}
                            </button>
                          </>
                        )}
                        <span className="text-xs text-[#1e3a5f]/50 ml-auto">
                          {filteredCandidates.length} {language === 'en' ? 'of' : '/'} {Object.values(candidateDetails.candidates || {}).length}
                        </span>
                      </div>
                      <div className="max-h-[min(40vh,12rem)] sm:max-h-52 overflow-y-auto pr-1 -mr-1">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {filteredCandidates.map((candidate, idx) => {
                          const name = candidate.candidate_name ?? 'Unknown';
                          const parts = name.trim().split(' ').filter(Boolean);
                          const initials =
                            parts.length === 1
                              ? parts[0].charAt(0)
                              : `${parts[0].charAt(0)}${parts[parts.length - 1].charAt(0)}`;

                          return (
                            <div
                              key={`${candidate.candidate_id}-${idx}`}
                              className="flex gap-2.5 p-2.5 rounded-lg border border-[#1e3a5f]/12 bg-[#1e3a5f]/[0.02] hover:border-[#1e3a5f]/25 transition-colors"
                            >
                              <div className="relative w-9 h-9 shrink-0">
                                <div className="absolute inset-0 w-9 h-9 rounded-full bg-[#1e3a5f]/15 flex items-center justify-center text-[#1e3a5f] font-medium text-xs">
                                  {initials}
                                </div>
                                {candidate.image_url && (
                                  <img
                                    src={candidate.image_url}
                                    alt={name}
                                    className="relative w-9 h-9 rounded-full object-cover border border-[#1e3a5f]/15"
                                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                                  />
                                )}
                              </div>

                              <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-[#1e3a5f] truncate">{name}</p>
                                <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-0.5">
                                  {CANDIDATE_FILTER_FIELDS.map(({ key, label, getValue }) => {
                                    const value = getValue(candidate);
                                    if (!value) return null;
                                    const isActive = candidateListFilter.field === key && candidateListFilter.value === value;
                                    return (
                                      <button
                                        key={key}
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setCandidateListFilter(isActive ? { field: '', value: '' } : { field: key, value });
                                        }}
                                        className={`inline-flex items-center gap-1 text-[11px] rounded px-1 -mx-1 truncate max-w-full focus:outline-none focus:ring-1 focus:ring-[#1e3a5f]/40 ${isActive ? 'bg-[#b91c1c]/15 text-[#b91c1c]' : 'text-[#1e3a5f]/75 hover:bg-[#1e3a5f]/10'}`}
                                        title={value}
                                      >
                                        {key === 'party' && <PartyImage partyName={value} className="w-3 h-3 shrink-0" />}
                                        <span className="truncate">{value}</span>
                                      </button>
                                    );
                                  })}
                                </div>
                                {(candidate.gender || candidate.age || candidate.education_level) && (
                                  <p className="text-[11px] text-[#1e3a5f]/55 mt-0.5">
                                    {[candidate.gender, candidate.age && `${Math.round(candidate.age)} yrs`, candidate.education_level].filter(Boolean).join(' · ')}
                                  </p>
                                )}
                              </div>

                              <div className="shrink-0 flex flex-col items-end gap-1">
                                {candidate.symbol && (
                                  <span title={candidate.symbol}>
                                    <ElectionSymbolImage symbolName={candidate.symbol} className="w-6 h-6" />
                                  </span>
                                )}
                                {candidate.is_winner && (
                                  <span className="px-1.5 py-0.5 rounded bg-[#b91c1c]/15 text-[#b91c1c] text-[10px] font-medium">
                                    {language === 'en' ? 'Winner' : 'विजेता'}
                                  </span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                    </>
                  )}
                </div>
              )}

              {currentLevel !== 'constituency' && (
                <p className="text-xs text-[#1e3a5f]/55 mt-3">
                  {language === 'en' ? 'Click a card and drill down to see candidates.' : 'निर्वाचन क्षेत्र हेर्न कार्डमा क्लिक गर्नुहोस्।'}
                </p>
              )}
            </div>
            <button
              onClick={() => {
                setSelectedItem(null);
                setCandidateDetails(null);
                setCandidatesError(null);
                setCandidateListFilter({ field: '', value: '' });
              }}
              className="min-w-[44px] min-h-[44px] p-2 flex items-center justify-center hover:bg-[#1e3a5f]/10 rounded-full shrink-0 text-[#1e3a5f]/80 hover:text-[#b91c1c] touch-manipulation"
              aria-label={language === 'en' ? 'Close' : 'बन्द गर्नुहोस्'}
            >
              <IconClose className="w-5 h-5 sm:w-4 sm:h-4" />
            </button>
          </div>
        </div>
      )}
      {viewContext?.takeaway && (
        <p className="text-xs text-[#1e3a5f]/70 px-3 sm:px-4 pb-3 pt-2 border-t border-[#1e3a5f]/10 mt-2" aria-label={language === 'en' ? 'Key takeaway' : 'मुख्य निष्कर्ष'}>
          {viewContext.takeaway}
        </p>
      )}
    </div>
  );
};

export default MapView;
