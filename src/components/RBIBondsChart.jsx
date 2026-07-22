import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';

export default function RBIBondsChart({ data = [] }) {
  const chartContainerRef = useRef();
  const chartRef = useRef();

  const [isLogScale, setIsLogScale] = useState(false);

  useEffect(() => {
    chartRef.current = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: { background: { color: '#1a1a1a' }, textColor: '#FFD700' },
      rightPriceScale: { mode: isLogScale ? 1 : 0, borderColor: '#FFD700' },
    });

    const lineSeries = chartRef.current.addLineSeries({
      color: '#FFD700', // Gold for Indian Bonds
      lineWidth: 2,
    });

    lineSeries.setData(data);

    return () => chartRef.current.remove();
  }, [data, isLogScale]);

  return (
    <div className="p-4 bg-black rounded-lg border border-yellow-600">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-yellow-500">RBI Government Bonds (G-Sec)</h2>
        <button onClick={() => setIsLogScale(!isLogScale)} className="px-3 py-1 bg-gray-800 text-yellow-500 rounded">
          Toggle {isLogScale ? 'Linear' : 'Log'}
        </button>
      </div>
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}
