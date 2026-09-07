import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';

export default function USDINRChart({ data }) {
    const chartContainerRef = useRef();
    const chartRef = useRef();
    const seriesRef = useRef();
    
    const [chartType, setChartType] = useState('candlestick');
    const [isLogScale, setIsLogScale] = useState(false);

    useEffect(() => {
        const handleResize = () => {
            chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        };

        chartRef.current = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 400,
            layout: {
                background: { color: '#1a1a1a' },
                textColor: '#FFD700', // Golden theme
            },
            grid: {
                vertLines: { color: '#333' },
                horzLines: { color: '#333' },
            },
            rightPriceScale: {
                mode: isLogScale ? 1 : 0, // 1 for Log, 0 for Normal
                borderColor: '#FFD700',
            },
            timeScale: {
                borderColor: '#FFD700',
            },
        });

        if (chartType === 'candlestick') {
            seriesRef.current = chartRef.current.addCandlestickSeries({
                upColor: '#00ff00',
                downColor: '#ff0000',
                borderVisible: false,
                wickUpColor: '#00ff00',
                wickDownColor: '#ff0000',
            });
        } else {
            seriesRef.current = chartRef.current.addLineSeries({
                color: '#FFD700',
                lineWidth: 2,
            });
        }

        seriesRef.current.setData(data);
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chartRef.current.remove();
        };
    }, [data, chartType, isLogScale]);

    return (
        <div className="p-4 bg-black rounded-lg border border-yellow-600">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-yellow-500">USD/INR Currency Pair</h2>
                <div className="space-x-2">
                    <button onClick={() => setChartType(chartType === 'line' ? 'candlestick' : 'line')} className="px-3 py-1 bg-gray-800 text-yellow-500 rounded hover:bg-gray-700 transition">
                        Toggle {chartType === 'line' ? 'Candles' : 'Line'}
                    </button>
                    <button onClick={() => setIsLogScale(!isLogScale)} className="px-3 py-1 bg-gray-800 text-yellow-500 rounded hover:bg-gray-700 transition">
                        Toggle {isLogScale ? 'Linear' : 'Log'}
                    </button>
                </div>
            </div>
            <div ref={chartContainerRef} className="w-full" />
        </div>
    );
}