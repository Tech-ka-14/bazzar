// P6 (roadmap 6.3): unit tests for the IPC payload validators used by
// electron/main.cjs. These pin the schema contract so a renderer can never
// push malformed or hostile input into the main process.
import { describe, expect, it } from 'vitest';
import {
  ALLOWED_EXTERNAL_HOSTS,
  validateExternalUrl,
  validateScraperAnalyze,
  validateScraperStart,
} from '../validation.cjs';

describe('validateExternalUrl', () => {
  it('accepts allowlisted https URLs', () => {
    const res = validateExternalUrl('https://kite.trade/connect/login?api_key=abc');
    expect(res.ok).toBe(true);
    expect(res.url).toContain('kite.trade');
    expect(validateExternalUrl('https://developers.kite.trade/apps').ok).toBe(true);
  });

  it('rejects non-allowlisted hosts', () => {
    expect(validateExternalUrl('https://evil.example.com').ok).toBe(false);
    expect(validateExternalUrl('https://kite.trade.evil.com').ok).toBe(false);
    expect(validateExternalUrl('https://sub.kite.trade').ok).toBe(false);
  });

  it('rejects non-https schemes', () => {
    expect(validateExternalUrl('http://kite.trade').ok).toBe(false);
    expect(validateExternalUrl('file:///etc/passwd').ok).toBe(false);
    expect(validateExternalUrl('javascript:alert(1)').ok).toBe(false);
  });

  it('rejects non-strings and garbage', () => {
    for (const bad of [undefined, null, 42, {}, [], 'not a url', '']) {
      expect(validateExternalUrl(bad).ok).toBe(false);
    }
  });

  it('keep the allowlist limited to Kite domains', () => {
    expect([...ALLOWED_EXTERNAL_HOSTS].sort()).toEqual(['developers.kite.trade', 'kite.trade']);
  });
});

describe('validateScraperStart', () => {
  it('accepts an absent payload (defaults to sample mode)', () => {
    expect(validateScraperStart(undefined)).toEqual({ ok: true, value: {} });
    expect(validateScraperStart(null).ok).toBe(true);
  });

  it('accepts sample mode', () => {
    const res = validateScraperStart({ mode: 'sample' });
    expect(res.ok).toBe(true);
    expect(res.value.mode).toBe('sample');
  });

  it('accepts url mode with an http(s) URL', () => {
    expect(validateScraperStart({ mode: 'url', url: 'https://example.com/data.csv' }).ok).toBe(
      true
    );
    expect(validateScraperStart({ mode: 'url', url: 'http://127.0.0.1/x.csv' }).ok).toBe(true);
  });

  it('rejects url mode without a usable URL', () => {
    expect(validateScraperStart({ mode: 'url' }).ok).toBe(false);
    expect(validateScraperStart({ mode: 'url', url: 'not a url' }).ok).toBe(false);
    expect(validateScraperStart({ mode: 'url', url: 'file:///etc/passwd' }).ok).toBe(false);
    expect(validateScraperStart({ mode: 'url', url: 'javascript:alert(1)' }).ok).toBe(false);
  });

  it('rejects malformed payloads and strips unknown keys', () => {
    expect(validateScraperStart('sample').ok).toBe(false);
    expect(validateScraperStart(42).ok).toBe(false);
    expect(validateScraperStart({ mode: 'evil' }).ok).toBe(false);
    expect(validateScraperStart({ mode: 'sample', exec: 'calc.exe' }).ok).toBe(false);
    expect(validateScraperStart({ url: 123 }).ok).toBe(false);
  });
});

describe('validateScraperAnalyze', () => {
  it('accepts an absent payload (null path = default output)', () => {
    expect(validateScraperAnalyze(undefined)).toEqual({ ok: true, path: null });
  });

  it('accepts a string path', () => {
    expect(validateScraperAnalyze({ path: 'C:\\data\\out.csv' })).toEqual({
      ok: true,
      path: 'C:\\data\\out.csv',
    });
  });

  it('rejects malformed payloads', () => {
    expect(validateScraperAnalyze({ path: 42 }).ok).toBe(false);
    expect(validateScraperAnalyze({ path: {}, extra: true }).ok).toBe(false);
    expect(validateScraperAnalyze('x').ok).toBe(false);
  });
});
