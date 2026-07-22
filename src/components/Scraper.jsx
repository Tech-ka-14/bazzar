import React, { useCallback, useEffect, useRef, useState } from 'react';
import { theme } from '../theme.js';

// Scraper test-bench tab. All scraping/parsing/analysis runs in the Electron
// main process behind the narrow window.bazzar scraper IPC API; this
// component only renders status, progress, analysis and a data preview.
// In browser mode (vite dev without Electron) a fallback notice is shown.

const STATUS_STYLES = {
  idle: 'text-gray-400 border-gray-600',
  running: 'text-yellow-500 border-yellow-500',
  paused: 'text-blue-400 border-blue-400',
  cancelled: 'text-red-500 border-red-500',
  completed: 'text-green-500 border-green-500',
  error: 'text-red-500 border-red-500',
};

function StatCard({ label, value }) {
  return (
    <div className={`${theme.card} p-3`}>
      <div className="text-xs uppercase tracking-wide text-gray-400">{label}</div>
      <div className="text-lg font-bold text-white break-all">{value ?? '—'}</div>
    </div>
  );
}

export default function Scraper() {
  const hasBridge = typeof window !== 'undefined' && !!window.bazzar?.scraperStart;
  const [mode, setMode] = useState('sample');
  const [url, setUrl] = useState('');
  const [snapshot, setSnapshot] = useState(null);
  const [result, setResult] = useState(null);
  const [uiError, setUiError] = useState(null);
  const busyRef = useRef(false);

  const applySnapshot = useCallback((snap) => {
    if (snap) setSnapshot(snap);
  }, []);

  useEffect(() => {
    if (!hasBridge) return undefined;
    let cancelled = false;
    window.bazzar
      .scraperGetStatus()
      .then((snap) => {
        if (!cancelled) applySnapshot(snap);
      })
      .catch(() => {});
    const unsubscribe = window.bazzar.onScraperStatus?.((snap) => {
      if (!cancelled) applySnapshot(snap);
    });
    return () => {
      cancelled = true;
      if (typeof unsubscribe === 'function') unsubscribe();
    };
  }, [hasBridge, applySnapshot]);

  const guard = async (fn) => {
    if (busyRef.current) return;
    busyRef.current = true;
    setUiError(null);
    try {
      await fn();
    } catch (err) {
      setUiError(err instanceof Error ? err.message : String(err));
    } finally {
      busyRef.current = false;
    }
  };

  const handleStart = () =>
    guard(async () => {
      setResult(null);
      const snap = await window.bazzar.scraperStart({ mode, url: mode === 'url' ? url : undefined });
      applySnapshot(snap);
    });
  const handlePause = () => guard(async () => applySnapshot(await window.bazzar.scraperPause()));
  const handleResume = () => guard(async () => applySnapshot(await window.bazzar.scraperResume()));
  const handleCancel = () => guard(async () => applySnapshot(await window.bazzar.scraperCancel()));
  const handleAnalyze = () =>
    guard(async () => {
      const res = await window.bazzar.scraperAnalyze();
      setResult(res);
      if (!res.ok && res.error) setUiError(res.error);
    });

  if (!hasBridge) {
    return (
      <div className={theme.card}>
        <h2 className={`text-xl font-bold ${theme.goldText} mb-2`}>Scraper Test-Bench</h2>
        <p className="text-gray-300">
          The scraper runs inside the Electron main process. Launch the desktop app
          (<code className="text-yellow-500">npm start</code> or the installed Bazzar Terminal) to
          use this tab; it is unavailable in plain browser mode.
        </p>
      </div>
    );
  }

  const status = snapshot?.status ?? 'idle';
  const processed = snapshot?.progress?.processed ?? 0;
  const total = snapshot?.progress?.total ?? 0;
  const pct = total > 0 ? Math.min(100, Math.round((processed / total) * 100)) : status === 'completed' ? 100 : 0;
  const analysis = result?.analysis ?? null;

  return (
    <div className="space-y-6">
      <div className={theme.card}>
        <h2 className={`text-xl font-bold ${theme.goldText} mb-1`}>Scraper Test-Bench</h2>
        <p className="text-sm text-gray-400 mb-4">
          Safe Electron-main scraper for product testing. Offline sample mode needs no network; URL
          mode fetches a CSV or JSON document through the main process. Rows are normalized to
          Symbol/Open/High/Low/Close/Volume (+ optional Date) and written to{' '}
          <code className="text-yellow-500">daily_ohlcv.csv</code> under the app data directory.
        </p>

        <div className="flex flex-wrap items-center gap-4 mb-4">
          <label className="flex items-center gap-2 text-sm text-gray-300">
            <input type="radio" name="scrape-mode" checked={mode === 'sample'} onChange={() => setMode('sample')} />
            Offline sample data (no network)
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-300">
            <input type="radio" name="scrape-mode" checked={mode === 'url'} onChange={() => setMode('url')} />
            Fetch CSV/JSON URL
          </label>
          {mode === 'url' && (
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/daily_ohlcv.csv"
              className="flex-1 min-w-64 p-2 bg-gray-800 text-white rounded border border-gray-700 focus:border-yellow-500 outline-none text-sm"
            />
          )}
        </div>

        <div className="flex flex-wrap gap-3 mb-4">
          <button
            onClick={handleStart}
            disabled={status === 'running' || status === 'paused' || (mode === 'url' && !url.trim())}
            className={`px-4 py-2 rounded font-bold ${theme.goldBg} disabled:opacity-40 disabled:cursor-not-allowed`}
          >
            Start Scrape
          </button>
          <button
            onClick={handlePause}
            disabled={status !== 'running'}
            className="px-4 py-2 rounded font-bold bg-gray-700 text-white hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Pause
          </button>
          <button
            onClick={handleResume}
            disabled={status !== 'paused'}
            className="px-4 py-2 rounded font-bold bg-gray-700 text-white hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Resume
          </button>
          <button
            onClick={handleCancel}
            disabled={status !== 'running' && status !== 'paused'}
            className="px-4 py-2 rounded font-bold bg-red-600 text-white hover:bg-red-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleAnalyze}
            disabled={status === 'running' || status === 'paused'}
            className="px-4 py-2 rounded font-bold bg-gray-700 text-white hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Analyze CSV
          </button>
        </div>

        <div className="flex items-center gap-4 mb-2">
          <span className={`px-3 py-1 rounded border text-sm font-bold uppercase ${STATUS_STYLES[status] || STATUS_STYLES.idle}`}>
            {status}
          </span>
          <div className="flex-1 h-3 bg-gray-800 rounded overflow-hidden">
            <div className="h-full bg-yellow-500 transition-all" style={{ width: `${pct}%` }} />
          </div>
          <span className="text-sm text-gray-400 whitespace-nowrap">
            {processed}
            {total > 0 ? ` / ${total}` : ''} rows
          </span>
        </div>

        {snapshot?.outputPath && (
          <p className="text-sm text-gray-400">
            Output: <code className="text-yellow-500 break-all">{snapshot.outputPath}</code>
          </p>
        )}
        {(snapshot?.error || uiError) && (
          <p className="text-sm text-red-500 mt-2">{snapshot?.error || uiError}</p>
        )}
      </div>

      {analysis && (
        <div className={theme.card}>
          <h3 className={`text-lg font-bold ${theme.goldText} mb-3`}>Analysis</h3>
          {result?.path && (
            <p className="text-xs text-gray-500 mb-3 break-all">
              Source: {result.path}
              {result.skippedRows ? ` (${result.skippedRows} malformed rows skipped)` : ''}
            </p>
          )}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <StatCard label="Rows" value={analysis.rowCount} />
            <StatCard label="Unique Symbols" value={analysis.uniqueSymbols} />
            <StatCard
              label="Date Range"
              value={
                analysis.dateRange?.min
                  ? `${analysis.dateRange.min} → ${analysis.dateRange.max}`
                  : '—'
              }
            />
            <StatCard label="Total Volume" value={analysis.totalVolume?.toLocaleString()} />
            <StatCard label="Avg Close" value={analysis.averageClose} />
            <StatCard label="Min Close" value={analysis.minClose} />
            <StatCard label="Max Close" value={analysis.maxClose} />
          </div>

          {analysis.topMovers?.length > 0 && (
            <>
              <h4 className="text-md font-bold text-white mb-2">Top |Close − Open| Movers</h4>
              <div className="overflow-x-auto mb-6">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400 border-b border-gray-700">
                      <th className="py-1 pr-4">Symbol</th>
                      <th className="py-1 pr-4">Date</th>
                      <th className="py-1 pr-4 text-right">Open</th>
                      <th className="py-1 pr-4 text-right">Close</th>
                      <th className="py-1 pr-4 text-right">|Δ|</th>
                      <th className="py-1 text-right">Δ%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.topMovers.map((m, i) => (
                      <tr key={`${m.symbol}-${m.date}-${i}`} className="border-b border-gray-800">
                        <td className="py-1 pr-4 font-bold text-white">{m.symbol}</td>
                        <td className="py-1 pr-4 text-gray-400">{m.date ?? '—'}</td>
                        <td className="py-1 pr-4 text-right text-gray-300">{m.open}</td>
                        <td className="py-1 pr-4 text-right text-gray-300">{m.close}</td>
                        <td className="py-1 pr-4 text-right text-yellow-500">{m.absChange}</td>
                        <td className={`py-1 text-right ${m.pctChange >= 0 ? theme.profit : theme.loss}`}>
                          {m.pctChange >= 0 ? '+' : ''}
                          {m.pctChange}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {result?.preview?.length > 0 && (
            <>
              <h4 className="text-md font-bold text-white mb-2">
                Data Preview (first {result.preview.length} rows)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400 border-b border-gray-700">
                      <th className="py-1 pr-4">Date</th>
                      <th className="py-1 pr-4">Symbol</th>
                      <th className="py-1 pr-4 text-right">Open</th>
                      <th className="py-1 pr-4 text-right">High</th>
                      <th className="py-1 pr-4 text-right">Low</th>
                      <th className="py-1 pr-4 text-right">Close</th>
                      <th className="py-1 text-right">Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.preview.map((r, i) => (
                      <tr key={`${r.symbol}-${r.date}-${i}`} className="border-b border-gray-800">
                        <td className="py-1 pr-4 text-gray-400">{r.date || '—'}</td>
                        <td className="py-1 pr-4 font-bold text-white">{r.symbol}</td>
                        <td className="py-1 pr-4 text-right text-gray-300">{r.open}</td>
                        <td className="py-1 pr-4 text-right text-gray-300">{r.high}</td>
                        <td className="py-1 pr-4 text-right text-gray-300">{r.low}</td>
                        <td className="py-1 pr-4 text-right text-gray-300">{r.close}</td>
                        <td className="py-1 text-right text-gray-300">{r.volume?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
