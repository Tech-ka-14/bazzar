import React, { useEffect, useState } from 'react';
import { theme } from './theme.js';
import Home from './components/Home.jsx';
import Equity from './components/Equity.jsx';
import Commodities from './components/Commodities.jsx';
import Currency from './components/Currency.jsx';
import MarketAnalysis from './components/MarketAnalysis.jsx';
import Benchmarks from './components/Benchmarks.jsx';
import Indices from './components/Indices.jsx';
import InternationalMarkets from './components/InternationalMarkets.jsx';
import Scraper from './components/Scraper.jsx';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activePage, setActivePage] = useState('Home');

  if (!isAuthenticated) return <Login onLogin={() => setIsAuthenticated(true)} />;

  return (
    <div className={theme.bg}>
      <UpdateBanner />
      <Topbar activePage={activePage} setActivePage={setActivePage} />
      <main className="p-6">
        {activePage === 'Home' && <Home />}
        {activePage === 'Equity' && <Equity />}
        {activePage === 'Commodities' && <Commodities />}
        {activePage === 'Currency' && <Currency />}
        {activePage === 'Market Analysis' && <MarketAnalysis />}
        {activePage === 'Benchmarks' && <Benchmarks />}
        {activePage === 'Indices' && <Indices />}
        {activePage === 'International Markets' && <InternationalMarkets />}
        {activePage === 'Scraper' && <Scraper />}
      </main>
    </div>
  );
}

// --- Update Notification Banner ---
// Shown when the Electron-main update check reports an enabled manifest whose
// latestVersion is at least the running app version. Notification only;
// this is not an auto-updater.
function UpdateBanner() {
  const [update, setUpdate] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (window.bazzar && typeof window.bazzar.checkForUpdates === 'function') {
      window.bazzar
        .checkForUpdates()
        .then((info) => {
          if (!cancelled && info && info.enabled && info.updateAvailable) setUpdate(info);
        })
        .catch((err) => console.error('Update check failed', err));
    }
    return () => {
      cancelled = true;
    };
  }, []);

  if (!update || dismissed) return null;

  return (
    <div className="bg-yellow-500 text-black px-4 py-2 flex items-center justify-between gap-4">
      <div className="text-sm font-semibold">
        {update.message || `Bazzar Terminal ${update.latestVersion} is available.`}
        {update.url && (
          <span className="ml-2 font-mono text-xs break-all">({update.url})</span>
        )}
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="px-2 py-1 text-xs font-bold border border-black rounded hover:bg-black hover:text-yellow-500 transition-colors"
      >
        DISMISS
      </button>
    </div>
  );
}

// --- Login Component ---
function Login({ onLogin }) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-black">
      <div className={`${theme.card} w-96 border-yellow-500 border-t-4`}>
        <h2 className={`text-2xl mb-6 font-bold ${theme.goldText} text-center`}>Terminal Login</h2>
        <input type="text" placeholder="Name" className="w-full mb-4 p-2 bg-gray-800 text-white rounded border border-gray-700 focus:border-yellow-500 outline-none" />
        <input type="password" placeholder="Password" className="w-full mb-6 p-2 bg-gray-800 text-white rounded border border-gray-700 focus:border-yellow-500 outline-none" />
        <button onClick={onLogin} className={`w-full py-2 rounded font-bold ${theme.goldBg}`}>ENTER</button>
      </div>
    </div>
  );
}

// --- Topbar Navigation ---
function Topbar({ activePage, setActivePage }) {
  const pages = ['Home', 'Equity', 'Commodities', 'Currency', 'Market Analysis', 'Benchmarks', 'Indices', 'International Markets', 'Scraper'];
  return (
    <nav className="bg-gray-900 border-b-2 border-yellow-500 p-4 flex gap-6 overflow-x-auto">
      {pages.map((page) => (
        <button
          key={page}
          onClick={() => setActivePage(page)}
          className={`font-semibold tracking-wide whitespace-nowrap ${activePage === page ? theme.goldText : 'text-gray-400 hover:text-white'}`}
        >
          {page}
        </button>
      ))}
    </nav>
  );
}
