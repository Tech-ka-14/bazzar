import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';

export default function USTreasuryBondsChart({ data }) {
    const chartContainerRef = useRef();
    const chartRef = useRef();
    const seriesRef = useRef();
    
    const [isLogScale, setIsLogScale] = useState(false);

    useEffect(() => {
        chartRef.current = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 400,
            layout: { background: { color: '#1a1a1a' }, textColor: '#FFD700' },
            grid: { vertLines: { color: '#333' }, horzLines: { color: '#333' } },
            rightPriceScale: { mode: isLogScale ? 1 : 0, borderColor: '#FFD700' },
            timeScale: { borderColor: '#FFD700' },
        });

        seriesRef.current = chartRef.current.addLineSeries({
            color: '#FFFFFF', // White accent for US Treasuries
            lineWidth: 2,
        });

        seriesRef.current.setData(data);

        return () => chartRef.current.remove();
    }, [data, isLogScale]);

    return (
        <div className="p-4 bg-black rounded-lg border border-yellow-600">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-yellow-500">US Treasury Yields (10Y)</h2>
                <button onClick={() => setIsLogScale(!isLogScale)} className="px-3 py-1 bg-gray-800 text-yellow-500 rounded">
                    Toggle {isLogScale ? 'Linear' : 'Log'}
                </button>
            </div>
            <div ref={chartContainerRef} className="w-full" />
        </div>
    );
}