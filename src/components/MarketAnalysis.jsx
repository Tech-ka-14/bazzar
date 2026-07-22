import React, { useEffect, useMemo, useState } from 'react';
import { theme } from '../theme.js';
import { generateMockOHLC, toLineData } from '../mockData.js';
import ChartDashboard from './ChartDashboard.jsx';
import USDINRChart from './USDINRChart.jsx';
import RBIBondsChart from './RBIBondsChart.jsx';
import RepoRatesChart from './RepoRatesChart.jsx';
import SGBChart from './SGBChart.jsx';
import USTreasuryBondsChart from './USTreasuryBondsChart.jsx';
import IndexContribution from './IndexContribution.jsx';

// Market Analysis page: renders the terminal's chart components against
// deterministic mock data until a live data backend is connected.
export default function MarketAnalysis() {
  const primaryData = useMemo(() => generateMockOHLC({ startPrice: 150, seed: 7 }), []);
  const comparisonData = useMemo(() => generateMockOHLC({ startPrice: 140, seed: 21 }), []);
  const usdinrData = useMemo(() => generateMockOHLC({ startPrice: 83, seed: 3 }), []);
  const rbiBondData = useMemo(() => toLineData(generateMockOHLC({ startPrice: 7.2, seed: 11 })), []);
  const usTreasuryData = useMemo(() => toLineData(generateMockOHLC({ startPrice: 4.4, seed: 13 })), []);
  const sgbData = useMemo(() => generateMockOHLC({ startPrice: 6200, seed: 17 }), []);
  const indiaRepoData = useMemo(() => toLineData(generateMockOHLC({ startPrice: 6.5, seed: 23 })), []);
  const usFedData = useMemo(() => toLineData(generateMockOHLC({ startPrice: 5.4, seed: 29 })), []);

  return (
    <div className="space-y-8">
      <ChartDashboard data={primaryData} comparisonData={comparisonData} />
      <USDINRChart data={usdinrData} />
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <RBIBondsChart data={rbiBondData} />
        <USTreasuryBondsChart data={usTreasuryData} />
      </div>
      <SGBChart data={sgbData} />
      <RepoRatesChart indiaRepoData={indiaRepoData} usFedData={usFedData} />
      <IndexContribution />
      <AppInfoCard />
    </div>
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
