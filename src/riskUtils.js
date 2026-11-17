// Shared helpers for the risk-analytics UI (P7-D, roadmap 7.4): error
// classification onto explicit UI states and display formatting. The SPEC
// hard rule applies: never fabricate numbers — unsynced or
// insufficient-history symbols render explicit empty states, and every
// rendered number comes from the API payload (with its `asOf`).
import { ApiError } from './api.js';

// Maps a fetch error onto an explicit UI state:
//   'insufficient' → 422 insufficient_data (history floor not met)
//   'not_found'    → 404 (symbol not synced into the local store)
//   'error'        → anything else (network, 400, 5xx)
export function classifyAnalyticsError(err) {
  if (err instanceof ApiError) {
    if (err.status === 422 && err.code === 'insufficient_data') {
      return { state: 'insufficient', detail: err.detail || '' };
    }
    if (err.status === 404) {
      return { state: 'not_found', detail: err.detail || '' };
    }
  }
  return { state: 'error', detail: err && err.message ? err.message : String(err) };
}

// Extracts {nObs, minimum} from the backend insufficient_data message
// ("insufficient data for VaR: 42 return observations available, at least
// 250 required"). Returns nulls when the message does not match — the UI
// then falls back to a generic "not enough history" line (still no
// fabricated numbers).
export function parseInsufficientDetail(detail) {
  const match = /(\d+)\s+return observations? available, at least (\d+) required/i.exec(
    detail || ''
  );
  if (!match) return { nObs: null, minimum: null };
  return { nObs: Number(match[1]), minimum: Number(match[2]) };
}

// Formats a fraction (e.g. 0.0234) as a percentage string; null/non-finite
// renders '—' (never a fabricated number).
export function formatPct(value, digits = 2) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  return `${(value * 100).toFixed(digits)}%`;
}

// Formats a plain ratio (Sharpe/Sortino, test statistics); '—' when absent.
export function formatRatio(value, digits = 2) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  return value.toFixed(digits);
}
