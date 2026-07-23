// Central access point for the Bazzar local HTTP API served by the Python
// backend (see SPEC.md "Local HTTP API contract"). All renderer data comes
// from this API; there is no mock data anywhere in the renderer.
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8787';

// Small JSON GET helper with error handling. Throws on non-2xx or invalid JSON.
export async function apiGet(path) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { headers: { Accept: 'application/json' } });
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

// Builds a URL for a backend matplotlib PNG chart endpoint.
//   kind: 'indices' | 'stocks' | 'benchmarks'
//   key:  symbol or benchmark group key
//   params: optional query params (e.g. { exchange: 'NSE' })
export function chartUrl(kind, key, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([name, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(name, value);
  });
  const qs = query.toString();
  return `${API_BASE}/api/${kind}/${encodeURIComponent(key)}/chart.png${qs ? `?${qs}` : ''}`;
}
