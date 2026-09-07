import { describe, expect, it } from 'vitest';
import { API_BASE, chartUrl } from '../api.js';

describe('api.js', () => {
  it('uses the local backend base by default', () => {
    expect(API_BASE).toBe('http://127.0.0.1:8787');
  });

  it('builds chart URLs without params', () => {
    expect(chartUrl('indices', 'NIFTY 50')).toBe(`${API_BASE}/api/indices/NIFTY%2050/chart.png`);
  });

  it('builds chart URLs with query params and skips empties', () => {
    expect(chartUrl('stocks', 'INFY', { exchange: 'NSE', skip: '' })).toBe(
      `${API_BASE}/api/stocks/INFY/chart.png?exchange=NSE`
    );
  });
});
