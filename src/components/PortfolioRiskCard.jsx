import React, { useState } from 'react';
import { theme } from '../theme.js';
import { getPortfolioRisk } from '../api.js';
import {
  classifyAnalyticsError,
  formatPct,
  formatRatio,
  parseInsufficientDetail,
} from '../riskUtils.js';

// Portfolio risk card (P7-D, roadmap 7.4) for the Home page. The user enters
// a few symbols with percentage weights, POSTs to
// /api/v1/analytics/portfolio/risk, and gets portfolio VaR/ES, annualized
// Sharpe/Sortino and the per-symbol Euler component-VaR split as simple
// theme-consistent bars. SPEC hard rule: no fabricated numbers — empty,
// insufficient-data and not-synced states are explicit, and every rendered
// number comes from the response payload (shown with its asOf stamp).

const CONFIDENCES = [0.95, 0.99];
const MAX_ROWS = 8;
const MIN_ROWS = 2;

const inputClass = 'bg-gray-800 p-2 rounded border border-gray-700 text-white text-sm w-full';

export default function PortfolioRiskCard({ className = '' }) {
  const [rows, setRows] = useState(() => emptyRows());
  const [confidence, setConfidence] = useState(0.99);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | loading | ok | failed
  const [failure, setFailure] = useState(null);

  // Live weight sum (percent) so the user sees the sum-to-100 constraint
  // (the API requires fractions summing to 1) before submitting.
  const weightSum = rows.reduce((acc, row) => {
    const w = Number(row.weight);
    return acc + (Number.isFinite(w) && row.weight !== '' ? w : 0);
  }, 0);

  const updateRow = (index, field, value) => {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  };

  const addRow = () => setRows((prev) => (prev.length < MAX_ROWS ? [...prev, emptyRow()] : prev));
  const removeRow = (index) =>
    setRows((prev) => (prev.length > MIN_ROWS ? prev.filter((_, i) => i !== index) : prev));

  const handleCompute = () => {
    const weights = {};
    for (const row of rows) {
      const symbol = row.symbol.trim().toUpperCase();
      const weight = Number(row.weight) / 100; // percent input → fraction
      if (!symbol || row.weight === '' || !Number.isFinite(weight)) continue;
      weights[symbol] = (weights[symbol] || 0) + weight;
    }
    setStatus('loading');
    setFailure(null);
    getPortfolioRisk(weights, confidence)
      .then((data) => {
        setResult(data);
        setStatus('ok');
      })
      .catch((err) => {
        setResult(null);
        setFailure(classifyAnalyticsError(err));
        setStatus('failed');
      });
  };

  return (
    <section className={`${theme.card} ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-xl ${theme.goldText}`}>Portfolio Risk</h3>
        <select
          aria-label="Portfolio confidence"
          className="bg-gray-800 border border-gray-600 text-white p-1 rounded text-sm"
          value={confidence}
          onChange={(e) => setConfidence(Number(e.target.value))}
        >
          {CONFIDENCES.map((c) => (
            <option key={c} value={c}>
              {(c * 100).toFixed(0)}% confidence
            </option>
          ))}
        </select>
      </div>

      {/* Weight entry rows (percent weights, must sum to 100) */}
      <div className="space-y-2 mb-3">
        {rows.map((row, index) => (
          <div key={index} className="flex gap-2 items-center">
            <input
              aria-label={`Symbol ${index + 1}`}
              className={`${inputClass} w-2/5 uppercase`}
              placeholder="Symbol (e.g. INFY)"
              value={row.symbol}
              onChange={(e) => updateRow(index, 'symbol', e.target.value)}
            />
            <input
              aria-label={`Weight ${index + 1}`}
              className={`${inputClass} w-1/4`}
              placeholder="Weight %"
              type="number"
              min="0"
              max="100"
              value={row.weight}
              onChange={(e) => updateRow(index, 'weight', e.target.value)}
            />
            <button
              className="text-xs text-gray-400 hover:text-red-500 border border-gray-700 rounded px-2 py-1"
              onClick={() => removeRow(index)}
              disabled={rows.length <= MIN_ROWS}
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-4 mb-4">
        <button
          className="text-xs text-gray-400 hover:text-yellow-500 border border-gray-700 rounded px-2 py-1"
          onClick={addRow}
          disabled={rows.length >= MAX_ROWS}
        >
          + Add symbol
        </button>
        <span
          className={`text-sm ${Math.abs(weightSum - 100) < 0.01 ? 'text-gray-400' : 'text-red-500'}`}
        >
          Weights sum: {weightSum.toFixed(1)}% (must equal 100%)
        </span>
        <button
          className={`ml-auto px-4 py-2 rounded font-bold ${theme.goldBg}`}
          onClick={handleCompute}
        >
          Compute
        </button>
      </div>

      {/* Result states: idle prompt → loading → data → explicit errors */}
      {status === 'idle' && (
        <p className="text-gray-500 text-sm">
          Enter symbols and weights above, then Compute to run portfolio risk analytics.
        </p>
      )}
      {status === 'loading' && (
        <p className="text-gray-500 text-sm animate-pulse">Computing portfolio risk...</p>
      )}
      {status === 'failed' && <FailureMessage failure={failure} />}
      {status === 'ok' && result && <PortfolioRiskResult data={result} />}
    </section>
  );
}

function emptyRow() {
  return { symbol: '', weight: '' };
}

function emptyRows() {
  return Array.from({ length: MIN_ROWS }, emptyRow);
}

// Data state: headline metrics + per-symbol component-VaR bars. Null fields
// (e.g. Sharpe when the portfolio vol is zero) render '—' per the SPEC.
function PortfolioRiskResult({ data }) {
  const components = Object.entries(data.component_var || {});
  const maxComponent = Math.max(...components.map(([, value]) => Math.abs(value)), 0);
  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4 text-sm">
        <Headline
          label={`VaR (${(data.confidence * 100).toFixed(0)}%)`}
          value={formatPct(data.var_pct)}
          accent
        />
        <Headline label="Expected Shortfall" value={formatPct(data.es_pct)} accent />
        <Headline
          label="Portfolio volatility (daily)"
          value={formatPct(data.portfolio_volatility)}
        />
        <Headline label="Undiversified VaR" value={formatPct(data.undiversified_var)} />
        <Headline label="Sharpe (ann.)" value={formatRatio(data.sharpe)} />
        <Headline label="Sortino (ann.)" value={formatRatio(data.sortino)} />
      </div>

      <h4 className="text-sm font-bold text-gray-300 mb-2">Component VaR (Euler split)</h4>
      <div className="space-y-1 mb-4">
        {components.map(([symbol, value]) => (
          <div key={symbol} className="flex items-center gap-2 text-sm">
            <span className="w-20 font-bold text-yellow-500">{symbol}</span>
            <div className="flex-1 bg-gray-800 rounded h-4 overflow-hidden">
              <div
                className="h-full bg-yellow-500"
                style={{
                  width: maxComponent > 0 ? `${(Math.abs(value) / maxComponent) * 100}%` : 0,
                }}
              />
            </div>
            <span className="w-16 text-right text-gray-300">{formatPct(value)}</span>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-500">
        as of {data.asOf} · {data.n_obs} obs{data.cached ? ' · cached' : ''}
      </p>
    </div>
  );
}

function Headline({ label, value, accent = false }) {
  return (
    <div className="bg-gray-800 rounded p-3">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-lg font-bold ${accent ? theme.loss : 'text-white'}`}>{value}</p>
    </div>
  );
}

// Explicit empty/error states — no placeholder numbers.
function FailureMessage({ failure }) {
  if (failure && failure.state === 'insufficient') {
    const { nObs, minimum } = parseInsufficientDetail(failure.detail);
    return (
      <p className="text-gray-500 text-sm">
        {nObs !== null && minimum !== null
          ? `Not enough history (${nObs} obs, need ${minimum}).`
          : 'Not enough history yet.'}
      </p>
    );
  }
  if (failure && failure.state === 'not_found') {
    return <p className="text-gray-500 text-sm">Symbol not synced.</p>;
  }
  return (
    <p className="text-gray-500 text-sm">
      Portfolio risk unavailable{failure && failure.detail ? ` — ${failure.detail}` : ''}.
    </p>
  );
}
