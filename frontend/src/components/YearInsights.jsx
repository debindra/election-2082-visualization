import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { getFilterOptions, getYearInsights } from '../services/api';

const ELECTION_YEAR = 2082;

const CHART_COLORS = ['#1e3a5f', '#b91c1c', '#0d9488', '#f59e0b', '#6366f1', '#ec4899'];

const CARD_KEYS = { age: 'age', gender: 'gender', education: 'education', partyAge: 'partyAge', partyGender: 'partyGender', local: 'local', symbol: 'symbol' };
// Priority order: 1 = Power insights, 2 = Demographics, 3 = Local, 4 = Education, 5 = UX
const CHART_PRIORITY_ORDER = ['partyAge', 'partyGender', 'age', 'gender', 'local', 'education', 'symbol'];
const CARD_TITLES = {
  partyAge: '1. Party vs Age Trend (Power Insight)',
  partyGender: '2. Party vs Gender (Power Insight)',
  age: '3. Age Demographics of Candidates',
  gender: '4. Gender Demographics',
  local: '5. Birthplace vs Contest (Local Representation)',
  education: '6. Education Profile Insight',
  symbol: '7. Symbol Recognition (UX Insight)',
};

// Indicator metadata: range, bands, description, and interpretation for composite metrics
const COMPOSITE_INDICATOR_META = {
  education_index: {
    label: 'Education Index',
    range: '1.0 → 4.0',
    description: 'Average education level of candidates, mapped to numeric weights.',
    bands: [
      { label: 'Low (1.0 – 1.5)', meaning: 'Mostly secondary-level education' },
      { label: 'Medium (1.6 – 2.5)', meaning: 'Intermediate to Bachelor dominated (common in Nepal)' },
      { label: 'High (2.6 – 4.0)', meaning: 'Strong presence of Bachelor & Master-level candidates' },
    ],
    getInterpretation: (v) => {
      if (v == null) return null;
      if (v <= 1.5) return 'Mostly secondary-level education';
      if (v <= 2.5) return 'Intermediate to Bachelor dominated, limited advanced degrees';
      return 'Strong Bachelor & Master-level candidate presence';
    },
  },
  local_percentage: {
    label: 'Local Representation (%)',
    range: '0% → 100%',
    description: 'Percentage of candidates contesting from their birth district or permanent address district.',
    bands: [
      { label: 'Low (0–40%)', meaning: 'Mostly outsider candidates' },
      { label: 'Moderate (41–70%)', meaning: 'Mixed local & non-local representation' },
      { label: 'High (71–100%)', meaning: 'Strong local-rooted candidacy' },
    ],
    getInterpretation: (v) => {
      if (v == null) return null;
      if (v <= 40) return 'Mostly outsider candidates';
      if (v <= 70) return 'Mixed local & non-local representation';
      return 'Strong local ties; outsiders are a minority';
    },
  },
  symbol_coverage: {
    label: 'Symbol Diversity (%)',
    range: '0% → 100% (in practice usually under 20%)',
    description: 'How many unique or rare symbols exist compared to total symbols used.',
    bands: [
      { label: 'Very Low (0–5%)', meaning: 'Heavy symbol repetition, possible voter confusion' },
      { label: 'Moderate (6–15%)', meaning: 'Some variety, still crowded' },
      { label: 'High (16%+)', meaning: 'Strong visual differentiation' },
    ],
    getInterpretation: (v) => {
      if (v == null) return null;
      if (v <= 5) return 'Symbol reuse very high; ballots may feel visually crowded';
      if (v <= 15) return 'Some variety, still crowded';
      return 'Strong visual differentiation';
    },
  },
  party_fragmentation_score: {
    label: 'Party Fragmentation Score',
    range: '0 → 100',
    description: 'How divided the political field is (number of parties, independents, candidate distribution balance).',
    bands: [
      { label: 'Low (0–30)', meaning: 'Dominated by few parties' },
      { label: 'Medium (31–60)', meaning: 'Competitive but structured' },
      { label: 'High (61–100)', meaning: 'Highly fragmented, vote-splitting likely' },
    ],
    getInterpretation: (v) => {
      if (v == null) return null;
      if (v <= 30) return 'Dominated by few parties';
      if (v <= 60) return 'Competitive but structured';
      return 'Highly fragmented; harder to predict outcomes';
    },
  },
  independent_influence_index: {
    label: 'Independent Influence Index',
    range: '0 → 100',
    description: 'Strength of independent candidates relative to parties (% independents, concentration, growth).',
    bands: [
      { label: 'Low (0–25)', meaning: 'Independents are symbolic' },
      { label: 'Moderate (26–50)', meaning: 'Independents affect outcomes' },
      { label: 'High (51–100)', meaning: 'Independents are structurally influential' },
    ],
    getInterpretation: (v) => {
      if (v == null) return null;
      if (v <= 25) return 'Independents are largely symbolic';
      if (v <= 50) return 'Independents affect outcomes';
      return 'Parties are no longer the only power centers';
    },
  },
  female_representation_percentage: {
    label: 'Female Representation (%)',
    range: '0% → 100%',
    description: 'Share of female candidates in the selection.',
    bands: [
      { label: 'Low (0–15%)', meaning: 'Significant gender gap' },
      { label: 'Moderate (16–30%)', meaning: 'Improving but below parity' },
      { label: 'High (31%+)', meaning: 'Strong female representation' },
    ],
    getInterpretation: (v) => {
      if (v == null) return null;
      if (v <= 15) return 'Significant gender gap';
      if (v <= 30) return 'Improving but below parity';
      return 'Strong female representation';
    },
  },
  gender_parity_index: {
    label: 'Gender Parity Index',
    range: '0 → 1 (1 = perfect parity)',
    description: 'Ratio of smaller gender share to 50%; 1.0 means 50/50.',
    bands: [
      { label: 'Low (0–0.2)', meaning: 'Strong gender imbalance' },
      { label: 'Moderate (0.21–0.5)', meaning: 'Modest progress toward balance' },
      { label: 'High (0.51–1.0)', meaning: 'Strong progress toward parity' },
    ],
    getInterpretation: (v) => {
      if (v == null) return null;
      if (v <= 0.2) return 'Strong gender imbalance';
      if (v <= 0.5) return 'Modest progress toward balance';
      return 'Strong progress toward parity';
    },
  },
  youth_representation_score: {
    label: 'Youth Representation Score',
    range: '0% → 100%',
    description: 'Share of candidates below the youth threshold (e.g. under 40 years).',
    bands: [
      { label: 'Low (0–20%)', meaning: 'Aging leadership' },
      { label: 'Moderate (21–40%)', meaning: 'Balanced generational mix' },
      { label: 'High (41%+)', meaning: 'Strong youth presence' },
    ],
    getInterpretation: (v) => {
      if (v == null) return null;
      if (v <= 20) return 'Aging leadership';
      if (v <= 40) return 'Balanced generational mix';
      return 'Strong youth presence; indicates leadership renewal';
    },
  },
  candidate_count: {
    label: 'Candidates',
    range: null,
    description: 'Total number of candidates in the current selection (year/filter).',
    bands: [],
    getInterpretation: () => null,
  },
  winner_count: {
    label: 'Winners',
    range: null,
    description: 'Number of candidates who won in their constituency.',
    bands: [],
    getInterpretation: () => null,
  },
  avg_vote_share: {
    label: 'Avg vote share',
    range: '0% → 100%',
    description: 'Average vote share among candidates (where vote data is available).',
    bands: [],
    getInterpretation: () => null,
  },
  avg_margin_winner: {
    label: 'Avg winner margin',
    range: 'Points',
    description: 'Average margin (vote-share gap) between winner and runner-up in contested races.',
    bands: [],
    getInterpretation: () => null,
  },
};

const YearInsights = ({ electionYear: propYear, province: propProvince, district: propDistrict, party: propParty, gender: propGender, language = 'ne' }) => {
  const [year, setYear] = useState(propYear ?? ELECTION_YEAR);
  const [province, setProvince] = useState(propProvince ?? null);
  const [district, setDistrict] = useState(propDistrict ?? null);
  const [party, setParty] = useState(propParty ?? null);
  const [gender, setGender] = useState(propGender ?? null);
  const [filterOptions, setFilterOptions] = useState({ provinces: [], districts: [], parties: [] });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [maximizedCard, setMaximizedCard] = useState(null);

  useEffect(() => {
    if (propYear !== undefined) setYear(propYear);
    if (propProvince !== undefined) setProvince(propProvince);
    if (propDistrict !== undefined) setDistrict(propDistrict);
    if (propParty !== undefined) setParty(propParty);
    if (propGender !== undefined) setGender(propGender);
  }, [propYear, propProvince, propDistrict, propParty, propGender]);

  useEffect(() => {
    if (!year) return;
    const load = async () => {
      setError(null);
      try {
        const options = await getFilterOptions(year, province || null, district || null);
        setFilterOptions(options);
      } catch (e) {
        console.error(e);
      }
    };
    load();
  }, [year, province, district]);

  useEffect(() => {
    if (!year) return;
    setLoading(true);
    setError(null);
    getYearInsights(year, { province: province || null, district: district || null, party: party || null, gender: gender || null })
      .then(setData)
      .catch((e) => {
        setError(e?.message || 'Failed to load year insights');
        setData(null);
      })
      .finally(() => setLoading(false));
  }, [year, province, district, party, gender]);

  useEffect(() => {
    if (!maximizedCard) return;
    const onEscape = (e) => {
      if (e.key === 'Escape') setMaximizedCard(null);
    };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, [maximizedCard]);


  // 1. Age Demographics — horizontal bar
  const ageOption = data?.age_demographics?.bands?.length
    ? {
        title: {
          text: '1. Age Demographics of Candidates',
          left: 'center',
          textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
          subtext: data.age_demographics.total_with_age
            ? `Avg: ${data.age_demographics.average_age ?? '—'} yrs · Median: ${data.age_demographics.median_age ?? '—'} yrs`
            : '',
          subtextStyle: { fontSize: 11, color: '#1e3a5f99' },
        },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 60, right: 40, top: 55, bottom: 30 },
        xAxis: { type: 'value', name: 'Count', splitLine: { show: false } },
        yAxis: {
          type: 'category',
          data: data.age_demographics.bands.map((b) => b.band),
          axisLabel: { fontSize: 11 },
          splitLine: { show: false },
        },
        series: [
          {
            type: 'bar',
            data: data.age_demographics.bands.map((b) => b.count),
            itemStyle: {
              color: (params) => CHART_COLORS[params.dataIndex % CHART_COLORS.length],
            },
          },
        ],
      }
    : null;

  // 2. Gender Demographics — pie (when data available)
  const genderOption = data?.gender_demographics?.distribution?.length
    ? {
        title: {
          text: '4. Gender Demographics',
          left: 'center',
          textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
          subtext: data.gender_demographics.female_percentage != null
            ? `Female: ${data.gender_demographics.female_percentage}% · Parity: ${(data.gender_demographics.gender_parity_index ?? 0).toFixed(2)}`
            : data.gender_demographics.power_insight || '',
          subtextStyle: { fontSize: 11, color: '#1e3a5f99' },
        },
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        series: [
          {
            type: 'pie',
            radius: ['40%', '65%'],
            center: ['50%', '55%'],
            data: data.gender_demographics.distribution.map((d, i) => ({
              value: d.count,
              name: d.gender === 'M' ? 'Male' : d.gender === 'F' ? 'Female' : d.gender,
              itemStyle: { color: d.gender === 'F' ? '#ec4899' : d.gender === 'M' ? '#1e3a5f' : CHART_COLORS[(i + 2) % CHART_COLORS.length] },
            })),
            label: { fontSize: 11 },
          },
        ],
      }
    : null;

  // Party vs Gender — horizontal bar
  const partyGenderOption = data?.party_vs_gender?.parties?.length
    ? (() => {
        const parties = data.party_vs_gender.parties.filter((p) => (p.female_percentage ?? 0) > 0).slice(0, 15);
        if (parties.length === 0) return null;
        return {
          title: {
            text: '2. Party vs Gender (Power Insight)',
            left: 'center',
            textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
            subtext: data.party_vs_gender.power_insight || '',
            subtextStyle: { fontSize: 10, color: '#1e3a5f99' },
          },
          tooltip: {
            trigger: 'axis',
            formatter: (params) => {
              const i = params[0].dataIndex;
              const p = parties[i];
              return `${p.party}<br/>Female: ${p.female_percentage}%<br/>Candidates: ${p.candidate_count}`;
            },
          },
          grid: { left: 120, right: 60, top: 70, bottom: 30 },
          xAxis: { type: 'value', name: 'Female %', min: 0, max: 100, splitLine: { show: false } },
          yAxis: {
            type: 'category',
            data: parties.map((p) => (p.party.length > 18 ? p.party.slice(0, 18) + '…' : p.party)),
            axisLabel: { fontSize: 10 },
            splitLine: { show: false },
          },
          series: [
            {
              type: 'bar',
              data: parties.map((p) => p.female_percentage),
              itemStyle: { color: '#ec4899' },
            },
          ],
        };
      })()
    : null;

  // 3. Education Profile — bar (or pie)
  const educationOption = data?.education_profile?.distribution?.length
    ? {
        title: {
          text: '2. Education Profile Insight',
          left: 'center',
          textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
          subtext: data.education_profile.average_index != null
            ? `Education index: ${data.education_profile.average_index}`
            : '',
          subtextStyle: { fontSize: 11, color: '#1e3a5f99' },
        },
        tooltip: {
          trigger: 'item',
          formatter: (p) => {
            const d = data.education_profile.distribution[p.dataIndex];
            return `${d.level}<br/>Count: ${d.count}<br/>${d.percentage}%`;
          },
        },
        grid: { left: 80, right: 20, top: 55, bottom: 80 },
        xAxis: {
          type: 'category',
          data: data.education_profile.distribution.map((d) =>
            d.level.length > 12 ? d.level.slice(0, 12) + '…' : d.level
          ),
          axisLabel: { rotate: 35, fontSize: 10 },
          splitLine: { show: false },
        },
        yAxis: { type: 'value', name: 'Count', splitLine: { show: false } },
        series: [
          {
            type: 'bar',
            data: data.education_profile.distribution.map((d) => d.count),
            itemStyle: {
              color: (params) => CHART_COLORS[params.dataIndex % CHART_COLORS.length],
            },
          },
        ],
      }
    : null;

  // 4. Party vs Age — horizontal bar + power insight
  const partyAgeOption = data?.party_vs_age?.parties?.length
    ? (() => {
        const parties = data.party_vs_age.parties.filter((p) => p.average_age != null).slice(0, 20);
        return {
          title: {
            text: '3. Party vs Age Trend (Power Insight)',
            left: 'center',
            textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
            subtext: data.party_vs_age.power_insight || '',
            subtextStyle: { fontSize: 10, color: '#1e3a5f99' },
          },
          tooltip: {
            trigger: 'axis',
            formatter: (params) => {
              const i = params[0].dataIndex;
              const p = data.party_vs_age.parties[i];
              return `${p.party}<br/>Avg age: ${p.average_age} yrs<br/>Candidates: ${p.candidate_count}`;
            },
          },
          grid: { left: 120, right: 60, top: 70, bottom: 30 },
          xAxis: { type: 'value', name: 'Avg age (yrs)', min: 25, max: 75, splitLine: { show: false } },
          yAxis: {
            type: 'category',
            data: parties.map((p) => (p.party.length > 18 ? p.party.slice(0, 18) + '…' : p.party)),
            axisLabel: { fontSize: 10 },
            splitLine: { show: false },
          },
          series: [
            {
              type: 'bar',
              data: parties.map((p) => p.average_age),
              itemStyle: { color: '#b91c1c' },
            },
          ],
        };
      })()
    : null;

  // 5. Birthplace vs Contest — donut (Local vs Outsider)
  const localOption =
    data?.birthplace_vs_contest && (data.birthplace_vs_contest.local_count + data.birthplace_vs_contest.outsider_count) > 0
      ? {
          title: {
            text: '4. Birthplace vs Contest (Local Representation)',
            left: 'center',
            textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
            subtext: `Local: ${data.birthplace_vs_contest.local_percentage ?? 0}%`,
            subtextStyle: { fontSize: 11, color: '#1e3a5f99' },
          },
          tooltip: { trigger: 'item' },
          series: [
            {
              type: 'pie',
              radius: ['40%', '65%'],
              center: ['50%', '55%'],
              data: [
                {
                  value: data.birthplace_vs_contest.local_count,
                  name: 'Local (contest in birth district)',
                  itemStyle: { color: '#0d9488' },
                },
                {
                  value: data.birthplace_vs_contest.outsider_count,
                  name: 'Outsider (contest elsewhere)',
                  itemStyle: { color: '#f59e0b' },
                },
              ],
              label: { fontSize: 11 },
            },
          ],
        }
      : null;

  // 6. Symbol Recognition — horizontal bar (top symbols)
  const symbolOption = data?.symbol_recognition?.symbols?.length
    ? {
        title: {
          text: '5. Symbol Recognition (UX Insight)',
          left: 'center',
          textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
          subtext: data.symbol_recognition.ux_insight || '',
          subtextStyle: { fontSize: 10, color: '#1e3a5f99' },
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const i = params[0].dataIndex;
            const s = data.symbol_recognition.symbols[i];
            const partyLine = s.party_name ? `${s.party_name}<br/>` : '';
            return `${partyLine}${s.symbol}<br/>Candidates: ${s.candidate_count}<br/>${s.percentage}%`;
          },
        },
        grid: { left: 100, right: 30, top: 65, bottom: 30 },
        xAxis: { type: 'value', name: 'Candidates', splitLine: { show: false } },
        yAxis: {
          type: 'category',
          data: data.symbol_recognition.symbols.map((s) =>
            s.symbol.length > 15 ? s.symbol.slice(0, 15) + '…' : s.symbol
          ),
          axisLabel: { fontSize: 10 },
          splitLine: { show: false },
        },
        series: [
          {
            type: 'bar',
            data: data.symbol_recognition.symbols.map((s) => s.candidate_count),
            itemStyle: { color: '#6366f1' },
          },
        ],
      }
    : null;

  // 7. Composite metrics — KPI cards + summary (no ECharts)
  const composite = data?.composite_metrics;

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-wrap items-end gap-2 sm:gap-3 mb-4">
        <div className="w-full sm:w-auto min-w-0 sm:min-w-[120px]">
          <label className="block text-xs text-[#1e3a5f]/70 mb-1">Province (state)</label>
          <select
            value={province ?? ''}
            onChange={(e) => {
              setProvince(e.target.value || null);
              setDistrict(null);
            }}
            className="w-full sm:w-auto min-w-0 px-2 py-2 sm:py-1.5 border border-[#1e3a5f]/25 rounded-md text-sm text-[#1e3a5f] focus:ring-2 focus:ring-[#1e3a5f] touch-manipulation"
          >
            <option value="">All</option>
            {(filterOptions.provinces || []).map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <div className="w-full sm:w-auto min-w-0 sm:min-w-[120px]">
          <label className="block text-xs text-[#1e3a5f]/70 mb-1">District</label>
          <select
            value={district ?? ''}
            onChange={(e) => setDistrict(e.target.value || null)}
            className="w-full sm:w-auto min-w-0 px-2 py-2 sm:py-1.5 border border-[#1e3a5f]/25 rounded-md text-sm text-[#1e3a5f] focus:ring-2 focus:ring-[#1e3a5f] touch-manipulation"
          >
            <option value="">All</option>
            {(filterOptions.districts || []).map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
        <div className="w-full sm:w-auto min-w-0 sm:min-w-[140px]">
          <label className="block text-xs text-[#1e3a5f]/70 mb-1">Party</label>
          <select
            value={party ?? ''}
            onChange={(e) => setParty(e.target.value || null)}
            className="w-full sm:w-auto min-w-0 px-2 py-2 sm:py-1.5 border border-[#1e3a5f]/25 rounded-md text-sm text-[#1e3a5f] focus:ring-2 focus:ring-[#1e3a5f] touch-manipulation"
          >
            <option value="">All</option>
            {(filterOptions.parties || []).map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <div className="w-full sm:w-auto min-w-0 sm:min-w-[100px]">
          <label className="block text-xs text-[#1e3a5f]/70 mb-1">Gender</label>
          <select
            value={gender ?? ''}
            onChange={(e) => setGender(e.target.value || null)}
            className="w-full sm:w-auto min-w-0 px-2 py-2 sm:py-1.5 border border-[#1e3a5f]/25 rounded-md text-sm text-[#1e3a5f] focus:ring-2 focus:ring-[#1e3a5f] touch-manipulation"
          >
            <option value="">All</option>
            {(filterOptions.genders || ['M', 'F']).map((g) => (
              <option key={g} value={g}>{g === 'M' ? 'Male' : g === 'F' ? 'Female' : g}</option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 text-red-800 text-sm">{error}</div>
      )}

      {loading && (
        <div className="flex-1 flex items-center justify-center text-[#1e3a5f]/70">Loading year insights…</div>
      )}

      {!loading && data && (
        <>
          <p className="text-xs text-[#1e3a5f]/70 mb-2 font-medium" aria-hidden="true">
            Main story: Party vs age and gender power insights, then demographics and representation.
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 overflow-x-hidden min-w-0">
            {CHART_PRIORITY_ORDER.map((key) => {
              const option = key === 'partyAge' ? partyAgeOption : key === 'partyGender' ? partyGenderOption : key === 'age' ? ageOption : key === 'gender' ? genderOption : key === 'local' ? localOption : key === 'education' ? educationOption : symbolOption;
              if (!option) return null;
              const isWide = key === 'partyAge' || key === 'partyGender';
              return (
                <div
                  key={key}
                  className={`bg-white rounded-xl border border-[#1e3a5f]/15 shadow-sm p-3 relative min-w-0 ${isWide ? 'lg:col-span-2' : ''}`}
                >
                <button
                  type="button"
                  onClick={() => setMaximizedCard(CARD_KEYS[key])}
                  className="absolute top-2 right-2 z-10 p-1.5 rounded-lg text-[#1e3a5f]/70 hover:text-[#1e3a5f] hover:bg-[#1e3a5f]/10 transition-colors"
                  title="Maximize full screen"
                  aria-label="Maximize full screen"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  </svg>
                </button>
                <div role="img" aria-label={CARD_TITLES[key] || key} className="min-w-0 overflow-hidden">
                  <ReactECharts option={option} style={{ height: isWide ? 'min(320px, 45vh)' : 'min(280px, 40vh)', width: '100%' }} className="min-h-[220px]" />
                </div>
              </div>
            );
            })}
          </div>

          {maximizedCard && (
            <div
              className="fixed inset-0 z-50 flex flex-col bg-[#1e3a5f]/95"
              role="dialog"
              aria-modal="true"
              aria-label="Year insight chart full screen"
            >
              <div className="flex items-center justify-between p-3 sm:p-4 border-b border-white/20 bg-[#1e3a5f]/90 gap-2 min-h-[44px]">
                <span className="text-white font-medium truncate text-sm sm:text-base">
                  {CARD_TITLES[maximizedCard] || maximizedCard}
                </span>
                <button
                  type="button"
                  onClick={() => setMaximizedCard(null)}
                  className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg text-white/80 hover:text-white hover:bg-white/20 transition-colors touch-manipulation"
                  title="Close full screen"
                  aria-label="Close full screen"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="flex-1 flex items-center justify-center p-4 min-h-0">
                <div className="w-full h-full max-w-6xl bg-white rounded-xl shadow-xl overflow-hidden flex items-center justify-center">
                  {maximizedCard === CARD_KEYS.age && ageOption && (
                    <ReactECharts option={ageOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                  {maximizedCard === CARD_KEYS.gender && genderOption && (
                    <ReactECharts option={genderOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                  {maximizedCard === CARD_KEYS.partyGender && partyGenderOption && (
                    <ReactECharts option={partyGenderOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                  {maximizedCard === CARD_KEYS.education && educationOption && (
                    <ReactECharts option={educationOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                  {maximizedCard === CARD_KEYS.partyAge && partyAgeOption && (
                    <ReactECharts option={partyAgeOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                  {maximizedCard === CARD_KEYS.local && localOption && (
                    <ReactECharts option={localOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                  {maximizedCard === CARD_KEYS.symbol && symbolOption && (
                    <ReactECharts option={symbolOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                </div>
              </div>
            </div>
          )}

          {composite && (
            <div className="mt-4 bg-white rounded-xl border border-[#1e3a5f]/15 shadow-sm p-4" role="region" aria-labelledby="composite-metrics-heading">
              <h3 id="composite-metrics-heading" className="text-sm font-semibold text-[#1e3a5f] mb-1">How inclusive was this election?</h3>
              <p className="text-xs text-[#1e3a5f]/70 mb-3">Key metrics: female and youth representation, local roots, education, gender parity.</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 mb-3">
                {[
                  { key: 'female_representation_percentage', label: 'Female Representation', value: composite.female_representation_percentage, suffix: '%', className: 'bg-[#ec4899]/15 text-[#ec4899]', labelClass: 'text-[#ec4899]/80' },
                  { key: 'youth_representation_score', label: 'Youth Representation Score', value: composite.youth_representation_score, suffix: '%', className: 'bg-[#0d9488]/15 text-[#0d9488]', labelClass: 'text-[#0d9488]/80' },
                  { key: 'local_percentage', label: 'Local representation', value: composite.local_percentage, suffix: '%', className: 'bg-[#0d9488]/15 text-[#0d9488]', labelClass: 'text-[#0d9488]/80' },
                  { key: 'education_index', label: 'Education index', value: composite.education_index, suffix: '', className: 'bg-[#1e3a5f]/10 text-[#1e3a5f]', labelClass: 'text-[#1e3a5f]/70' },
                  { key: 'gender_parity_index', label: 'Gender Parity Index', value: composite.gender_parity_index, suffix: '', className: 'bg-[#ec4899]/10 text-[#be185d]', labelClass: 'text-[#be185d]/80' },
                  { key: 'winner_count', label: 'Winners', value: composite.winner_count, suffix: '', className: 'bg-[#b91c1c]/10 text-[#b91c1c]', labelClass: 'text-[#b91c1c]/80' },
                  { key: 'independent_influence_index', label: 'Independent Influence Index', value: composite.independent_influence_index, suffix: '', className: 'bg-[#f59e0b]/15 text-[#d97706]', labelClass: 'text-[#d97706]/80' },
                  { key: 'party_fragmentation_score', label: 'Party Fragmentation Score', value: composite.party_fragmentation_score, suffix: '', className: 'bg-[#6366f1]/10 text-[#6366f1]', labelClass: 'text-[#6366f1]/80' },
                  { key: 'avg_vote_share', label: 'Avg vote share', value: composite.avg_vote_share, suffix: '%', className: 'bg-[#1e3a5f]/10 text-[#1e3a5f]', labelClass: 'text-[#1e3a5f]/70' },
                  { key: 'avg_margin_winner', label: 'Avg winner margin', value: composite.avg_margin_winner, suffix: ' pts', className: 'bg-[#1e3a5f]/10 text-[#1e3a5f]', labelClass: 'text-[#1e3a5f]/70' },
                  { key: 'symbol_coverage', label: 'Symbol diversity', value: composite.symbol_coverage, suffix: '%', className: 'bg-[#1e3a5f]/10 text-[#1e3a5f]', labelClass: 'text-[#1e3a5f]/70' },
                ].filter(({ value }) => value != null).map(({ key, label, value, suffix, className, labelClass }) => {
                  const meta = COMPOSITE_INDICATOR_META[key];
                  const interpretation = meta?.getInterpretation?.(value) ?? null;
                  const hasTooltip = meta?.description != null;
                  return (
                    <div key={key} tabIndex={hasTooltip ? 0 : undefined} className={`relative group w-full min-w-0 ${hasTooltip ? 'cursor-help focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1e3a5f]/40 focus-visible:ring-offset-1 rounded-lg' : ''}`}>
                      <div className={`px-3 py-2 rounded-lg ${className}`}>
                        <span className={`text-xs ${labelClass}`}>{label}</span>
                        {interpretation ? (
                          <>
                            <div className="font-semibold text-sm leading-tight max-w-[180px]" title={interpretation}>
                              {interpretation}
                            </div>
                            <div className="text-[10px] mt-0.5 opacity-85">{value}{suffix}</div>
                          </>
                        ) : (
                          <div className="font-semibold">{value}{suffix}</div>
                        )}
                      </div>
                      {hasTooltip && (
                        <div className="absolute left-0 bottom-full z-20 mb-1 hidden group-hover:block group-focus-within:block w-72 max-w-[calc(100vw-2rem)] p-3 bg-[#1e3a5f] text-white text-left rounded-lg shadow-xl border border-white/10">
                          <div className="text-xs font-semibold mb-1">{meta.label}</div>
                          <p className="text-[11px] text-white/90 mb-2">{meta.description}</p>
                          {meta.range && (
                            <p className="text-[11px] text-white/80 mb-2"><strong>Value range:</strong> {meta.range}</p>
                          )}
                          {meta.bands?.length > 0 && (
                            <div className="mb-2">
                              <p className="text-[11px] font-medium mb-1">Interpretation</p>
                              <ul className="text-[10px] text-white/85 space-y-0.5 list-disc list-inside">
                                {meta.bands.map((b, i) => (
                                  <li key={i}><span className="font-medium">{b.label}</span> → {b.meaning}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {interpretation && (
                            <p className="text-[11px] border-t border-white/20 pt-2 mt-1">
                              <strong>Your value ({value}{suffix}):</strong> {interpretation}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {data?.geographic_indicators && (
            <div className="mt-4 bg-white rounded-xl border border-[#1e3a5f]/15 shadow-sm p-4">
              <h3 className="text-sm font-semibold text-[#1e3a5f] mb-3">9. Geographic Indicators</h3>
              <div className="space-y-4">
                {/* Gender 0 districts */}
                <div>
                  <h4 className="text-xs font-medium text-[#ec4899] mb-1.5">
                    {language === 'en' ? 'Districts with zero female candidates' : 'शुन्य महिला उम्मेदवार भएका जिल्ला'}
                    {(data.geographic_indicators.gender_zero_count ?? 0) > 0 && (
                      <span className="text-[#1e3a5f]/70 font-normal ml-1">
                        ({data.geographic_indicators.gender_zero_count})
                      </span>
                    )}
                  </h4>
                  {(data.geographic_indicators.gender_zero_count ?? 0) === 0 ? (
                    <p className="text-xs text-[#1e3a5f]/70">
                      {language === 'en' ? 'All districts have at least one female candidate.' : 'सबै जिल्लामा कम्तीमा एक महिला उम्मेदवार छन्।'}
                    </p>
                  ) : (
                    <p className="text-xs text-[#1e3a5f]/85">
                      {(data.geographic_indicators.gender_zero_districts || []).join(', ')}
                    </p>
                  )}
                </div>

                {/* Top 5 high female concentration districts */}
                {(data.geographic_indicators.top_female_districts || []).length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium text-[#ec4899] mb-1.5">
                      {language === 'en' ? 'High female concentration (top 5 districts)' : 'उच्च महिला एकाग्रता (शीर्ष ५ जिल्ला)'}
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {(data.geographic_indicators.top_female_districts || []).map((d, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center px-2.5 py-1 rounded-lg bg-[#ec4899]/15 text-[#1e3a5f] text-xs"
                          title={d?.district}
                        >
                          {d?.district ?? ''}
                          {d?.province && <span className="text-[#1e3a5f]/60 ml-1">({d.province})</span>}
                          <span className="font-semibold text-[#ec4899] ml-1">{d?.female_percentage ?? 0}%</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* High and low state female concentration */}
                {((data.geographic_indicators.state_female_high || []).length > 0 || (data.geographic_indicators.state_female_low || []).length > 0) && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {(data.geographic_indicators.state_female_high || []).length > 0 && (
                      <div>
                        <h4 className="text-xs font-medium text-[#0d9488] mb-1.5">
                          {language === 'en' ? 'High female concentration (states)' : 'उच्च महिला एकाग्रता (प्रदेश)'}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {(data.geographic_indicators.state_female_high || []).map((s, i) => (
                            <span key={i} className="inline-flex items-center px-2 py-1 rounded-lg bg-[#0d9488]/15 text-[#1e3a5f] text-xs">
                              {s.province} <span className="font-semibold text-[#0d9488] ml-1">{s.female_percentage}%</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {(data.geographic_indicators.state_female_low || []).length > 0 && (
                      <div>
                        <h4 className="text-xs font-medium text-[#6366f1] mb-1.5">
                          {language === 'en' ? 'Low female concentration (states)' : 'न्यून महिला एकाग्रता (प्रदेश)'}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {(data.geographic_indicators.state_female_low || []).map((s, i) => (
                            <span key={i} className="inline-flex items-center px-2 py-1 rounded-lg bg-[#6366f1]/15 text-[#1e3a5f] text-xs">
                              {s.province} <span className="font-semibold text-[#6366f1] ml-1">{s.female_percentage}%</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {!loading && !data && (
        <div className="flex-1 flex items-center justify-center text-[#1e3a5f]/70">
          No insights data available.
        </div>
      )}
    </div>
  );
};

export default YearInsights;
