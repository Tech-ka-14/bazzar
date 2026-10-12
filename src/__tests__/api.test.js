import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { API_BASE, apiGet, chartUrl } from '../api.js';

describe('api.js', () => {
  it('uses the local backend base by default', () => {
    expect(API_BASE).toBe('http://127.0.0.1:8787');
  });

  it('builds chart URLs on the versioned /api/v1 mount without params', () => {
    expect(chartUrl('indices', 'NIFTY 50')).toBe(`${API_BASE}/api/v1/indices/NIFTY%2050/chart.png`);
  });

  it('builds chart URLs with query params and skips empties', () => {
    expect(chartUrl('stocks', 'INFY', { exchange: 'NSE', skip: '' })).toBe(
      `${API_BASE}/api/v1/stocks/INFY/chart.png?exchange=NSE`
    );
  });
});

describe('api.js bearer token (P5)', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('sends no Authorization header outside Electron (dev fallback)', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' }),
    });
    vi.stubGlobal('fetch', fetchMock);
    await apiGet('/api/v1/health');
    const headers = fetchMock.mock.calls[0][1].headers;
    expect(headers.Authorization).toBeUndefined();
    expect(headers.Accept).toBe('application/json');
  });

  it('attaches the Electron-provided token as a Bearer header', async () => {
    vi.stubGlobal('window', { bazzar: { getApiToken: async () => 'tok123' } });
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' }),
    });
    vi.stubGlobal('fetch', fetchMock);
    // Re-import so the module-level token cache starts fresh.
    const { apiGet: authedGet } = await import('../api.js');
    await authedGet('/api/v1/health');
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer tok123');
  });

  it('fetches chart PNGs as authorized blob object URLs', async () => {
    vi.stubGlobal('window', { bazzar: { getApiToken: async () => 'tok123' } });
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['png'], { type: 'image/png' }),
    });
    vi.stubGlobal('fetch', fetchMock);
    const createObjectURL = vi.fn().mockReturnValue('blob:mock-url');
    vi.stubGlobal('URL', { ...URL, createObjectURL });
    const { fetchChartObjectUrl: fetchChart } = await import('../api.js');
    const url = await fetchChart(`${API_BASE}/api/v1/indices/NIFTY%2050/chart.png`);
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer tok123');
    expect(url).toBe('blob:mock-url');
  });

  it('throws on non-OK chart responses', async () => {
    vi.stubGlobal('window', { bazzar: { getApiToken: async () => 'tok123' } });
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 404, statusText: 'Not Found' })
    );
    const { fetchChartObjectUrl: fetchChart } = await import('../api.js');
    await expect(fetchChart(`${API_BASE}/api/v1/indices/X/chart.png`)).rejects.toThrow('404');
  });
});
