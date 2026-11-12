// Bazzar Terminal - IPC payload validation (P6, roadmap 6.3).
//
// Every ipcMain.handle payload from the renderer is untrusted input: a
// compromised renderer (XSS, a malicious remote page) must not be able to
// push unexpected shapes into the main process. This module holds the zod
// schemas and the small allowlist helpers used by electron/main.cjs. It is
// plain CommonJS so both main.cjs (require) and the vitest suite
// (electron/__tests__/validation.test.js) can import it.
const { z } = require('zod');

// Hosts the renderer may ask the main process to open in the system browser
// (P3: Zerodha Kite Connect login). Exact-match allowlist, https only.
const ALLOWED_EXTERNAL_HOSTS = new Set(['kite.trade', 'developers.kite.trade']);

// scraper:start payload. mode 'url' additionally requires a usable http(s)
// URL; the URL itself is fetched by the main process with size/timeout caps.
const scraperStartSchema = z
  .object({
    mode: z.enum(['sample', 'url']).optional(),
    url: z.string().trim().max(2048).optional(),
  })
  .strict()
  .nullish();

// scraper:analyze payload: an optional path (constrained to the app userData
// directory by analyzeScraperOutput in main.cjs).
const scraperAnalyzeSchema = z
  .object({
    path: z.string().max(1024).optional(),
  })
  .strict()
  .nullish();

// Validate a scraper:start payload. Returns { ok: true, value } with the
// parsed (stripped) object, or { ok: false, error } with a human-readable
// message. A missing payload is valid (defaults to sample mode).
function validateScraperStart(options) {
  const parsed = scraperStartSchema.safeParse(options);
  if (!parsed.success) {
    return { ok: false, error: 'Invalid scraper options' };
  }
  const value = parsed.data ?? {};
  if (value.mode === 'url') {
    if (!value.url) {
      return { ok: false, error: 'URL mode requires a url' };
    }
    let parsedUrl;
    try {
      parsedUrl = new URL(value.url);
    } catch {
      return { ok: false, error: 'Invalid URL' };
    }
    if (parsedUrl.protocol !== 'https:' && parsedUrl.protocol !== 'http:') {
      return { ok: false, error: 'Only http(s) URLs can be scraped' };
    }
  }
  return { ok: true, value };
}

// Validate a scraper:analyze payload. Returns { ok: true, path } (path may be
// null = use the default output CSV) or { ok: false, error }.
function validateScraperAnalyze(options) {
  const parsed = scraperAnalyzeSchema.safeParse(options);
  if (!parsed.success) {
    return { ok: false, error: 'Invalid analyze options' };
  }
  return { ok: true, path: parsed.data?.path ?? null };
}

// Validate a shell:open-external URL against the allowlist. Returns
// { ok: true, url } (normalized) or { ok: false, error }.
function validateExternalUrl(url) {
  const parsed = z.string().max(2048).safeParse(url);
  if (!parsed.success) {
    return { ok: false, error: 'Invalid URL' };
  }
  let parsedUrl;
  try {
    parsedUrl = new URL(parsed.data);
  } catch {
    return { ok: false, error: 'Invalid URL' };
  }
  if (parsedUrl.protocol !== 'https:') {
    return { ok: false, error: 'URL not allowed' };
  }
  if (!ALLOWED_EXTERNAL_HOSTS.has(parsedUrl.hostname)) {
    return { ok: false, error: 'URL not allowed' };
  }
  return { ok: true, url: parsedUrl.toString() };
}

module.exports = {
  ALLOWED_EXTERNAL_HOSTS,
  validateScraperStart,
  validateScraperAnalyze,
  validateExternalUrl,
};
