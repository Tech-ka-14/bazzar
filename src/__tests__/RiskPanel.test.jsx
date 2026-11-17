// @vitest-environment jsdom
import React, { act } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createRoot } from 'react-dom/client';
import RiskPanel from '../components/RiskPanel.jsx';

// jsdom render tests for the Equity deep-dive risk panel (P7-D). Fetch is
// mocked per analytics endpoint; assertions cover the data state (payload
// numbers + asOf stamp, never placeholders) and the explicit empty states
// (422 insufficient_data, 404 not synced).

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

const VAR_PAYLOAD = {
  symbol: 'INFY',
  method: 'historical',
  confidence: 0.99,
  var_pct: 0.0234,
  var_value: null,
  es_pct: 0.0311,
  n_obs: 300,
  asOf: '2026-10-10',
  source: 'daily_ohlcv',
  cached: false,
};

const VOL_PAYLOAD = {
  symbol: 'INFY',
  model: 'ewma',
  current_vol: 0.0123,
  annualized_vol: 0.1953,
  params: { lambda: 0.94 },
  n_obs: 300,
  asOf: '2026-10-10',
  source: 'daily_ohlcv',
  cached: false,
};

const BACKTEST_PAYLOAD = {
  symbol: 'INFY',
  method: 'historical',
  confidence: 0.99,
  window: 250,
  n_obs: 330,
  exceptions: 3,
  exception_rate: 0.0375,
  expected_exceptions: 0.8,
  kupiec: { lr: 4.21, p_value: 0.04, decision: 'reject' },
  christoffersen: { lr: 4.3, p_value: 0.038, decision: 'reject' },
  basel_zone: 'green',
  asOf: '2026-10-10',
  source: 'daily_ohlcv',
  cached: false,
};

const INSUFFICIENT_ENVELOPE = {
  error: {
    code: 'insufficient_data',
    message: 'insufficient data for VaR: 42 return observations available, at least 250 required',
  },
};

function jsonResponse(body, { ok = true, status = 200, statusText = 'OK' } = {}) {
  return { ok, status, statusText, json: async () => body };
}

function mockFetch(handler) {
  const fetchMock = vi.fn(async (url) => handler(String(url)));
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function render(ui) {
  const container = document.createElement('div');
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => {
    root.render(ui);
  });
  return container;
}

async function flush() {
  await act(async () => {});
}

describe('RiskPanel (P7-D)', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllGlobals();
    document.body.innerHTML = '';
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    document.body.innerHTML = '';
  });

  it('renders the data state with payload numbers and asOf stamps', async () => {
    mockFetch((url) => {
      if (url.includes('/analytics/var?')) return jsonResponse(VAR_PAYLOAD);
      if (url.includes('/analytics/volatility')) return jsonResponse(VOL_PAYLOAD);
      if (url.includes('/analytics/backtest/var')) return jsonResponse(BACKTEST_PAYLOAD);
      throw new Error(`unexpected fetch: ${url}`);
    });
    const container = render(<RiskPanel symbol="INFY" />);
    await flush();

    const text = container.textContent;
    // VaR/ES block (fractions rendered as percentages).
    expect(text).toContain('2.34%');
    expect(text).toContain('3.11%');
    // Volatility block (current + annualized).
    expect(text).toContain('1.23%');
    expect(text).toContain('19.53%');
    // Backtest block: exceptions vs expected, Kupiec decision, Basel badge.
    expect(text).toContain('3 / 0.8');
    expect(text).toContain('reject');
    expect(text).toContain('Basel green');
    // Every block stamps asOf + n_obs straight from its payload.
    expect(text.match(/as of 2026-10-10/g)).toHaveLength(3);
    // No placeholder dashes where payload numbers exist.
    expect(text).not.toContain('—');
  });

  it('renders the insufficient-history empty state on 422', async () => {
    mockFetch(() =>
      jsonResponse(INSUFFICIENT_ENVELOPE, {
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
      })
    );
    const container = render(<RiskPanel symbol="INFY" />);
    await flush();

    const text = container.textContent;
    expect(text.match(/Not enough history \(42 obs, need 250\)\./g)).toHaveLength(3);
    // No fabricated metric values leak into the empty state.
    expect(text).not.toContain('2.34%');
    expect(text).not.toContain('1.23%');
  });

  it('renders the not-synced empty state on 404', async () => {
    mockFetch(() =>
      jsonResponse(
        { error: { code: 'not_found', message: 'unknown symbol: FOO' } },
        {
          ok: false,
          status: 404,
          statusText: 'Not Found',
        }
      )
    );
    const container = render(<RiskPanel symbol="FOO" />);
    await flush();

    expect(container.textContent.match(/Symbol not synced\./g)).toHaveLength(3);
  });
});
