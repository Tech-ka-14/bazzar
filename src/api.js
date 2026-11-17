// Central access point for the Bazzar local HTTP API served by the Python
// backend (see SPEC.md "Local HTTP API contract"). All renderer data comes
// from this API; there is no mock data anywhere in the renderer.
//
// P5 (roadmap 5.1/5.3):
//  * all calls go to the versioned /api/v1 mount (the flat /api alias is a
//    one-release backward-compat shim on the server side);
//  * every request carries `Authorization: Bearer <token>` with the
//    per-launch token exposed by the Electron main process via
//    window.bazzar.getApiToken() (P5 handshake). Outside Electron (plain
//    browser dev) there is no token and the server runs its documented
//    open dev fallback, so calls still work.
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8787';

// Cached per-launch bearer token. `null` = not fetched yet, `''` = running
// outside Electron (dev fallback, no token required).
let apiToken = null;

export async function getApiToken() {
  if (apiToken !== null) return apiToken;
  // `window` may not exist (node test env); the Electron preload is the only
  // source of the per-launch token.
  const win = typeof window === 'undefined' ? undefined : window;
  if (win && win.bazzar && typeof win.bazzar.getApiToken === 'function') {
    try {
      apiToken = (await win.bazzar.getApiToken()) || '';
    } catch {
      apiToken = ''; // IPC failed — fall back to token-less dev mode
    }
  } else {
    apiToken = import.meta.env.VITE_API_TOKEN || '';
  }
  return apiToken;
}

async function authHeaders(extra = {}) {
  const token = await getApiToken();
  const headers = { ...extra };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

// Error thrown by apiGet/apiPost on non-2xx responses. Carries the HTTP
// status and, when the body is the standard {"error": {code, message}}
// envelope, the parsed payload — so callers can render explicit states
// (400 bad request, 404 not synced, 422 insufficient_data) instead of ever
// fabricating numbers.
export class ApiError extends Error {
  constructor(status, statusText, path, payload = null) {
    super(`API request failed: ${status} ${statusText} (${path})`);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }

  // The envelope's machine-readable code (e.g. 'insufficient_data'), or null.
  get code() {
    return this.payload && this.payload.error ? this.payload.error.code : null;
  }

  // The envelope's human-readable message, or null when absent.
  get detail() {
    return this.payload && this.payload.error ? this.payload.error.message : null;
  }
}

// Builds an ApiError from a non-OK response, parsing the error envelope when
// the body is JSON (non-JSON bodies yield a payload-less ApiError).
async function toApiError(response, path) {
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null; // non-JSON error body
  }
  return new ApiError(response.status, response.statusText, path, payload);
}

// Shared response handling for apiGet/apiPost: throws ApiError on non-2xx,
// parses the JSON body otherwise.
async function parseJsonResponse(response, path) {
  if (!response.ok) throw await toApiError(response, path);
  try {
    return await response.json();
  } catch (err) {
    throw new Error(`API returned invalid JSON (${path}): ${err.message}`);
  }
}

// Small JSON GET helper with error handling. Throws on non-2xx or invalid JSON.
export async function apiGet(path) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: await authHeaders({ Accept: 'application/json' }),
    });
  } catch (err) {
    throw new Error(`API unreachable at ${API_BASE}${path}: ${err.message}`);
  }
  return parseJsonResponse(response, path);
}

// Small JSON POST helper (same auth + error handling as apiGet). Throws on
// non-2xx or invalid JSON.
export async function apiPost(path, body = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: await authHeaders({
        Accept: 'application/json',
        'Content-Type': 'application/json',
      }),
      body: JSON.stringify(body),
    });
  } catch (err) {
    throw new Error(`API unreachable at ${API_BASE}${path}: ${err.message}`);
  }
  return parseJsonResponse(response, path);
}

// Builds a URL for a backend matplotlib PNG chart endpoint (api/v1 mount).
//   kind: 'indices' | 'stocks' | 'benchmarks'
//   key:  symbol or benchmark group key
//   params: optional query params (e.g. { exchange: 'NSE' })
export function chartUrl(kind, key, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([name, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(name, value);
  });
  const qs = query.toString();
  return `${API_BASE}/api/v1/${kind}/${encodeURIComponent(key)}/chart.png${qs ? `?${qs}` : ''}`;
}

// <img> tags cannot send Authorization headers, so chart PNGs are fetched as
// authenticated blobs and handed to the renderer as object URLs (P5). The
// caller owns the returned URL and should URL.revokeObjectURL() it when done.
export async function fetchChartObjectUrl(url) {
  let response;
  try {
    response = await fetch(url, { headers: await authHeaders({ Accept: 'image/png' }) });
  } catch (err) {
    throw new Error(`chart fetch failed: ${err.message}`);
  }
  if (!response.ok) {
    throw new Error(`chart request failed: ${response.status} ${response.statusText}`);
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

// --- P7-D analytics wrappers (roadmap 7.4) ----------------------------------
// Thin wrappers over the /api/v1/analytics/* endpoints (SPEC "Local HTTP API
// contract"). Payloads are returned unchanged — every number keeps its
// `asOf`, `source` and `cached` fields — and failure modes surface as
// ApiError (400 unknown method/model, 404 symbol not synced, 422
// insufficient_data) so the UI renders explicit states, never placeholders.

// GET /api/v1/analytics/var?symbol&method=historical|parametric|montecarlo&confidence
export function getVar(symbol, method = 'historical', confidence = 0.99) {
  const query = new URLSearchParams({
    symbol,
    method,
    confidence: String(confidence),
  });
  return apiGet(`/api/v1/analytics/var?${query.toString()}`);
}

// GET /api/v1/analytics/volatility?symbol&model=ewma|garch
export function getVolatility(symbol, model = 'ewma') {
  const query = new URLSearchParams({ symbol, model });
  return apiGet(`/api/v1/analytics/volatility?${query.toString()}`);
}

// POST /api/v1/analytics/portfolio/risk — weights: {SYMBOL: fraction, ...}
// (must sum to 1 server-side), confidence: 0.95 | 0.99.
export function getPortfolioRisk(weights, confidence = 0.99) {
  return apiPost('/api/v1/analytics/portfolio/risk', { weights, confidence });
}

// GET /api/v1/analytics/backtest/var?symbol&confidence
export function getVarBacktest(symbol, confidence = 0.99) {
  const query = new URLSearchParams({ symbol, confidence: String(confidence) });
  return apiGet(`/api/v1/analytics/backtest/var?${query.toString()}`);
}
