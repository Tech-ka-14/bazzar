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
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText} (${path})`);
  }
  try {
    return await response.json();
  } catch (err) {
    throw new Error(`API returned invalid JSON (${path}): ${err.message}`);
  }
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
