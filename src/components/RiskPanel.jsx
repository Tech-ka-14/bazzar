import React, { useEffect, useState } from 'react';
import { theme } from '../theme.js';
import { getVar, getVarBacktest, getVolatility } from '../api.js';
import {
  classifyAnalyticsError,
  formatPct,
  formatRatio,
  parseInsufficientDetail,
} from '../riskUtils.js';

// Risk analytics panel for a single symbol (P7-D, roadmap 7.4). Shown in the
// Equity deep-dive once a symbol is selected. Fetches the three single-symbol
// analytics endpoints (VaR/ES, volatility, VaR backtest) independently so one
// failure mode (e.g. 422 insufficient history on the backtest) never hides
// the others. SPEC hard rule: no fabricated numbers — every block renders
// loading → data (with asOf + n_obs) → an explicit empty state.

const VAR_METHODS = ['historical', 'parametric', 'montecarlo'];
const VOL_MODELS = ['ewma', 'garch'];
const CONFIDENCES = [0.95, 0.99];

// Basel traffic-light badge colours (green/amber/red), theme-consistent.
const ZONE_CLASSES = {
  green: 'bg-green-700 text-white',
  amber: 'bg-yellow-500 text-black',
  red: 'bg-red-600 text-white',
};

const selectClass = 'bg-gray-800 border border-gray-600 text-white p-1 rounded text-sm';

export default function RiskPanel({ symbol }) {
  const [method, setMethod] = useState('historical');
  const [confidence, setConfidence] = useState(0.99);
  const [model, setModel] = useState('ewma');
  const [varState, setVarState] = useState({ status: 'idle' });
  const [volState, setVolState] = useState({ status: 'idle' });
  const [backtestState, setBacktestState] = useState({ status: 'idle' });

  useEffect(() => {
    if (!symbol) return undefined;
    let cancelled = false;
    setVarState({ status: 'loading' });
    getVar(symbol, method, confidence)
      .then((data) => {
        if (!cancelled) setVarState({ status: 'ok', data });
      })
      .catch((err) => {
        if (!cancelled) setVarState({ status: 'failed', ...classifyAnalyticsError(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, method, confidence]);

  useEffect(() => {
    if (!symbol) return undefined;
    let cancelled = false;
    setVolState({ status: 'loading' });
    getVolatility(symbol, model)
      .then((data) => {
        if (!cancelled) setVolState({ status: 'ok', data });
      })
      .catch((err) => {
        if (!cancelled) setVolState({ status: 'failed', ...classifyAnalyticsError(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, model]);

  useEffect(() => {
    if (!symbol) return undefined;
    let cancelled = false;
    setBacktestState({ status: 'loading' });
    getVarBacktest(symbol, confidence)
      .then((data) => {
        if (!cancelled) setBacktestState({ status: 'ok', data });
      })
      .catch((err) => {
        if (!cancelled) setBacktestState({ status: 'failed', ...classifyAnalyticsError(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, confidence]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* VaR / ES block */}
      <div className="bg-gray-800 rounded p-4">
        <div className="flex items-center justify-between mb-3">
          <h5 className={`font-bold ${theme.goldText}`}>VaR / ES</h5>
          <div className="flex gap-2">
            <select
              aria-label="VaR method"
              className={selectClass}
              value={method}
              onChange={(e) => setMethod(e.target.value)}
            >
              {VAR_METHODS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <select
              aria-label="VaR confidence"
              className={selectClass}
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
            >
              {CONFIDENCES.map((c) => (
                <option key={c} value={c}>
                  {(c * 100).toFixed(0)}%
                </option>
              ))}
            </select>
          </div>
        </div>
        <BlockBody state={varState}>
          {(data) => (
            <dl className="space-y-1 text-sm">
              <Metric label={`VaR (${method}, ${(data.confidence * 100).toFixed(0)}%)`}>
                <span className={theme.loss}>{formatPct(data.var_pct)}</span>
              </Metric>
              <Metric label="Expected Shortfall">
                <span className={theme.loss}>{formatPct(data.es_pct)}</span>
              </Metric>
            </dl>
          )}
        </BlockBody>
      </div>

      {/* Volatility block */}
      <div className="bg-gray-800 rounded p-4">
        <div className="flex items-center justify-between mb-3">
          <h5 className={`font-bold ${theme.goldText}`}>Volatility</h5>
          <select
            aria-label="Volatility model"
            className={selectClass}
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            {VOL_MODELS.map((m) => (
              <option key={m} value={m}>
                {m.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
        <BlockBody state={volState}>
          {(data) => (
            <dl className="space-y-1 text-sm">
              <Metric label={`Current (${data.model.toUpperCase()}, daily)`}>
                <span className="text-white">{formatPct(data.current_vol)}</span>
              </Metric>
              <Metric label="Annualized (252d)">
                <span className="text-white">{formatPct(data.annualized_vol)}</span>
              </Metric>
            </dl>
          )}
        </BlockBody>
      </div>

      {/* VaR backtest block */}
      <div className="bg-gray-800 rounded p-4">
        <div className="flex items-center justify-between mb-3">
          <h5 className={`font-bold ${theme.goldText}`}>VaR Backtest</h5>
          {backtestState.status === 'ok' && <BaselBadge zone={backtestState.data.basel_zone} />}
        </div>
        <BlockBody state={backtestState}>
          {(data) => (
            <dl className="space-y-1 text-sm">
              <Metric label="Exceptions vs expected">
                <span className="text-white">
                  {data.exceptions} / {formatRatio(data.expected_exceptions, 1)}
                </span>
              </Metric>
              <Metric label="Exception rate">
                <span className="text-white">{formatPct(data.exception_rate)}</span>
              </Metric>
              <Metric label="Kupiec test (5%)">
                <span className="text-white">
                  {data.kupiec.decision} (p={formatRatio(data.kupiec.p_value, 3)})
                </span>
              </Metric>
            </dl>
          )}
        </BlockBody>
      </div>
    </div>
  );
}

// Label/value row inside a metric block.
function Metric({ label, children }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="text-gray-400">{label}</dt>
      <dd className="text-right">{children}</dd>
    </div>
  );
}

// Basel zone badge (green/amber/red traffic light).
function BaselBadge({ zone }) {
  const cls = ZONE_CLASSES[zone] || 'bg-gray-700 text-white';
  return (
    <span className={`text-xs font-bold uppercase px-2 py-1 rounded ${cls}`}>
      Basel {zone || '—'}
    </span>
  );
}

// Shared per-block state machine: loading → data → explicit empty states.
// `children` is a render function invoked with the payload only in the data
// state; the asOf/n_obs stamp comes straight from that payload.
function BlockBody({ state, children }) {
  if (state.status === 'loading' || state.status === 'idle') {
    return <p className="text-gray-500 text-sm animate-pulse">Loading risk analytics...</p>;
  }
  if (state.status === 'failed') {
    return <BlockError state={state} />;
  }
  return (
    <>
      {children(state.data)}
      <p className="text-xs text-gray-500 mt-3">
        as of {state.data.asOf} · {state.data.n_obs} obs
        {state.data.cached ? ' · cached' : ''}
      </p>
    </>
  );
}

// Explicit empty states — no placeholder numbers anywhere.
function BlockError({ state }) {
  if (state.state === 'insufficient') {
    const { nObs, minimum } = parseInsufficientDetail(state.detail);
    return (
      <p className="text-gray-500 text-sm">
        {nObs !== null && minimum !== null
          ? `Not enough history (${nObs} obs, need ${minimum}).`
          : 'Not enough history yet.'}
      </p>
    );
  }
  if (state.state === 'not_found') {
    return <p className="text-gray-500 text-sm">Symbol not synced.</p>;
  }
  return <p className="text-gray-500 text-sm">Risk analytics unavailable — {state.detail}</p>;
}
