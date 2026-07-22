import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';

// Sample Data Structure expected from your Python/Go backend
// { time: '2023-10-01', open: 150.5, high: 155.2, low: 148.9, close: 152.3, value: 152.3 }

const ChartDashboard = ({ data = [], comparisonData = null }) => {
  const chartContainerRef = useRef();
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const comparisonSeriesRef = useRef(null);

  const [chartType, setChartType] = useState('candlestick'); // 'candlestick' or 'line'
  const [scaleType, setScaleType] = useState('linear'); // 'linear' or 'log'
  const [upColor, setUpColor] = useState('#26a69a'); // Green
  const [downColor, setDownColor] = useState('#ef5350'); // Red

  useEffect(() => {
    // Initialize Chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { type: 'solid', color: '#131722' }, // Dark theme
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      rightPriceScale: {
        mode: scaleType === 'log' ? 2 : 0, // 2 = Logarithmic, 0 = Normal
      },
    });

    chartRef.current = chart;

    return () => chart.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!chartRef.current) return;

    // Remove existing series if any
    if (seriesRef.current) {
      chartRef.current.removeSeries(seriesRef.current);
      seriesRef.current = null;
    }

    // Add selected series type
    if (chartType === 'candlestick') {
      seriesRef.current = chartRef.current.addCandlestickSeries({
        upColor: upColor,
        downColor: downColor,
        borderVisible: false,
        wickUpColor: upColor,
        wickDownColor: downColor,
      });
      seriesRef.current.setData(data);
    } else {
      seriesRef.current = chartRef.current.addLineSeries({
        color: '#FFD700', // Gold accent for line graph
        lineWidth: 2,
      });
      // Line chart requires 'value' instead of OHLC
      const lineData = data.map((d) => ({ time: d.time, value: d.close }));
      seriesRef.current.setData(lineData);
    }

    // --- COMPARISON LOGIC ---
    // Remove the old comparison series if it exists before re-rendering
    if (comparisonSeriesRef.current) {
      chartRef.current.removeSeries(comparisonSeriesRef.current);
      comparisonSeriesRef.current = null;
    }

    // Overlay the second graph in line format if data is provided
    if (comparisonData && comparisonData.length > 0) {
      comparisonSeriesRef.current = chartRef.current.addLineSeries({
        color: '#E02424', // Red accent to contrast with the golden primary theme
        lineWidth: 2,
        lineStyle: 0, // Solid line
      });

      // Map the comparison OHLCV data to the { time, value } structure required for line graphs
      const mappedComparisonData = comparisonData.map((d) => ({
        time: d.time,
        value: d.close,
      }));

      comparisonSeriesRef.current.setData(mappedComparisonData);
    }
    // ----------------------------

    // Update Scale
    chartRef.current.priceScale('right').applyOptions({
      mode: scaleType === 'log' ? 2 : 0,
    });
  }, [chartType, scaleType, upColor, downColor, data, comparisonData]);

  return (
    <div className="p-4 bg-gray-900 rounded-lg shadow-lg border border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-yellow-500">Market Visualizer</h2>
        <div className="space-x-4">
          <select
            className="bg-gray-800 text-white p-2 rounded border border-gray-600"
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
          >
            <option value="candlestick">Candlestick</option>
            <option value="line">Line Graph</option>
          </select>

          <button
            className="bg-gray-800 text-white px-4 py-2 rounded border border-gray-600 hover:bg-gray-700"
            onClick={() => setScaleType(scaleType === 'linear' ? 'log' : 'linear')}
          >
            {scaleType === 'linear' ? 'Switch to Log Scale' : 'Switch to Linear Scale'}
          </button>
        </div>
      </div>

      {/* Chart Container */}
      <div ref={chartContainerRef} className="w-full h-[500px]" />
    </div>
  );
};

export default ChartDashboard;
