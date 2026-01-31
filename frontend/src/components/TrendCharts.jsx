import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { getTrends } from '../services/api';

const ELECTION_YEAR = 2082;

const TrendCharts = () => {
  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getTrends([ELECTION_YEAR])
      .then((data) => {
        if (!cancelled) setTrendsData(data);
      })
      .catch((err) => {
        if (!cancelled) console.error('Failed to load trends:', err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

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
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#1e3a5f99', fontSize: 10 },
        splitLine: { show: false },
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

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-[#1e3a5f]">Trends</h2>
          <p className="text-sm text-[#1e3a5f]/70">Election {ELECTION_YEAR} metrics</p>
        </div>
      </div>

      {loading && <div className="flex-1 flex items-center justify-center text-[#1e3a5f]/70 text-sm">Loading trends…</div>}

      {trendsData && trendsData.trends && Object.keys(trendsData.trends).length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 overflow-auto min-h-0">
          {Object.entries(trendsData.trends).map(([metricName, trend]) => (
            <div key={metricName} className="rounded-xl border border-[#1e3a5f]/15 bg-white p-4" role="img" aria-label={`Trend: ${metricName.replace(/_/g, ' ')}`}>
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
          No trend data available.
        </div>
      )}
    </div>
  );
};

export default TrendCharts;
