import React, { useEffect, useState } from 'react';
import { theme } from '../theme.js';
import { apiGet, chartUrl } from '../api.js';
import ChartImage from './ChartImage.jsx';

const BENCHMARK_GROUPS = [
  { key: 'rbi_gsec', fallbackTitle: 'RBI Government Bonds (G-Sec)' },
  { key: 'us_treasury_10y', fallbackTitle: 'US Treasury Yields (10Y)' },
  { key: 'sgb', fallbackTitle: 'Sovereign Gold Bonds (SGB)' },
  { key: 'repo_rates', fallbackTitle: 'Global Repo Rates: RBI vs US Fed' },
];

function formatValue(value, unit) {
  if (typeof value !== 'number') return null;
  return `${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}${unit ? ` ${unit}` : ''}`;
}

function ChangeValue({ change }) {
  if (typeof change !== 'number') return <span className="text-gray-500">—</span>;
  const up = change >= 0;
  return (
    <span className={up ? theme.profit : theme.loss}>
      {up ? '▲' : '▼'} {change > 0 ? '+' : ''}{change.toFixed(2)}
    </span>
  );
}

// Benchmarks page: fixed-income / gold / policy-rate benchmark charts rendered
// by the backend as matplotlib PNGs, plus grouped macroeconomic indicators.
export default function Benchmarks() {
  const [groups, setGroups] = useState({});
  const [benchmarksError, setBenchmarksError] = useState('');
  const [macro, setMacro] = useState([]);
  const [macroError, setMacroError] = useState('');

  useEffect(() => {
    let cancelled = false;
    apiGet('/api/benchmarks')
      .then((data) => {
        if (cancelled) return;
        const byKey = {};
        ((data && data.groups) || []).forEach((group) => {
          if (group && group.key) byKey[group.key] = group;
        });
        setGroups(byKey);
      })
      .catch((err) => {
        console.error('Failed to load benchmarks', err);
        if (!cancelled) setBenchmarksError(err.message);
      });
    apiGet('/api/macro')
      .then((data) => {
        if (!cancelled) setMacro(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error('Failed to load macro indicators', err);
        if (!cancelled) setMacroError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const macroByCategory = macro.reduce((acc, item) => {
    const category = item.category || 'Other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(item);
    return acc;
  }, {});

  return (
    <div className="space-y-8">
      {benchmarksError && (
        <p className="text-gray-500 text-sm">Benchmark feed unavailable — awaiting data sync.</p>
      )}

      {/* Benchmark chart groups */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {BENCHMARK_GROUPS.map(({ key, fallbackTitle }) => {
          const group = groups[key];
          const series = (group && group.series) || [];
          return (
            <section key={key} className={theme.card}>
              <h3 className={`text-xl mb-4 ${theme.goldText}`}>{(group && group.title) || fallbackTitle}</h3>
              <ChartImage src={chartUrl('benchmarks', key)} alt={`${(group && group.title) || fallbackTitle} chart`} />
              <div className="mt-4 space-y-2">
                {series.length === 0 && (
                  <p className="text-gray-500 text-sm">awaiting data sync</p>
                )}
                {series.map((row) => (
                  <div key={row.name} className="flex justify-between items-center bg-gray-800 p-2 rounded text-sm">
                    <span className="text-white">{row.name}</span>
                    <span className="flex items-center gap-4">
                      <span className="text-white">
                        {formatValue(row.latest, group && group.unit) || <span className="text-gray-500">—</span>}
                      </span>
                      <ChangeValue change={row.change} />
                    </span>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>

      {/* Macroeconomic indicators grouped by category */}
      <section>
        <h3 className={`text-2xl mb-4 font-bold ${theme.goldText}`}>Macroeconomic Indicators</h3>
        {macroError && <p className="text-gray-500 text-sm">Macro feed unavailable — awaiting data sync.</p>}
        {!macroError && macro.length === 0 && (
          <p className="text-gray-500 text-sm">awaiting data sync</p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {Object.entries(macroByCategory).map(([category, items]) => (
            <div key={category} className={theme.card}>
              <h4 className={`text-lg font-bold mb-3 border-b border-gray-700 pb-2 ${theme.goldText}`}>{category}</h4>
              <ul className="space-y-3">
                {items.map((item) => (
                  <li key={item.key || item.title} className="text-sm">
                    <div className="flex justify-between items-baseline gap-2">
                      <span className="text-white">{item.title}</span>
                      <span className="text-white font-semibold">
                        {formatValue(item.latest, item.unit) || <span className="text-gray-500">awaiting data sync</span>}
                      </span>
                    </div>
                    <div className="flex justify-between items-baseline gap-2 text-xs text-gray-400">
                      <span>{item.period || '—'}</span>
                      <ChangeValue change={item.change} />
                    </div>
                    {item.source && (
                      <div className="text-xs text-gray-500 mt-1">
                        {item.sourceUrl ? (
                          <a href={item.sourceUrl} target="_blank" rel="noreferrer" className="hover:text-yellow-500">
                            Source: {item.source}
                          </a>
                        ) : (
                          <>Source: {item.source}</>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
