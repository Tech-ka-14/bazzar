// Bazzar Terminal - Electron main process.
// Loads the production renderer from dist/index.html and exposes only a
// narrow, context-isolated preload API to the renderer.
//
// Main-process services:
//  - app:get-info        app/version/repository-payload information
//  - scraper:*           safe test-bench scraper (offline sample mode works
//                        without network; optional URL mode fetches CSV/JSON)
//  - update:check        update notification check against the packaged
//                        electron/update-manifest.json (or the optional remote
//                        manifest at BAZZAR_UPDATE_MANIFEST_URL)
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const https = require('https');

const isDev = !!process.env.VITE_DEV_SERVER_URL;

// ---------------------------------------------------------------------------
// Repository payload info
// ---------------------------------------------------------------------------

// Recursively count files in a directory (best effort).
function countFiles(dir) {
  let count = 0;
  try {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        count += countFiles(full);
      } else if (entry.isFile()) {
        count += 1;
      }
    }
  } catch {
    /* ignore unreadable entries */
  }
  return count;
}

function getRepositoryInfo() {
  // electron-builder extraResources installs the original repository source
  // payload under <install>/resources/repository.
  const repoPath = path.join(process.resourcesPath, 'repository');
  try {
    const stat = fs.statSync(repoPath);
    if (stat.isDirectory()) {
      const topLevel = fs.readdirSync(repoPath).filter((name) => !name.startsWith('.'));
      return {
        path: repoPath,
        present: true,
        fileCount: countFiles(repoPath),
        sampleEntries: topLevel.slice(0, 25),
      };
    }
  } catch {
    /* payload not present (e.g. unpackaged dev run) */
  }
  return { path: repoPath, present: false, fileCount: 0, sampleEntries: [] };
}

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

// Compare dotted numeric versions: returns -1, 0 or 1.
function compareVersions(a, b) {
  const pa = String(a || '').split('.').map((part) => parseInt(part, 10) || 0);
  const pb = String(b || '').split('.').map((part) => parseInt(part, 10) || 0);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i += 1) {
    const x = pa[i] || 0;
    const y = pb[i] || 0;
    if (x < y) return -1;
    if (x > y) return 1;
  }
  return 0;
}

// Fetch a URL (http/https) with redirects and a timeout. Rejects on failure.
function fetchUrl(url, { timeoutMs = 20000, maxBytes = 10 * 1024 * 1024, redirects = 3 } = {}) {
  return new Promise((resolve, reject) => {
    let parsed;
    try {
      parsed = new URL(url);
    } catch {
      reject(new Error(`Invalid URL: ${url}`));
      return;
    }
    const transport = parsed.protocol === 'https:' ? https : parsed.protocol === 'http:' ? http : null;
    if (!transport) {
      reject(new Error(`Unsupported protocol: ${parsed.protocol}`));
      return;
    }
    const req = transport.get(parsed, { headers: { 'user-agent': 'bazzar-terminal/1.1.0' } }, (res) => {
      const status = res.statusCode || 0;
      if (status >= 300 && status < 400 && res.headers.location) {
        res.resume();
        if (redirects <= 0) {
          reject(new Error('Too many redirects'));
          return;
        }
        const next = new URL(res.headers.location, parsed).toString();
        fetchUrl(next, { timeoutMs, maxBytes, redirects: redirects - 1 }).then(resolve, reject);
        return;
      }
      if (status < 200 || status >= 300) {
        res.resume();
        reject(new Error(`Request failed with HTTP ${status}`));
        return;
      }
      const chunks = [];
      let received = 0;
      res.on('data', (chunk) => {
        received += chunk.length;
        if (received > maxBytes) {
          req.destroy(new Error(`Response exceeded ${maxBytes} bytes`));
          return;
        }
        chunks.push(chunk);
      });
      res.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
      res.on('error', reject);
    });
    req.setTimeout(timeoutMs, () => req.destroy(new Error('Request timed out')));
    req.on('error', reject);
  });
}

// Escape a value for CSV output.
function csvEscape(value) {
  const s = String(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

// Parse CSV text into records, honoring simple quoting. Returns array of
// string arrays; malformed lines are tolerated best-effort.
function parseCsvRecords(text) {
  const records = [];
  let field = '';
  let record = [];
  let inQuotes = false;
  const pushRecord = () => {
    record.push(field);
    field = '';
    // Skip completely empty lines.
    if (record.length > 1 || record[0].trim() !== '') records.push(record);
    record = [];
  };
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ',') {
      record.push(field);
      field = '';
    } else if (ch === '\n') {
      pushRecord();
    } else if (ch === '\r') {
      /* ignore */
    } else {
      field += ch;
    }
  }
  if (field !== '' || record.length > 0) pushRecord();
  return records;
}

// Normalize parsed CSV records into OHLCV rows. Column aliases are resolved
// from the header (Ticker/Symbol, Open, High, Low, Close, Volume, optional
// Date). Malformed rows are skipped; returns { rows, skipped }.
function normalizeCsvRows(text) {
  const records = parseCsvRecords(text);
  if (records.length === 0) return { rows: [], skipped: 0 };

  const header = records[0].map((h) => h.trim().toLowerCase());
  const findCol = (...names) => {
    for (const name of names) {
      const idx = header.indexOf(name);
      if (idx !== -1) return idx;
    }
    return -1;
  };
  const col = {
    symbol: findCol('symbol', 'ticker'),
    open: findCol('open'),
    high: findCol('high'),
    low: findCol('low'),
    close: findCol('close', 'adj close', 'adjclose', 'last'),
    volume: findCol('volume', 'vol'),
    date: findCol('date', 'time', 'timestamp'),
  };
  if (col.symbol === -1 || col.close === -1) {
    // No usable header: cannot normalize.
    return { rows: [], skipped: Math.max(0, records.length - 1), error: 'missing required columns' };
  }

  const num = (v) => {
    const cleaned = String(v || '').replace(/[,$]/g, '').trim();
    if (cleaned === '') return null;
    const n = Number(cleaned);
    return Number.isFinite(n) ? n : null;
  };

  const rows = [];
  let skipped = 0;
  for (const rec of records.slice(1)) {
    const symbol = String(rec[col.symbol] || '').trim().toUpperCase();
    const close = num(rec[col.close]);
    if (!symbol || close === null) {
      skipped += 1;
      continue;
    }
    const open = num(rec[col.open]) ?? close;
    const high = num(rec[col.high]) ?? Math.max(open, close);
    const low = num(rec[col.low]) ?? Math.min(open, close);
    const volume = num(rec[col.volume]) ?? 0;
    const date = col.date !== -1 ? String(rec[col.date] || '').trim() : '';
    rows.push({ date, symbol, open, high, low, close, volume });
  }
  return { rows, skipped };
}

// Convert a JSON document into OHLCV rows. Accepts an array of objects, or
// { data: [...] } / { rows: [...] } wrappers. Field names are normalized with
// the same aliases as the CSV path.
function normalizeJsonRows(text) {
  let doc;
  try {
    doc = JSON.parse(text);
  } catch {
    return { rows: [], skipped: 0, error: 'invalid JSON' };
  }
  const list = Array.isArray(doc)
    ? doc
    : Array.isArray(doc?.data)
      ? doc.data
      : Array.isArray(doc?.rows)
        ? doc.rows
        : null;
  if (!list) return { rows: [], skipped: 0, error: 'JSON is not an array of rows' };

  const pick = (obj, ...names) => {
    for (const name of names) {
      if (obj[name] !== undefined && obj[name] !== null && obj[name] !== '') return obj[name];
    }
    // Case-insensitive fallback.
    const lower = {};
    for (const key of Object.keys(obj)) lower[key.toLowerCase()] = obj[key];
    for (const name of names) {
      const v = lower[name.toLowerCase()];
      if (v !== undefined && v !== null && v !== '') return v;
    }
    return undefined;
  };
  const num = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };

  const rows = [];
  let skipped = 0;
  for (const item of list) {
    if (!item || typeof item !== 'object') {
      skipped += 1;
      continue;
    }
    const symbol = String(pick(item, 'symbol', 'ticker') || '').trim().toUpperCase();
    const close = num(pick(item, 'close', 'adj close', 'adjclose', 'last'));
    if (!symbol || close === null) {
      skipped += 1;
      continue;
    }
    const open = num(pick(item, 'open')) ?? close;
    const high = num(pick(item, 'high')) ?? Math.max(open, close);
    const low = num(pick(item, 'low')) ?? Math.min(open, close);
    const volume = num(pick(item, 'volume', 'vol')) ?? 0;
    const date = String(pick(item, 'date', 'time', 'timestamp') || '').trim();
    rows.push({ date, symbol, open, high, low, close, volume });
  }
  return { rows, skipped };
}

// Analyze OHLCV rows: row count, unique symbols, date range, close stats,
// total volume, and top absolute close-to-open movers.
function analyzeRows(rows) {
  const symbols = new Set();
  let minDate = null;
  let maxDate = null;
  let closeSum = 0;
  let minClose = null;
  let maxClose = null;
  let totalVolume = 0;

  for (const r of rows) {
    symbols.add(r.symbol);
    if (r.date) {
      if (minDate === null || r.date < minDate) minDate = r.date;
      if (maxDate === null || r.date > maxDate) maxDate = r.date;
    }
    closeSum += r.close;
    if (minClose === null || r.close < minClose) minClose = r.close;
    if (maxClose === null || r.close > maxClose) maxClose = r.close;
    totalVolume += r.volume || 0;
  }

  const topMovers = rows
    .map((r) => ({
      date: r.date || null,
      symbol: r.symbol,
      open: r.open,
      close: r.close,
      absChange: Math.abs(r.close - r.open),
      pctChange: r.open ? ((r.close - r.open) / r.open) * 100 : 0,
    }))
    .sort((a, b) => b.absChange - a.absChange)
    .slice(0, 10)
    .map((m) => ({
      ...m,
      absChange: Number(m.absChange.toFixed(4)),
      pctChange: Number(m.pctChange.toFixed(2)),
    }));

  return {
    rowCount: rows.length,
    uniqueSymbols: symbols.size,
    symbols: Array.from(symbols).sort(),
    dateRange: { min: minDate, max: maxDate },
    averageClose: rows.length ? Number((closeSum / rows.length).toFixed(4)) : null,
    minClose,
    maxClose,
    totalVolume,
    topMovers,
  };
}

// ---------------------------------------------------------------------------
// Scraper test-bench service (main process only; renderer has no Node access)
// ---------------------------------------------------------------------------

const SCRAPER_OUTPUT_NAME = 'daily_ohlcv.csv';
const SCRAPER_SAMPLE_SYMBOLS = [
  'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'TATAMOTORS', 'ITC',
];
const SCRAPER_SAMPLE_DAYS = 60;
// Flush to disk in chunks so pause/cancel remain responsive mid-scrape.
const SCRAPER_CHUNK_ROWS = 200;

const scraperState = {
  status: 'idle', // idle | running | paused | cancelled | completed | error
  mode: null,
  progress: { processed: 0, total: 0 },
  outputPath: null,
  error: null,
  rowCount: 0,
};

function scraperSnapshot() {
  return {
    status: scraperState.status,
    mode: scraperState.mode,
    progress: { ...scraperState.progress },
    outputPath: scraperState.outputPath,
    error: scraperState.error,
    rowCount: scraperState.rowCount,
  };
}

function broadcastScraperStatus() {
  for (const win of BrowserWindow.getAllWindows()) {
    win.webContents.send('scraper:status', scraperSnapshot());
  }
}

// Deterministic pseudo-random generator for reproducible offline samples.
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Generate the offline sample dataset (no network required).
function generateSampleRows() {
  const rand = mulberry32(20250115);
  const rows = [];
  const start = new Date('2024-11-01T00:00:00Z');
  for (let s = 0; s < SCRAPER_SAMPLE_SYMBOLS.length; s += 1) {
    const symbol = SCRAPER_SAMPLE_SYMBOLS[s];
    let prevClose = 100 + s * 55 + rand() * 25;
    let emitted = 0;
    for (let d = 0; emitted < SCRAPER_SAMPLE_DAYS; d += 1) {
      const day = new Date(start.getTime() + d * 86400000);
      const dow = day.getUTCDay();
      if (dow === 0 || dow === 6) continue; // skip weekends
      const drift = (rand() - 0.48) * 0.04;
      const open = prevClose * (1 + (rand() - 0.5) * 0.01);
      const close = open * (1 + drift);
      const high = Math.max(open, close) * (1 + rand() * 0.012);
      const low = Math.min(open, close) * (1 - rand() * 0.012);
      const volume = Math.floor(200000 + rand() * 4800000);
      rows.push({
        date: day.toISOString().slice(0, 10),
        symbol,
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume,
      });
      prevClose = close;
      emitted += 1;
    }
  }
  return rows;
}

function scraperOutputPath() {
  return path.join(app.getPath('userData'), SCRAPER_OUTPUT_NAME);
}

// Write rows to the output CSV in chunks, honoring pause/cancel between
// chunks and reporting progress after each flush.
async function writeRowsWithProgress(rows) {
  const outPath = scraperOutputPath();
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, 'Date,Symbol,Open,High,Low,Close,Volume\n', 'utf8');

  scraperState.outputPath = outPath;
  scraperState.progress = { processed: 0, total: rows.length };
  broadcastScraperStatus();

  let offset = 0;
  while (offset < rows.length) {
    if (scraperState.status === 'cancelled') return;
    if (scraperState.status === 'paused') {
      await new Promise((resolve) => setTimeout(resolve, 150));
      continue;
    }
    const chunk = rows.slice(offset, offset + SCRAPER_CHUNK_ROWS);
    const lines = chunk.map((r) =>
      [r.date || '', r.symbol, r.open, r.high, r.low, r.close, r.volume].map(csvEscape).join(',')
    );
    fs.appendFileSync(outPath, `${lines.join('\n')}\n`, 'utf8');
    offset += chunk.length;
    scraperState.progress.processed = offset;
    scraperState.rowCount = offset;
    broadcastScraperStatus();
    // Yield so IPC (pause/cancel/status) can be processed between chunks.
    await new Promise((resolve) => setTimeout(resolve, 30));
  }
}

async function runScrape({ mode, url }) {
  try {
    if (mode === 'sample') {
      const rows = generateSampleRows();
      await writeRowsWithProgress(rows);
    } else if (mode === 'url') {
      if (!url || typeof url !== 'string') throw new Error('URL mode requires a url');
      const text = await fetchUrl(url);
      if (scraperState.status === 'cancelled') return;
      const trimmed = text.trimStart();
      const looksJson = trimmed.startsWith('[') || trimmed.startsWith('{');
      const parsed = looksJson ? normalizeJsonRows(text) : normalizeCsvRows(text);
      if (parsed.error) throw new Error(`Could not parse response: ${parsed.error}`);
      if (parsed.rows.length === 0) throw new Error('No usable rows found in response');
      await writeRowsWithProgress(parsed.rows);
    } else {
      throw new Error(`Unknown scrape mode: ${mode}`);
    }
    if (scraperState.status === 'cancelled') return;
    scraperState.status = 'completed';
  } catch (err) {
    if (scraperState.status === 'cancelled') return;
    scraperState.status = 'error';
    scraperState.error = err instanceof Error ? err.message : String(err);
  } finally {
    broadcastScraperStatus();
  }
}

// Read and parse the last written output CSV (or a caller-supplied path under
// userData) and return analysis + a small preview.
function analyzeScraperOutput(csvPath) {
  let target = csvPath || scraperState.outputPath || scraperOutputPath();
  // Constrain caller-supplied paths to the app's userData directory.
  if (csvPath) {
    const resolved = path.resolve(csvPath);
    const userDataDir = path.resolve(app.getPath('userData'));
    if (!resolved.startsWith(userDataDir + path.sep)) {
      return { ok: false, error: 'Analysis is restricted to files under the app data directory', path: resolved };
    }
    target = resolved;
  }
  if (!fs.existsSync(target)) {
    return { ok: false, error: `No scraped CSV found at ${target}`, path: target };
  }
  const text = fs.readFileSync(target, 'utf8');
  const { rows, skipped, error } = normalizeCsvRows(text);
  const analysis = analyzeRows(rows);
  return {
    ok: rows.length > 0,
    path: target,
    skippedRows: skipped,
    parseError: error || null,
    analysis,
    preview: rows.slice(0, 25),
  };
}

// ---------------------------------------------------------------------------
// Update notification service
// ---------------------------------------------------------------------------

function readPackagedManifest() {
  const manifestPath = path.join(__dirname, 'update-manifest.json');
  try {
    return { manifest: JSON.parse(fs.readFileSync(manifestPath, 'utf8')), source: manifestPath };
  } catch {
    return { manifest: null, source: manifestPath };
  }
}

async function checkForUpdates() {
  const currentVersion = app.getVersion();
  let manifest = null;
  let source = 'packaged';

  const remoteUrl = process.env.BAZZAR_UPDATE_MANIFEST_URL;
  if (remoteUrl) {
    try {
      manifest = JSON.parse(await fetchUrl(remoteUrl, { timeoutMs: 8000, maxBytes: 256 * 1024 }));
      source = 'remote';
    } catch {
      // Fall back to the packaged manifest on any remote failure.
    }
  }
  if (!manifest) {
    const packaged = readPackagedManifest();
    manifest = packaged.manifest;
  }

  if (!manifest || typeof manifest !== 'object') {
    return {
      enabled: false,
      updateAvailable: false,
      currentVersion,
      latestVersion: null,
      message: null,
      url: null,
      publishedAt: null,
      source,
      error: 'No update manifest available',
    };
  }

  const enabled = manifest.enabled !== false;
  const latestVersion = typeof manifest.latestVersion === 'string' ? manifest.latestVersion : null;
  // Per the update-notification contract, the banner is shown when the
  // notification is enabled and the manifest's latestVersion is at least the
  // running version: 1.1.0 ships with latestVersion 1.1.0 + enabled so
  // installed 1.1.0 instances display the banner ("notification toggled on").
  const updateAvailable =
    enabled && !!latestVersion && compareVersions(latestVersion, currentVersion) >= 0;

  return {
    enabled,
    updateAvailable,
    currentVersion,
    latestVersion,
    message: typeof manifest.message === 'string' ? manifest.message : null,
    url: typeof manifest.url === 'string' ? manifest.url : null,
    publishedAt: typeof manifest.publishedAt === 'string' ? manifest.publishedAt : null,
    source,
    error: null,
  };
}

// ---------------------------------------------------------------------------
// Window + IPC wiring
// ---------------------------------------------------------------------------

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: '#000000',
    title: 'Bazzar Terminal',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
    },
  });

  // Harden navigation: deny new windows and external navigation by default.
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (event, url) => {
    if (!isDev && !url.startsWith('file://')) {
      event.preventDefault();
    }
  });

  if (isDev) {
    win.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }
}

app.whenReady().then(() => {
  // Narrow IPC surface: app/version/repository-payload information.
  ipcMain.handle('app:get-info', () => ({
    name: app.getName(),
    version: app.getVersion(),
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node,
    platform: process.platform,
    arch: process.arch,
    repository: getRepositoryInfo(),
  }));

  // Scraper test-bench IPC.
  ipcMain.handle('scraper:start', (_event, options) => {
    if (scraperState.status === 'running' || scraperState.status === 'paused') {
      return scraperSnapshot();
    }
    const mode = options?.mode === 'url' ? 'url' : 'sample';
    const url = typeof options?.url === 'string' ? options.url.trim() : '';
    scraperState.status = 'running';
    scraperState.mode = mode;
    scraperState.progress = { processed: 0, total: 0 };
    scraperState.error = null;
    scraperState.rowCount = 0;
    scraperState.outputPath = scraperOutputPath();
    broadcastScraperStatus();
    runScrape({ mode, url });
    return scraperSnapshot();
  });
  ipcMain.handle('scraper:pause', () => {
    if (scraperState.status === 'running') {
      scraperState.status = 'paused';
      broadcastScraperStatus();
    }
    return scraperSnapshot();
  });
  ipcMain.handle('scraper:resume', () => {
    if (scraperState.status === 'paused') {
      scraperState.status = 'running';
      broadcastScraperStatus();
    }
    return scraperSnapshot();
  });
  ipcMain.handle('scraper:cancel', () => {
    if (scraperState.status === 'running' || scraperState.status === 'paused') {
      scraperState.status = 'cancelled';
      broadcastScraperStatus();
    }
    return scraperSnapshot();
  });
  ipcMain.handle('scraper:status', () => scraperSnapshot());
  ipcMain.handle('scraper:analyze', (_event, options) =>
    analyzeScraperOutput(typeof options?.path === 'string' ? options.path : null)
  );

  // Update notification IPC.
  ipcMain.handle('update:check', () => checkForUpdates());

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
