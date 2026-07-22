import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

export default function RepoRatesChart({ indiaRepoData = [], usFedData = [] }) {
  const chartContainerRef = useRef();
  const chartRef = useRef();

  useEffect(() => {
    chartRef.current = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#FFD700',
      },
      grid: {
        vertLines: { color: '#333' },
        horzLines: { color: '#333' },
      },
      rightPriceScale: {
        borderColor: '#FFD700',
        autoScale: true,
      },
      timeScale: {
        borderColor: '#FFD700',
      },
    });

    // Series 1: India RBI Repo Rate
    const rbiSeries = chartRef.current.addLineSeries({
      color: '#FFD700', // Gold for India
      lineWidth: 2,
      title: 'RBI Repo Rate',
    });
    rbiSeries.setData(indiaRepoData);

    // Series 2: US Federal Reserve Rate
    const fedSeries = chartRef.current.addLineSeries({
      color: '#FFFFFF', // White for US Fed
      lineWidth: 2,
      title: 'US Fed Rate',
    });

    // Ensure comparisonData exists before setting
    if (usFedData && usFedData.length > 0) {
      fedSeries.setData(usFedData);
    }

    return () => chartRef.current.remove();
  }, [indiaRepoData, usFedData]);

  return (
    <div className="p-4 bg-black rounded-lg border border-yellow-600">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-yellow-500">Global Repo Rates: RBI vs US Fed</h2>
        <div className="flex gap-4 text-sm">
          <span className="text-yellow-500">● RBI Rate (Gold)</span>
          <span className="text-white">● Fed Rate (White)</span>
        </div>
      </div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}
