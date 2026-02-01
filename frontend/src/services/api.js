/**
 * API service for communicating with the FastAPI backend.
 * In dev, use empty string so Vite proxy (/api -> localhost:8000) is used (avoids CORS).
 * In prod: VITE_API_URL if set; else same host on port 8000 (e.g. droplet 165.22.215.152:8000); else localhost:8000.
 */
import axios from 'axios';

function getProductionApiBase() {
  if (typeof window !== 'undefined' && window.location?.hostname) {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
}

const API_BASE_URL = import.meta.env.VITE_API_URL
  || (import.meta.env.DEV ? '' : getProductionApiBase());

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.detail
      ? (typeof err.response.data.detail === 'string'
        ? err.response.data.detail
        : err.response?.data?.detail?.msg || JSON.stringify(err.response.data.detail))
      : err.message || 'Network error';
    try {
      window.dispatchEvent(new CustomEvent('api-error', { detail: { message } }));
    } catch (_) {}
    return Promise.reject(err);
  }
);

/**
 * Get map data (GeoJSON) with filters
 * 
 * Drill-down hierarchy:
 * - level=province: Shows all 7 provinces of Nepal
 * - level=district: Shows districts (requires province filter)
 * - level=constituency: Shows constituencies/election areas (requires district filter)
 */
export const getMapData = async (filters) => {
  const params = new URLSearchParams();
  params.append('election_year', filters.electionYear);
  params.append('level', filters.level || 'province');
  if (filters.province) params.append('province', filters.province);
  if (filters.district) params.append('district', filters.district);
  if (filters.party) params.append('party', filters.party);
  if (filters.independent !== null && filters.independent !== undefined) {
    params.append('independent', filters.independent);
  }
  if (filters.ageMin) params.append('age_min', filters.ageMin);
  if (filters.ageMax) params.append('age_max', filters.ageMax);
  if (filters.gender) params.append('gender', filters.gender);
  if (filters.educationLevel) params.append('education_level', filters.educationLevel);

  const response = await api.get(`/api/v1/map?${params.toString()}`);
  return response.data;
};

/**
 * Get trend data across multiple years
 */
export const getTrends = async (years, metric = null) => {
  const params = new URLSearchParams();
  params.append('years', years.join(','));
  if (metric) params.append('metric', metric);

  const response = await api.get(`/api/v1/trends?${params.toString()}`);
  return response.data;
};

/**
 * Get insights for an election year
 */
export const getInsights = async (electionYear, compareWith = null) => {
  const params = new URLSearchParams();
  params.append('election_year', electionYear);
  if (compareWith) params.append('compare_with', compareWith);

  const response = await api.get(`/api/v1/insights?${params.toString()}`);
  return response.data;
};

/**
 * Independent Wave Insight (district-level independent strength)
 */
export const getIndependentWaveInsight = async (electionYear) => {
  const params = new URLSearchParams();
  params.append('election_year', electionYear);

  const response = await api.get(`/api/v1/insights/independent-wave?${params.toString()}`);
  return response.data;
};

/**
 * District Competition Pressure insight
 */
export const getCompetitionPressureInsight = async (electionYear) => {
  const params = new URLSearchParams();
  params.append('election_year', electionYear);

  const response = await api.get(`/api/v1/insights/competition-pressure?${params.toString()}`);
  return response.data;
};

/**
 * Party Saturation vs Reach insight
 */
export const getPartySaturationInsight = async (electionYear) => {
  const params = new URLSearchParams();
  params.append('election_year', electionYear);

  const response = await api.get(`/api/v1/insights/party-saturation?${params.toString()}`);
  return response.data;
};

/**
 * Gender Gap insight
 * Female candidate representation and gender parity
 */
export const getGenderGapInsight = async (electionYear) => {
  const params = new URLSearchParams();
  params.append('election_year', electionYear);

  const response = await api.get(`/api/v1/insights/gender-gap?${params.toString()}`);
  return response.data;
};

/**
 * Age Gap Between Political Movements insight
 * Average age: Top 3 legacy parties vs new/alternative parties vs independents
 */
export const getAgeGapInsight = async (electionYear) => {
  const params = new URLSearchParams();
  params.append('election_year', electionYear);

  const response = await api.get(`/api/v1/insights/age-gap?${params.toString()}`);
  return response.data;
};

/**
 * Year insights (filtered by party / province / district)
 * Returns: age demographics, education profile, party vs age, birthplace vs contest,
 * symbol recognition, composite metrics
 */
export const getYearInsights = async (electionYear, filters = {}) => {
  const params = new URLSearchParams();
  params.append('election_year', electionYear);
  if (filters.province) params.append('province', filters.province);
  if (filters.district) params.append('district', filters.district);
  if (filters.party) params.append('party', filters.party);
  if (filters.gender) params.append('gender', filters.gender);

  const response = await api.get(`/api/v1/insights/year-insights?${params.toString()}`);
  return response.data;
};

/**
 * Compare candidates by ID
 */
export const compareCandidates = async (candidateIds, electionYear = null) => {
  const params = new URLSearchParams();
  params.append('candidate_ids', candidateIds.join(','));
  if (electionYear) params.append('election_year', electionYear);

  const response = await api.get(`/api/v1/compare/candidates?${params.toString()}`);
  return response.data;
};

/**
 * Search candidates by name or ID (autocomplete, top 5)
 */
export const searchCandidates = async (q, limit = 5, electionYear = null) => {
  const params = new URLSearchParams();
  params.append('q', q);
  params.append('limit', String(limit));
  if (electionYear) params.append('election_year', electionYear);

  const response = await api.get(`/api/v1/compare/candidates/search?${params.toString()}`);
  return response.data;
};

/**
 * List available elections
 */
export const listElections = async () => {
  const response = await api.get('/api/v1/elections');
  return response.data;
};

/**
 * Get election summary
 */
export const getElectionSummary = async (year) => {
  const response = await api.get(`/api/v1/elections/${year}/summary`);
  return response.data;
};

/**
 * Get filter options (provinces, districts, parties, etc.) from CSV data
 * Supports hierarchical filtering based on province/district selection
 */
export const getFilterOptions = async (year, province = null, district = null) => {
  const params = new URLSearchParams();
  if (province) params.append('province', province);
  if (district) params.append('district', district);
  
  const queryString = params.toString() ? `?${params.toString()}` : '';
  const response = await api.get(`/api/v1/elections/${year}/filter-options${queryString}`);
  return response.data;
};

/**
 * Get supported schema (required, optional, English columns) for review
 */
export const getSchema = async () => {
  const response = await api.get('/api/v1/schema');
  return response.data;
};

/**
 * Get columns and first row for an election year (for review, includes English when present)
 */
export const getElectionColumns = async (year) => {
  const response = await api.get(`/api/v1/elections/${year}/columns`);
  return response.data;
};

export default api;
