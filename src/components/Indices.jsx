import React, { useEffect, useMemo, useState } from 'react';
import { theme } from '../theme.js';
import { apiGet, chartUrl } from '../api.js';
import SearchInput from './SearchInput.jsx';
import ChartImage from './ChartImage.jsx';

const COLUMNS = [
  { key: 'symbol', label: 'Symbol', numeric: false },
  { key: 'name', label: 'Name', numeric: false },
  { key: 'open', label: 'Open', numeric: true },
  { key: 'high', label: 'High', numeric: true },
  { key: 'low', label: 'Low', numeric: true },
  { key: 'close', label: 'Close', numeric: true },
  { key: 'yearLow', label: 'Year Low', numeric: true },
  { key: 'yearHigh', label: 'Year High', numeric: true },
];

function formatNumber(value) {
  if (typeof value !== 'number') return '—';
  return value.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

// Indices page: searchable, sortable-style table of every index known to the
// data platform. Clicking a row shows the backend candlestick PNG (daily).
export default function Indices() {
  const [indices, setIndices] = useState([]);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let cancelled = false;
    apiGet('/api/indices')
      .then((data) => {
        if (!cancelled) setIndices(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error('Failed to load indices', err);
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return indices;
    return indices.filter(
      (row) =>
        (row.symbol || '').toLowerCase().includes(q) ||
        (row.name || '').toLowerCase().includes(q)
    );
  }, [indices, filter]);

  return (
    <div className={theme.card}>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <h3 className={`text-xl ${theme.goldText}`}>Indices</h3>
        <div className="flex items-center gap-4">
          <SearchInput
            className="w-72"
            placeholder="Filter indices..."
            onSelect={(item) => setFilter(item.symbol)}
          />
          {filter && (
            <button
              onClick={() => setFilter('')}
              className="text-xs text-gray-400 hover:text-yellow-500 border border-gray-700 rounded px-2 py-1"
            >
              Clear: {filter}
            </button>
          )}
          <span className="text-gray-400 text-sm">{visible.length} of {indices.length} indices</span>
        </div>
      </div>

      {selected && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h4 className={`text-lg font-bold ${theme.goldText}`}>
              {selected.name || selected.symbol} — Daily Candlestick
            </h4>
            <button
              onClick={() => setSelected(null)}
              className="text-xs text-gray-400 hover:text-yellow-500 border border-gray-700 rounded px-2 py-1"
            >
              Close chart
            </button>
          </div>
          <ChartImage
            src={chartUrl('indices', selected.symbol)}
            alt={`${selected.name || selected.symbol} daily candlestick chart`}
          />
        </div>
      )}

      {error && <p className="text-gray-500 text-sm mb-4">Index feed unavailable — awaiting data sync.</p>}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-700 text-gray-400">
              {COLUMNS.map((col) => (
                <th key={col.key} className={`py-2 px-2 ${col.numeric ? 'text-right' : ''}`}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => {
              const closeUp = typeof row.close === 'number' && typeof row.open === 'number'
                ? row.close >= row.open
                : null;
              return (
                <tr
                  key={row.symbol}
                  onClick={() => setSelected(row)}
                  className={`border-b border-gray-800 cursor-pointer hover:bg-gray-800 ${selected && selected.symbol === row.symbol ? 'bg-gray-800' : ''}`}
                >
                  <td className="py-2 px-2 font-bold text-yellow-500">{row.symbol}</td>
                  <td className="py-2 px-2">{row.name || '—'}</td>
                  <td className="py-2 px-2 text-right">{formatNumber(row.open)}</td>
                  <td className="py-2 px-2 text-right">{formatNumber(row.high)}</td>
                  <td className="py-2 px-2 text-right">{formatNumber(row.low)}</td>
                  <td className={`py-2 px-2 text-right ${closeUp === null ? '' : closeUp ? theme.profit : theme.loss}`}>
                    {formatNumber(row.close)}
                  </td>
                  <td className="py-2 px-2 text-right">{formatNumber(row.yearLow)}</td>
                  <td className="py-2 px-2 text-right">{formatNumber(row.yearHigh)}</td>
                </tr>
              );
            })}
            {visible.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length} className="py-6 text-center text-gray-500">
                  {error ? 'awaiting data sync' : 'No indices match the current filter.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
