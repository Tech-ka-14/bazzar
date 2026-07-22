import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';

export default function SGBChart({ data = [] }) {
  const chartContainerRef = useRef();
  const chartRef = useRef();
  const [chartType, setChartType] = useState('candlestick');

  useEffect(() => {
    chartRef.current = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: { background: { color: '#1a1a1a' }, textColor: '#FFD700' },
    });

    let series;
    if (chartType === 'candlestick') {
      series = chartRef.current.addCandlestickSeries({
        upColor: '#00ff00', downColor: '#ff0000',
        wickUpColor: '#00ff00', wickDownColor: '#ff0000',
      });
    } else {
      series = chartRef.current.addLineSeries({ color: '#FFD700', lineWidth: 2 });
    }

    series.setData(data);

    return () => chartRef.current.remove();
  }, [data, chartType]);

  return (
    <div className="p-4 bg-black rounded-lg border border-yellow-600">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-yellow-500">Sovereign Gold Bonds (SGB)</h2>
        <button onClick={() => setChartType(chartType === 'line' ? 'candlestick' : 'line')} className="px-3 py-1 bg-gray-800 text-yellow-500 rounded">
          Toggle {chartType === 'line' ? 'Candles' : 'Line'}
        </button>
      </div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}
