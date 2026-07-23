import React, { useEffect, useState } from 'react';
import { theme } from '../theme.js';
import { chartUrl } from '../api.js';
import SearchInput from './SearchInput.jsx';
import ChartImage from './ChartImage.jsx';
import IndexContribution from './IndexContribution.jsx';

// Market Analysis page: backend-rendered chart cards only. Benchmark charts
// (RBI bonds, US Treasury, SGB, repo rates) now live on the Benchmarks page.
export default function MarketAnalysis() {
  return (
    <div className="space-y-8">
      <ChartViewer />
      <UsdInrCard />
      <IndexContribution />
      <AppInfoCard />
    </div>
  );
}

// Compact chart viewer: pick any stock or index via dictionary search and
// view its backend matplotlib PNG chart.
function ChartViewer() {
  const [selection, setSelection] = useState(null);

  return (
    <section className={theme.card}>
      <h3 className={`text-xl mb-4 ${theme.goldText}`}>Chart Viewer</h3>
      <SearchInput
        className="max-w-md mb-4"
        placeholder="Search any stock or index..."
        onSelect={(item) => setSelection(item)}
      />
      {selection ? (
        <>
          <p className="text-sm text-gray-400 mb-2">
            {selection.name} ({selection.symbol}{selection.exchange ? ` · ${selection.exchange}` : ''})
          </p>
          <ChartImage
            src={chartUrl('stocks', selection.symbol, selection.exchange ? { exchange: selection.exchange } : {})}
            alt={`${selection.symbol} chart`}
          />
        </>
      ) : (
        <p className="text-gray-500 text-sm">Search for a symbol above to load its chart.</p>
      )}
    </section>
  );
}

// USDINR currency pair card backed by the renderer contract chart endpoint.
// Shows a graceful empty state until the backend has CDS data synced.
function UsdInrCard() {
  return (
    <section className={theme.card}>
      <h3 className={`text-xl mb-4 ${theme.goldText}`}>USDINR</h3>
      <ChartImage
        src={chartUrl('stocks', 'USDINR', { exchange: 'CDS' })}
        alt="USDINR currency pair chart"
      />
    </section>
  );
}

// Displays app/version/repository-payload information exposed by the
// context-isolated Electron preload API (window.bazzar). Falls back to a
// browser-mode message when running outside Electron (e.g. vite dev).
function AppInfoCard() {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    let cancelled = false;
    if (window.bazzar && typeof window.bazzar.getAppInfo === 'function') {
      window.bazzar
        .getAppInfo()
        .then((data) => {
          if (!cancelled) setInfo(data);
        })
        .catch((err) => console.error('Failed to load app info', err));
    }
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className={theme.card}>
      <h3 className={`text-xl mb-4 ${theme.goldText}`}>Terminal Info</h3>
      {info ? (
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <div className="flex justify-between"><dt className="text-gray-400">Application</dt><dd>{info.name}</dd></div>
          <div className="flex justify-between"><dt className="text-gray-400">Version</dt><dd>{info.version}</dd></div>
          <div className="flex justify-between"><dt className="text-gray-400">Electron</dt><dd>{info.electron}</dd></div>
          <div className="flex justify-between"><dt className="text-gray-400">Platform</dt><dd>{info.platform}</dd></div>
          <div className="flex justify-between"><dt className="text-gray-400">Repository payload</dt><dd>{info.repository?.present ? `${info.repository.fileCount} files` : 'not installed'}</dd></div>
          <div className="flex justify-between"><dt className="text-gray-400">Payload path</dt><dd className="truncate ml-4" title={info.repository?.path}>{info.repository?.path || '—'}</dd></div>
        </dl>
      ) : (
        <p className="text-gray-500 text-sm">
          Running in browser mode (no Electron preload API detected). App and repository
          payload details are available when launched via the Bazzar Terminal desktop shell.
        </p>
      )}
    </section>
  );
}
