import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { getTrends, listElections } from '../services/api';

const TrendCharts = () => {
  const [trendsData, setTrendsData] = useState(null);
  const [availableElections, setAvailableElections] = useState([]);
  const [selectedYears, setSelectedYears] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadElections();
  }, []);

  const loadElections = async () => {
    try {
      const elections = await listElections();
      setAvailableElections(elections);
      const year2082 = elections.find((y) => Number(y) === 2082);
      if (year2082 != null) {
        setSelectedYears([year2082]);
      } else if (elections.length >= 2) {
        setSelectedYears(elections.slice(-2));
      }
    } catch (error) {
      console.error('Failed to load elections:', error);
    }
  };

  const loadTrends = async () => {
    if (selectedYears.length < 1) return;

    setLoading(true);
    try {
      const data = await getTrends(selectedYears);
      setTrendsData(data);
    } catch (error) {
      console.error('Failed to load trends:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedYears.length > 0) {
      loadTrends();
    }
  }, [selectedYears]);

  const getChartOption = (metricName, dataPoints) => {
    const title = metricName.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    return {
      title: {
        text: title,
        left: 'center',
        textStyle: { fontSize: 13, fontWeight: 600, color: '#1e3a5f' },
      },
      tooltip: { trigger: 'axis' },
      grid: { left: 48, right: 16, top: 40, bottom: 28 },
      xAxis: {
        type: 'category',
        data: dataPoints.map((dp) => dp.year),
        axisLabel: { color: '#1e3a5f99', fontSize: 10 },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#1e3a5f99', fontSize: 10 },
        splitLine: { lineStyle: { color: '#1e3a5f20', type: 'dashed' } },
      },
      series: [
        {
          data: dataPoints.map((dp) => dp.value),
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: { color: '#b91c1c' },
          lineStyle: { width: 2 },
          areaStyle: { color: 'rgba(220, 20, 60, 0.1)' },
        },
      ],
    };
  };

  const toggleYear = (y) => {
    if (selectedYears.includes(y)) {
      if (selectedYears.length > 1) setSelectedYears(selectedYears.filter((yr) => yr !== y));
    } else {
      setSelectedYears([...selectedYears, y].sort((a, b) => a - b));
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-[#1e3a5f]">Trends</h2>
          <p className="text-sm text-[#1e3a5f]/70">Compare metrics across election years</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {availableElections.map((y) => (
            <button
              key={y}
              type="button"
              onClick={() => toggleYear(y)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedYears.includes(y)
                  ? 'bg-[#b91c1c] text-white'
                  : 'bg-[#1e3a5f]/10 text-[#1e3a5f]/80 hover:bg-[#1e3a5f]/20'
              }`}
            >
              {y}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="flex-1 flex items-center justify-center text-[#1e3a5f]/70 text-sm">Loading trends…</div>}

      {trendsData && trendsData.trends && Object.keys(trendsData.trends).length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 overflow-auto min-h-0">
          {Object.entries(trendsData.trends).map(([metricName, trend]) => (
            <div key={metricName} className="rounded-xl border border-[#1e3a5f]/15 bg-white p-4">
              <ReactECharts
                option={getChartOption(metricName, trend.data_points)}
                style={{ height: 280 }}
              />
            </div>
          ))}
        </div>
      )}

      {!trendsData && !loading && (
        <div className="flex-1 flex items-center justify-center text-[#1e3a5f]/70 text-sm">
          Select at least one election year to view trends.
        </div>
      )}
    </div>
  );
};

export default TrendCharts;
