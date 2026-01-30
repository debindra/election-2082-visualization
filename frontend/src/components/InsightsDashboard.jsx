import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import {
  listElections,
  getIndependentWaveInsight,
  getCompetitionPressureInsight,
  getPartySaturationInsight,
} from '../services/api';
import YearInsights from './YearInsights';

const INSIGHTS_THRESHOLD_PERCENTILE = 0.8;

const CARD_KEYS = { independent: 'independent', competition: 'competition', party: 'party' };

const InsightsDashboard = ({ language = 'ne' }) => {
  const [availableElections, setAvailableElections] = useState([]);
  const [year, setYear] = useState(null);
  const [independentWave, setIndependentWave] = useState(null);
  const [competitionPressure, setCompetitionPressure] = useState(null);
  const [partySaturation, setPartySaturation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [maximizedCard, setMaximizedCard] = useState(null);

  useEffect(() => {
    if (!maximizedCard) return;
    const onEscape = (e) => {
      if (e.key === 'Escape') setMaximizedCard(null);
    };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, [maximizedCard]);

  useEffect(() => {
    const loadElections = async () => {
      try {
        const elections = await listElections();
        setAvailableElections(elections);
        if (elections.length > 0) {
          setYear(elections[elections.length - 1]);
        }
      } catch (err) {
        console.error('Failed to load elections for insights:', err);
        setError('Failed to load available elections');
      }
    };

    loadElections();
  }, []);

  useEffect(() => {
    const loadInsights = async () => {
      if (!year) return;
      setLoading(true);
      setError(null);

      try {
        const [indWave, compPress, partySat] = await Promise.all([
          getIndependentWaveInsight(year),
          getCompetitionPressureInsight(year),
          getPartySaturationInsight(year),
        ]);
        setIndependentWave(indWave);
        setCompetitionPressure(compPress);
        setPartySaturation(partySat);
      } catch (err) {
        console.error('Failed to load insights:', err);
        setError('Failed to load insights for the selected year');
      } finally {
        setLoading(false);
      }
    };

    loadInsights();
  }, [year]);

  const buildIndependentWaveOption = () => {
    if (!independentWave || !independentWave.districts) return null;

    const getShare = (d) => d.independent_vote_share ?? d.independent_candidate_share;
    const districts = independentWave.districts.filter(
      (d) => d.district && typeof getShare(d) === 'number' && getShare(d) > 0,
    );
    const shares = districts.map((d) => getShare(d));

    const sorted = [...districts].sort((a, b) => getShare(b) - getShare(a));

    const values = sorted.map((d) => getShare(d));
    const names = sorted.map((d) => d.district);

    let surgeThreshold = null;
    if (shares.length > 0) {
      const sortedShares = [...shares].sort((a, b) => a - b);
      const idx = Math.floor(INSIGHTS_THRESHOLD_PERCENTILE * (sortedShares.length - 1));
      surgeThreshold = sortedShares[idx];
    }

    return {
      title: {
        text: 'Independent Wave by District',
        left: 'center',
        textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
        subtext:
          independentWave.method === 'votes'
            ? 'Independent vote share per district'
            : 'Independent candidate share per district',
        subtextStyle: { fontSize: 11, color: '#1e3a5f99' },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const d = sorted[params.dataIndex];
          const value = getShare(d);
          const label =
            independentWave.method === 'votes'
              ? 'Independent vote share'
              : 'Independent candidate share';
          const extra =
            surgeThreshold !== null && value >= surgeThreshold
              ? '<br/><span style="color:#b91c1c;font-weight:600;">Independent Surge Zone</span>'
              : '';
          return `${d.district}<br/>${label}: ${value.toFixed(2)}%${extra}`;
        },
      },
      grid: { left: 80, right: 20, top: 70, bottom: 40 },
      xAxis: {
        type: 'value',
        name: '%',
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLabel: { fontSize: 10 },
      },
      series: [
        {
          type: 'bar',
          data: values,
          itemStyle: {
            color: (params) => {
              if (surgeThreshold === null) return '#1e3a5f';
              return params.data >= surgeThreshold ? '#b91c1c' : '#1e3a5f';
            },
          },
        },
      ],
    };
  };

  const buildCompetitionPressureOption = () => {
    if (!competitionPressure || !competitionPressure.districts) return null;

    const districts = [...competitionPressure.districts].filter(
      (d) => d.district,
    );
    if (districts.length === 0) return null;

    const names = districts.map((d) => d.district);
    const margins = districts.map((d) => d.avg_margin_top2 ?? 0);

    const minMargin = Math.min(...margins);
    const maxMargin = Math.max(...margins);

    return {
      title: {
        text: 'District Competition Pressure',
        left: 'center',
        textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
        subtext: 'Lower margin = higher competition pressure',
        subtextStyle: { fontSize: 11, color: '#1e3a5f99' },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const d = districts[params.dataIndex];
          return `${d.district}<br/>Avg margin (Top 2): ${(
            d.avg_margin_top2 ?? 0
          ).toFixed(2)} pts<br/>Avg margin (Top 3): ${(d.avg_margin_top3 ?? 0).toFixed(2)} pts`;
        },
      },
      grid: { left: 80, right: 20, top: 70, bottom: 40 },
      xAxis: {
        type: 'value',
        name: 'Avg margin (Top 2, pts)',
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLabel: { fontSize: 10 },
      },
      visualMap: {
        show: false,
        min: minMargin,
        max: maxMargin,
        inRange: {
          color: ['#b91c1c', '#fbbf24', '#1e3a5f'],
        },
      },
      series: [
        {
          type: 'bar',
          data: margins,
          itemStyle: {
            color: (params) => {
              const t = (params.data - minMargin) / (maxMargin - minMargin || 1);
              if (t < 0.5) return '#b91c1c';
              if (t < 0.75) return '#fbbf24';
              return '#1e3a5f';
            },
          },
        },
      ],
    };
  };

  const buildCompetitionIntensityOption = () => {
    const topDistricts = competitionPressure?.top_districts_by_candidates;
    if (!topDistricts || topDistricts.length === 0) return null;

    const districtNames = topDistricts.map((d) => d.district);
    const partyTotals = {};
    topDistricts.forEach((d) => {
      (d.by_party || []).forEach((p) => {
        partyTotals[p.party] = (partyTotals[p.party] || 0) + (p.count || 0);
      });
    });
    const partyOrder = Object.entries(partyTotals)
      .sort((a, b) => b[1] - a[1])
      .map(([p]) => p);

    const palette = [
      '#1e3a5f',
      '#b91c1c',
      '#059669',
      '#d97706',
      '#7c3aed',
      '#0d9488',
      '#dc2626',
      '#4f46e5',
      '#ca8a04',
      '#16a34a',
      '#ea580c',
      '#9333ea',
    ];
    const series = partyOrder.map((party, idx) => ({
      name: party,
      type: 'bar',
      stack: 'candidates',
      data: districtNames.map(
        (_, i) => topDistricts[i].by_party?.find((p) => p.party === party)?.count ?? 0,
      ),
      itemStyle: { color: palette[idx % palette.length] },
    }));

    return {
      title: {
        text: 'Top districts by number of candidates',
        left: 'center',
        textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
        subtext: 'Stacked by party — competition intensity',
        subtextStyle: { fontSize: 11, color: '#1e3a5f99' },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          const districtIdx = params[0]?.dataIndex;
          if (districtIdx == null) return '';
          const d = topDistricts[districtIdx];
          let lines = [d.district, `Total: ${d.total_candidates} candidates`];
          (d.by_party || []).forEach((p) => {
            lines.push(`${p.party}: ${p.count}`);
          });
          return lines.join('<br/>');
        },
      },
      legend: {
        type: 'scroll',
        bottom: 0,
        left: 'center',
        textStyle: { fontSize: 10 },
      },
      grid: { left: 80, right: 20, top: 60, bottom: 50 },
      xAxis: { type: 'value', name: 'Number of candidates' },
      yAxis: { type: 'category', data: districtNames, axisLabel: { fontSize: 10 } },
      series,
    };
  };

  const buildPartySaturationOption = () => {
    if (!partySaturation || !partySaturation.parties) return null;

    const parties = partySaturation.parties.filter(
      (p) => p.party && p.candidates != null,
    );

    const seriesData = parties.map((p) => [
      p.candidates,
      p.seats_won ?? 0,
      p.seats_contested ?? 0,
      p.party,
    ]);

    return {
      title: {
        text: 'Party Saturation vs Reach',
        left: 'center',
        textStyle: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
        subtext: 'Candidates vs seats won (bubble size = seats contested)',
        subtextStyle: { fontSize: 11, color: '#1e3a5f99' },
      },
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const [candidates, won, contested, party] = params.data;
          return `${party}<br/>Candidates: ${candidates}<br/>Seats contested: ${contested}<br/>Seats won: ${won}`;
        },
      },
      xAxis: {
        type: 'value',
        name: 'Candidates',
      },
      yAxis: {
        type: 'value',
        name: 'Seats won',
      },
      series: [
        {
          type: 'scatter',
          symbolSize: (val) => {
            const contested = val[2] || 0;
            return 10 + Math.sqrt(contested) * 3;
          },
          itemStyle: {
            color: '#1e3a5f',
            opacity: 0.8,
          },
          data: seriesData,
        },
      ],
    };
  };

  const independentOption = buildIndependentWaveOption();
  const competitionOption = buildCompetitionPressureOption();
  const competitionIntensityOption = buildCompetitionIntensityOption();
  const partyOption = buildPartySaturationOption();

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Insights Overview — always visible */}
      <section className="mb-6" aria-labelledby="insights-overview-heading">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h2 id="insights-overview-heading" className="text-xl font-bold text-[#1e3a5f]">
              Insights Overview
            </h2>
            <p className="text-sm text-[#1e3a5f]/70 mt-0.5">
              District-level independent wave, competition pressure, and party saturation for a single
              election year.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-[#1e3a5f]/80" htmlFor="insights-year-select">
              Election year:
            </label>
            <select
              id="insights-year-select"
              value={year ?? ''}
              onChange={(e) => setYear(Number(e.target.value) || null)}
              className="px-2 py-1.5 border border-[#1e3a5f]/25 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a5f] text-[#1e3a5f]"
            >
              <option value="" disabled>
                Select year
              </option>
              {availableElections.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && <div className="text-[#b91c1c] text-sm mb-3">{error}</div>}

        {loading && (
          <div className="py-8 text-center text-[#1e3a5f]/70">
            Loading overview…
          </div>
        )}

        {!loading && !year && (
          <div className="py-8 text-center text-[#1e3a5f]/70">
            Select an election year to view insights.
          </div>
        )}

        {!loading && year && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 overflow-auto">
            {independentOption && (
              <div className="bg-white rounded-xl border border-[#1e3a5f]/15 shadow-sm p-3 lg:p-4 relative">
                <button
                  type="button"
                  onClick={() => setMaximizedCard(CARD_KEYS.independent)}
                  className="absolute top-2 right-2 z-10 p-1.5 rounded-lg text-[#1e3a5f]/70 hover:text-[#1e3a5f] hover:bg-[#1e3a5f]/10 transition-colors"
                  title="Maximize full screen"
                  aria-label="Maximize full screen"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  </svg>
                </button>
                <ReactECharts option={independentOption} style={{ height: 360 }} />
              </div>
            )}
            <div className="bg-white rounded-xl border border-[#1e3a5f]/15 shadow-sm p-3 lg:p-4 relative">
              <h3 className="text-sm font-semibold text-[#1e3a5f] mb-2">District Competition Intensity</h3>
                {competitionIntensityOption ? (
                  <>
                    <button
                      type="button"
                      onClick={() => setMaximizedCard(CARD_KEYS.competition)}
                      className="absolute top-2 right-2 z-10 p-1.5 rounded-lg text-[#1e3a5f]/70 hover:text-[#1e3a5f] hover:bg-[#1e3a5f]/10 transition-colors"
                      title="Maximize full screen"
                      aria-label="Maximize full screen"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                      </svg>
                    </button>
                    {competitionIntensityOption && (
                      <ReactECharts option={competitionIntensityOption} style={{ height: 360 }} />
                    )}
                  </>
                ) : (
                  <div className="flex items-center justify-center text-[#1e3a5f]/60 text-sm py-12 px-4" style={{ minHeight: 360 }}>
                    {error
                      ? 'Competition intensity could not be loaded. Try another year.'
                      : 'No district competition intensity data for this year.'}
                  </div>
                )}
            </div>
            {/* Party Saturation vs Reach — disabled for now */}
          </div>
        )}

        {!loading && year && (!independentOption && !competitionIntensityOption) && (
          <p className="text-sm text-[#1e3a5f]/60 py-2">No overview charts for this year. Use Year Insights below.</p>
        )}
      </section>

      {maximizedCard && year && (
            <div
              className="fixed inset-0 z-50 flex flex-col bg-[#1e3a5f]/95"
              role="dialog"
              aria-modal="true"
              aria-label="Insight card full screen"
            >
              <div className="flex items-center justify-between p-3 border-b border-white/20 bg-[#1e3a5f]/90">
                <span className="text-white font-medium">
                  {maximizedCard === CARD_KEYS.independent && 'Independent Wave by District'}
                  {maximizedCard === CARD_KEYS.competition && 'District Competition Intensity'}
                  {maximizedCard === CARD_KEYS.party && 'Party Saturation vs Reach (disabled)'}
                </span>
                <button
                  type="button"
                  onClick={() => setMaximizedCard(null)}
                  className="p-2 rounded-lg text-white/80 hover:text-white hover:bg-white/20 transition-colors"
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
                  {maximizedCard === CARD_KEYS.independent && independentOption && (
                    <ReactECharts option={independentOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                  {maximizedCard === CARD_KEYS.competition && competitionIntensityOption && (
                    <ReactECharts option={competitionIntensityOption} style={{ width: '100%', height: '100%', minHeight: 400 }} />
                  )}
                  {maximizedCard === CARD_KEYS.party && partyOption && (
                    <div className="p-4 text-[#1e3a5f]/70">Party Saturation vs Reach is disabled for now.</div>
                  )}
                </div>
              </div>
            </div>
      )}

      {year && (
        <section className="mt-8 pt-6 border-t border-[#1e3a5f]/20" aria-labelledby="year-insights-heading">
          <h2 id="year-insights-heading" className="text-lg font-bold text-[#1e3a5f] mb-2">Individual Election Year Insights</h2>
          <p className="text-sm text-[#1e3a5f]/70 mb-4">
            Age demographics, education profile, party vs age, local representation, symbol recognition, and composite metrics. Filter by party, state (province), and district.
          </p>
          <YearInsights electionYear={year} language={language} />
        </section>
      )}
    </div>
  );
};

export default InsightsDashboard;

