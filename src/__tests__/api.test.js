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

describe('api.js analytics wrappers (P7-D)', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllGlobals();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  function mockJsonResponse(body, { ok = true, status = 200, statusText = 'OK' } = {}) {
    return vi.fn().mockResolvedValue({
      ok,
      status,
      statusText,
      json: async () => body,
    });
  }

  it('getVar hits the analytics endpoint with method and confidence params', async () => {
    const fetchMock = mockJsonResponse({ symbol: 'INFY' });
    vi.stubGlobal('fetch', fetchMock);
    const { getVar } = await import('../api.js');
    await getVar('INFY', 'parametric', 0.95);
    expect(fetchMock.mock.calls[0][0]).toBe(
      `${API_BASE}/api/v1/analytics/var?symbol=INFY&method=parametric&confidence=0.95`
    );
  });

  it('getVolatility defaults to the ewma model', async () => {
    const fetchMock = mockJsonResponse({ symbol: 'INFY' });
    vi.stubGlobal('fetch', fetchMock);
    const { getVolatility } = await import('../api.js');
    await getVolatility('INFY');
    expect(fetchMock.mock.calls[0][0]).toBe(
      `${API_BASE}/api/v1/analytics/volatility?symbol=INFY&model=ewma`
    );
  });

  it('getVarBacktest passes the confidence level', async () => {
    const fetchMock = mockJsonResponse({ symbol: 'INFY' });
    vi.stubGlobal('fetch', fetchMock);
    const { getVarBacktest } = await import('../api.js');
    await getVarBacktest('INFY', 0.99);
    expect(fetchMock.mock.calls[0][0]).toBe(
      `${API_BASE}/api/v1/analytics/backtest/var?symbol=INFY&confidence=0.99`
    );
  });

  it('getPortfolioRisk POSTs JSON weights with auth headers', async () => {
    vi.stubGlobal('window', { bazzar: { getApiToken: async () => 'tok123' } });
    const fetchMock = mockJsonResponse({ var_pct: 0.02 });
    vi.stubGlobal('fetch', fetchMock);
    const { getPortfolioRisk } = await import('../api.js');
    await getPortfolioRisk({ INFY: 0.6, TCS: 0.4 }, 0.95);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe(`${API_BASE}/api/v1/analytics/portfolio/risk`);
    expect(options.method).toBe('POST');
    expect(options.headers['Content-Type']).toBe('application/json');
    expect(options.headers.Authorization).toBe('Bearer tok123');
    expect(JSON.parse(options.body)).toEqual({
      weights: { INFY: 0.6, TCS: 0.4 },
      confidence: 0.95,
    });
  });

  it('non-2xx responses throw ApiError carrying status and the error envelope', async () => {
    const envelope = {
      error: {
        code: 'insufficient_data',
        message:
          'insufficient data for VaR: 42 return observations available, at least 250 required',
      },
    };
    const fetchMock = mockJsonResponse(envelope, {
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
    });
    vi.stubGlobal('fetch', fetchMock);
    const { ApiError, getVar } = await import('../api.js');
    const err = await getVar('INFY').catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(422);
    expect(err.code).toBe('insufficient_data');
    expect(err.detail).toContain('42 return observations');
  });

  it('404 responses surface as ApiError with status 404', async () => {
    const envelope = { error: { code: 'not_found', message: 'unknown symbol: FOO' } };
    const fetchMock = mockJsonResponse(envelope, {
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });
    vi.stubGlobal('fetch', fetchMock);
    const { ApiError, getVolatility } = await import('../api.js');
    const err = await getVolatility('FOO').catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(404);
  });
});
