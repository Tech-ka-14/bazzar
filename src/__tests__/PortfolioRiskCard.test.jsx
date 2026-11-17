// @vitest-environment jsdom
import React, { act } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createRoot } from 'react-dom/client';
import PortfolioRiskCard from '../components/PortfolioRiskCard.jsx';

// jsdom render tests for the Home portfolio risk card (P7-D): empty state
// before any compute, and the data state after a mocked portfolio/risk
// response (metrics + component-VaR bars + asOf stamp, never placeholders).

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

const PORTFOLIO_PAYLOAD = {
  symbols: ['INFY', 'TCS'],
  weights: { INFY: 0.6, TCS: 0.4 },
  confidence: 0.99,
  var_pct: 0.0187,
  es_pct: 0.0245,
  portfolio_volatility: 0.0112,
  undiversified_var: 0.0201,
  component_var: { INFY: 0.011, TCS: 0.0077 },
  sharpe: 1.24,
  sortino: 1.61,
  n_obs: 300,
  asOf: '2026-10-10',
  source: 'daily_ohlcv',
  cached: false,
};

function jsonResponse(body, { ok = true, status = 200, statusText = 'OK' } = {}) {
  return { ok, status, statusText, json: async () => body };
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

// Controlled-input helper: set the value through the native setter so
// React's onChange fires.
function setInputValue(input, value) {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(input, value);
  input.dispatchEvent(new window.Event('input', { bubbles: true }));
}

describe('PortfolioRiskCard (P7-D)', () => {
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

  it('renders the empty state before any compute', () => {
    const container = render(<PortfolioRiskCard />);
    expect(container.textContent).toContain(
      'Enter symbols and weights above, then Compute to run portfolio risk analytics.'
    );
    expect(container.textContent).toContain('Weights sum: 0.0%');
  });

  it('POSTs the entered weights and renders the data state', async () => {
    const fetchMock = vi.fn(async (url, options) => {
      expect(String(url)).toContain('/api/v1/analytics/portfolio/risk');
      expect(JSON.parse(options.body)).toEqual({
        weights: { INFY: 0.6, TCS: 0.4 },
        confidence: 0.99,
      });
      return jsonResponse(PORTFOLIO_PAYLOAD);
    });
    vi.stubGlobal('fetch', fetchMock);

    const container = render(<PortfolioRiskCard />);
    act(() => {
      setInputValue(container.querySelector('input[aria-label="Symbol 1"]'), 'INFY');
      setInputValue(container.querySelector('input[aria-label="Weight 1"]'), '60');
      setInputValue(container.querySelector('input[aria-label="Symbol 2"]'), 'TCS');
      setInputValue(container.querySelector('input[aria-label="Weight 2"]'), '40');
    });

    const compute = Array.from(container.querySelectorAll('button')).find(
      (button) => button.textContent === 'Compute'
    );
    await act(async () => {
      compute.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const text = container.textContent;
    expect(text).toContain('1.87%'); // VaR
    expect(text).toContain('2.45%'); // ES
    expect(text).toContain('1.12%'); // portfolio volatility
    expect(text).toContain('1.24'); // Sharpe
    expect(text).toContain('1.61'); // Sortino
    // Component VaR bars for both legs.
    expect(text).toContain('INFY');
    expect(text).toContain('TCS');
    // asOf stamp straight from the payload; no placeholder dashes.
    expect(text).toContain('as of 2026-10-10');
    expect(text).not.toContain('—');
  });

  it('renders the insufficient-history empty state on 422', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(
          {
            error: {
              code: 'insufficient_data',
              message:
                'insufficient data for portfolio risk: 42 return observations available, at least 250 required',
            },
          },
          { ok: false, status: 422, statusText: 'Unprocessable Entity' }
        )
      )
    );

    const container = render(<PortfolioRiskCard />);
    act(() => {
      setInputValue(container.querySelector('input[aria-label="Symbol 1"]'), 'INFY');
      setInputValue(container.querySelector('input[aria-label="Weight 1"]'), '60');
      setInputValue(container.querySelector('input[aria-label="Symbol 2"]'), 'TCS');
      setInputValue(container.querySelector('input[aria-label="Weight 2"]'), '40');
    });
    const compute = Array.from(container.querySelectorAll('button')).find(
      (button) => button.textContent === 'Compute'
    );
    await act(async () => {
      compute.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
    });

    expect(container.textContent).toContain('Not enough history (42 obs, need 250).');
  });
});
