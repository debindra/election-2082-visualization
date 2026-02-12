/**
 * API service for communicating with the FastAPI backend.
 * In dev, use empty string so Vite proxy (/api -> localhost:8000) is used (avoids CORS).
 * In prod: VITE_API_URL if set; else same origin (empty string). Same-origin works when
 * Nginx serves HTTPS and proxies / to the app on :8000 (no HTTPS on :8000), so API calls
 * must go to e.g. https://nepalelection.subsy.tech/api/v1/... not ...:8000.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL
  || (import.meta.env.DEV ? '' : '');

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

/**
 * Get voting centers
 * Filters can be applied by province, district, election_area, palika_name, ward_no, or polling_center_code
 * Returns: { voting_centers: [...], summary: { total_centers, total_voters, ... } }
 */
export const getVotingCenters = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.province) params.append('province', filters.province);
  if (filters.district) params.append('district', filters.district);
  if (filters.electionArea) params.append('election_area', filters.electionArea);
  if (filters.palikaName) params.append('palika_name', filters.palikaName);
  if (filters.wardNo) params.append('ward_no', filters.wardNo);
  if (filters.pollingCenterCode) params.append('polling_center_code', filters.pollingCenterCode);

  const response = await api.get(`/api/v1/voting-centers?${params.toString()}`);
  return response.data;
};

/**
 * Get candidates list for display in traditional format
 * @param {Object} filters - Filters: electionYear, province, district, party, etc.
 * @returns {Promise<Object>} Response with candidates list and summary
 */
export const getCandidatesList = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.electionYear) params.append('election_year', filters.electionYear);
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

  // Use the existing map endpoint which returns candidates with their data
  const response = await api.get(`/api/v1/map?${params.toString()}`);
  // Extract candidates from the response
  const candidates = response.data.features?.map(feature => feature.properties) || [];
  
  return {
    candidates,
    summary: {
      total: candidates.length,
      year: filters.electionYear
    }
  };
};

/**
 * RAG QA Service API
 * Queries the RAG QA service running on port 8002 for candidates and voting center information
 */

const RAG_API_BASE_URL = import.meta.env.VITE_RAG_API_URL || 
  (import.meta.env.DEV ? 'http://localhost:8002' : '/rag-api');

const ragApi = axios.create({
  baseURL: RAG_API_BASE_URL,
  // Remove default Content-Type header to allow FormData to work correctly
  // Axios will auto-set the correct Content-Type with boundary for FormData
});

/**
 * Query RAG QA service for candidates or voting center information
 * @param {string} query - User's question in Nepali or English
 * @param {string|null} sessionId - Session ID for multi-turn conversations (optional)
 * @param {string|null} mode - Force mode: 'polling', 'candidate', or null for auto-detection
 * @returns {Promise<Object>} Response with answer, sources, intent, confidence, etc.
 */
export const queryRAG = async (query, sessionId = null, mode = null) => {
  const payload = {
    query,
    filters: {},
    top_k: 10,  // Backend limit is 20, using 10 for good performance
  };

  const response = await ragApi.post('/api/v1/chat', payload);
  return response.data;
};

/**
 * Reset or clear a RAG QA session
 * @param {string} sessionId - Session ID to reset
 * @returns {Promise<Object>} Response status
 */
export const resetRAGSession = async (sessionId) => {
  const response = await ragApi.post('/api/reset_session', { session_id: sessionId });
  return response.data;
};

/**
 * Get RAG QA service health status
 * @returns {Promise<Object>} Health check response
 */
export const checkRAGHealth = async () => {
  const response = await ragApi.get('/health');
  return response.data;
};

export default api;
