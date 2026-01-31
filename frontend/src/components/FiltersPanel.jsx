import React, { useState, useEffect } from 'react';
import { getFilterOptions } from '../services/api';
import { IconMapPin } from './icons';

const ELECTION_YEAR = 2082;

const FiltersPanel = ({ filters, onFiltersChange, language = 'ne' }) => {
  const [localFilters, setLocalFilters] = useState(filters);
  // Sync from parent when filters are updated elsewhere (e.g. Candidate details filter)
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const [filterOptions, setFilterOptions] = useState({
    provinces: [],
    districts: [],
    constituencies: [],
    parties: [],
    genders: [],
    education_levels: [],
    age_range: { min: 18, max: 100 },
  });
  const [loading, setLoading] = useState(false);

  // Load filter options when election year changes
  useEffect(() => {
    if (localFilters.electionYear) {
      loadFilterOptions();
    }
  }, [localFilters.electionYear]);

  // Reload districts when province changes
  useEffect(() => {
    if (localFilters.electionYear && localFilters.province) {
      loadFilterOptions(localFilters.province, null);
    }
  }, [localFilters.province]);

  // Reload constituencies when district changes
  useEffect(() => {
    if (localFilters.electionYear && localFilters.district) {
      loadFilterOptions(localFilters.province, localFilters.district);
    }
  }, [localFilters.district]);

  const loadFilterOptions = async (province = null, district = null) => {
    if (!localFilters.electionYear) return;
    
    setLoading(true);
    try {
      const options = await getFilterOptions(localFilters.electionYear, province, district);
      setFilterOptions(options);
    } catch (error) {
      console.error('Failed to load filter options:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (key, value) => {
    let newFilters = { ...localFilters, [key]: value };
    
    // Reset dependent filters when parent changes
    if (key === 'province') {
      newFilters = {
        ...newFilters,
        district: null,
        level: value ? 'district' : 'province',
      };
    } else if (key === 'district') {
      newFilters = {
        ...newFilters,
        level: value ? 'constituency' : 'district',
      };
    }
    
    setLocalFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handleReset = () => {
    const resetFilters = {
      electionYear: ELECTION_YEAR,
      level: 'province',
      province: null,
      district: null,
      party: null,
      independent: null,
      ageMin: null,
      ageMax: null,
      gender: null,
      educationLevel: null,
    };
    setLocalFilters(resetFilters);
    onFiltersChange(resetFilters);
  };

  return (
    <div className="bg-white p-3 lg:p-4 rounded-2xl shadow-md space-y-4 lg:space-y-5 border border-[#1e3a5f]/15 fade-in">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-lg font-semibold text-[#1e3a5f] tracking-tight flex items-center gap-2">
            <IconMapPin className="w-5 h-5 text-[#1e3a5f]" />
            {language === 'en' ? 'Filters' : 'Election filters'}
          </h2>
          <p className="text-xs text-[#1e3a5f]/70 mt-0.5">
            {language === 'en' ? 'Narrow down by province, district and constituency' : 'Narrow down provinces, districts and नि.क्षे.'}
          </p>
        </div>
        <button
          onClick={handleReset}
          className="text-xs px-2 py-1 rounded-full bg-[#1e3a5f]/10 text-[#1e3a5f] hover:bg-[#b91c1c] hover:text-white font-medium border border-[#1e3a5f]/20 transition-all"
        >
          Reset
        </button>
      </div>

      {loading && (
        <div className="text-sm text-[#1e3a5f]/70 text-center py-3 bg-[#1e3a5f]/5 rounded-lg border border-[#1e3a5f]/15 slide-up">
          <div className="flex items-center justify-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border border-[#1e3a5f]/20 border-t-[#b91c1c]"></div>
            <span>Loading options...</span>
          </div>
        </div>
      )}

      {/* Section: Election Context */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-[#1e3a5f]/70 uppercase tracking-wide">
          Election context
        </p>

        {/* Map View Level */}
        <div className="bg-[#1e3a5f]/5 p-3 rounded-lg border border-[#1e3a5f]/15 min-w-0 overflow-hidden">
          <label className="flex items-center gap-1.5 text-xs font-semibold text-[#1e3a5f] mb-2 tracking-wide">
            <IconMapPin className="w-4 h-4" />
            <span>View level</span>
          </label>
          <div className="flex gap-1.5 min-w-0">
          <button
            onClick={() => handleChange('level', 'province')}
            className={`flex-1 min-w-0 px-2 py-1.5 text-xs font-medium rounded-full transition-colors text-center whitespace-normal break-words ${
              localFilters.level === 'province'
                ? 'bg-[#b91c1c] text-white shadow-sm'
                : 'bg-white text-[#1e3a5f]/80 border border-[#1e3a5f]/20 hover:bg-[#1e3a5f]/5'
            }`}
          >
            {language === 'en' ? 'Province' : 'प्रदेश'}
          </button>
          <button
            onClick={() => handleChange('level', 'district')}
            className={`flex-1 min-w-0 px-2 py-1.5 text-xs font-medium rounded-full transition-colors text-center whitespace-normal break-words ${
              localFilters.level === 'district'
                ? 'bg-[#b91c1c] text-white shadow-sm'
                : 'bg-white text-[#1e3a5f]/80 border border-[#1e3a5f]/20 hover:bg-[#1e3a5f]/5'
            }`}
          >
            {language === 'en' ? 'District' : 'जिल्ला'}
          </button>
          <button
            onClick={() => handleChange('level', 'constituency')}
            className={`flex-1 min-w-0 px-2 py-1.5 text-xs font-medium rounded-full transition-colors text-center whitespace-normal break-words ${
              localFilters.level === 'constituency'
                ? 'bg-[#b91c1c] text-white shadow-sm'
                : 'bg-white text-[#1e3a5f]/80 border border-[#1e3a5f]/20 hover:bg-[#1e3a5f]/5'
            }`}
          >
            {language === 'en' ? 'Constituency' : 'नि.क्षे.'}
          </button>
        </div>
          <p className="text-[11px] text-[#1e3a5f]/80 mt-2 leading-snug">
            {localFilters.level === 'province' && (language === 'en' ? 'National overview • 7 provinces' : 'National overview • ७ प्रदेश')}
            {localFilters.level === 'district' && (language === 'en' ? 'Mid level • 77 districts' : 'मध्य स्तर • ७७ जिल्ला')}
            {localFilters.level === 'constituency' && (language === 'en' ? 'Smallest unit • Constituencies' : 'सबैभन्दा सानो इकाई • नि.क्षे.')}
          </p>
        </div>
      </div>

      {/* Section: Geography & Party */}
      <div className="space-y-3 pt-2 border-t border-[#1e3a5f]/15">
        <p className="text-xs font-semibold text-[#1e3a5f]/70 uppercase tracking-wide">
          Geography & party
        </p>

        {/* Province */}
        <div>
          <label className="block text-xs font-medium text-[#1e3a5f]/90 mb-1.5">
            Province
          </label>
          <select
            value={localFilters.province || ''}
            onChange={(e) => handleChange('province', e.target.value || null)}
            disabled={!localFilters.electionYear || filterOptions.provinces.length === 0}
            className="w-full pl-3 py-2.5 border border-[#1e3a5f]/25 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] bg-white disabled:bg-[#1e3a5f]/5 disabled:cursor-not-allowed text-sm"
          >
            <option value="">All Provinces</option>
            {filterOptions.provinces.map((province) => (
              <option key={province} value={province}>
                {province}
              </option>
            ))}
          </select>
          {filterOptions.provinces.length > 0 && (
            <p className="text-[11px] text-[#1e3a5f]/60 mt-1">{filterOptions.provinces.length} provinces</p>
          )}
        </div>

        {/* District */}
        <div>
          <label className="block text-xs font-medium text-[#1e3a5f]/90 mb-1.5">
            District
          </label>
          <select
            value={localFilters.district || ''}
            onChange={(e) => handleChange('district', e.target.value || null)}
            disabled={!localFilters.electionYear || filterOptions.districts.length === 0}
            className="w-full pl-3 py-2.5 border border-[#1e3a5f]/25 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] bg-white disabled:bg-[#1e3a5f]/5 disabled:cursor-not-allowed text-sm"
          >
            <option value="">All Districts</option>
            {filterOptions.districts.map((district) => (
              <option key={district} value={district}>
                {district}
              </option>
            ))}
          </select>
          {filterOptions.districts.length > 0 && (
            <p className="text-[11px] text-[#1e3a5f]/60 mt-1">{filterOptions.districts.length} districts</p>
          )}
        </div>

        {/* Party */}
        <div>
          <label className="block text-xs font-medium text-[#1e3a5f]/90 mb-1.5">
            Political party
          </label>
          <select
            value={localFilters.party || ''}
            onChange={(e) => handleChange('party', e.target.value || null)}
            disabled={!localFilters.electionYear || filterOptions.parties.length === 0}
            className="w-full pl-3 py-2.5 border border-[#1e3a5f]/25 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] bg-white disabled:bg-[#1e3a5f]/5 disabled:cursor-not-allowed text-sm"
          >
            <option value="">All Parties</option>
            {filterOptions.parties.map((party) => (
              <option key={party} value={party}>
                {party}
              </option>
            ))}
          </select>
          {filterOptions.parties.length > 0 && (
            <p className="text-[11px] text-[#1e3a5f]/60 mt-1">{filterOptions.parties.length} parties</p>
          )}
        </div>

        {/* Candidate Type */}
        <div>
          <label className="block text-xs font-medium text-[#1e3a5f]/90 mb-1.5">
            Candidate type
          </label>
          <select
            value={localFilters.independent === null ? '' : localFilters.independent ? 'true' : 'false'}
            onChange={(e) => {
              const value = e.target.value === '' ? null : e.target.value === 'true';
              handleChange('independent', value);
            }}
            className="w-full pl-3 py-2.5 border border-[#1e3a5f]/25 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] bg-white text-sm"
          >
            <option value="">All Candidates</option>
            <option value="true">Independent Only</option>
            <option value="false">Party Candidates Only</option>
          </select>
        </div>
      </div>

      {/* Section: Demographics */}
      <div className="space-y-3 pt-2 border-t border-[#1e3a5f]/15">
        <p className="text-xs font-semibold text-[#1e3a5f]/70 uppercase tracking-wide">
          Demographics
        </p>

        {/* Gender */}
        <div>
          <label className="block text-xs font-medium text-[#1e3a5f]/90 mb-1.5">
            Gender
          </label>
          <select
            value={localFilters.gender || ''}
            onChange={(e) => handleChange('gender', e.target.value || null)}
            disabled={!localFilters.electionYear}
            className="w-full pl-3 py-2.5 border border-[#1e3a5f]/25 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] bg-white disabled:bg-[#1e3a5f]/5 disabled:cursor-not-allowed text-sm"
          >
            <option value="">All Genders</option>
            {filterOptions.genders.length > 0 ? (
              filterOptions.genders.map((gender) => (
                <option key={gender} value={gender}>
                  {gender === 'M' ? 'Male' : gender === 'F' ? 'Female' : gender}
                </option>
              ))
            ) : (
              <>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="Other">Other</option>
              </>
            )}
          </select>
        </div>

        {/* Education Level */}
        <div>
          <label className="block text-xs font-medium text-[#1e3a5f]/90 mb-1.5">
            Education level
          </label>
          <select
            value={localFilters.educationLevel || ''}
            onChange={(e) => handleChange('educationLevel', e.target.value || null)}
            disabled={!localFilters.electionYear || filterOptions.education_levels.length === 0}
            className="w-full pl-3 py-2.5 border border-[#1e3a5f]/25 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] bg-white disabled:bg-[#1e3a5f]/5 disabled:cursor-not-allowed text-sm"
          >
            <option value="">All Education Levels</option>
            {filterOptions.education_levels.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
          {filterOptions.education_levels.length > 0 && (
            <p className="text-[11px] text-[#1e3a5f]/60 mt-1">{filterOptions.education_levels.length} levels</p>
          )}
        </div>

        {/* Age Range */}
        <div>
          <label className="block text-xs font-medium text-[#1e3a5f]/90 mb-1.5">
            Age range ({filterOptions.age_range.min} - {filterOptions.age_range.max})
          </label>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <input
                type="number"
                min={filterOptions.age_range.min}
                max={filterOptions.age_range.max}
                value={localFilters.ageMin || ''}
                onChange={(e) => handleChange('ageMin', e.target.value ? parseInt(e.target.value) : null)}
                placeholder={`Min (${filterOptions.age_range.min})`}
                className="w-full px-3 py-2.5 border border-[#1e3a5f]/25 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] text-sm"
              />
            </div>
            <div>
              <input
                type="number"
                min={filterOptions.age_range.min}
                max={filterOptions.age_range.max}
                value={localFilters.ageMax || ''}
                onChange={(e) => handleChange('ageMax', e.target.value ? parseInt(e.target.value) : null)}
                placeholder={`Max (${filterOptions.age_range.max})`}
                className="w-full px-3 py-2.5 border border-[#1e3a5f]/25 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] text-sm"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Active Filters Summary */}
      {(localFilters.province || localFilters.district || localFilters.party || localFilters.gender || localFilters.educationLevel) && (
        <div className="mt-2 p-3 bg-[#1e3a5f]/5 rounded-lg border border-[#1e3a5f]/15">
          <p className="text-xs font-semibold text-[#1e3a5f] mb-2">Active filters</p>
          <div className="flex flex-wrap gap-2">
            {localFilters.province && (
              <span className="px-2.5 py-1 bg-[#b91c1c] text-white text-[11px] rounded-full">
                {localFilters.province}
              </span>
            )}
            {localFilters.district && (
              <span className="px-2.5 py-1 bg-[#b91c1c] text-white text-[11px] rounded-full">
                {localFilters.district}
              </span>
            )}
            {localFilters.party && (
              <span className="px-2.5 py-1 bg-[#b91c1c] text-white text-[11px] rounded-full">
                {localFilters.party}
              </span>
            )}
            {localFilters.gender && (
              <span className="px-2.5 py-1 bg-[#b91c1c] text-white text-[11px] rounded-full">
                {localFilters.gender === 'M' ? 'Male' : localFilters.gender === 'F' ? 'Female' : localFilters.gender}
              </span>
            )}
            {localFilters.educationLevel && (
              <span className="px-2.5 py-1 bg-[#b91c1c] text-white text-[11px] rounded-full">
                {localFilters.educationLevel}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FiltersPanel;
