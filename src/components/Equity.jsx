import React, { useState } from 'react';
import { theme } from '../theme.js';
import { chartUrl } from '../api.js';
import SearchInput from './SearchInput.jsx';
import ChartImage from './ChartImage.jsx';
import RiskPanel from './RiskPanel.jsx';

const MAX_WATCHLIST_STOCKS = 50;

export default function Equity() {
  const tabs = [
    'Watchlist',
    'NSE',
    'BSE',
    'Recommendations',
    'Results',
    'Top Gainers',
    'Top Losers',
    'Volume Shockers',
  ];
  const [activeTab, setActiveTab] = useState('Watchlist');
  const [activeWatchlist, setActiveWatchlist] = useState('Watchlist 1');
  // Local state: watchlist name -> array of { symbol, name, exchange }.
  const [watchlistStocks, setWatchlistStocks] = useState({});
  // Deep-dive selection (P7-D): a stock picked from the watchlist or the
  // search box below; drives the chart + risk analytics panel.
  const [deepDive, setDeepDive] = useState(null);

  // Initialize 20 renamable watchlists
  const watchlists = Array.from({ length: 20 }, (_, i) => `Watchlist ${i + 1}`);
  const currentStocks = watchlistStocks[activeWatchlist] || [];

  const handleAddStock = (item) => {
    setWatchlistStocks((prev) => {
      const list = prev[activeWatchlist] || [];
      if (list.length >= MAX_WATCHLIST_STOCKS) return prev;
      if (list.some((entry) => entry.symbol === item.symbol)) return prev;
      return { ...prev, [activeWatchlist]: [...list, item] };
    });
  };

  const handleRemoveStock = (symbol) => {
    setWatchlistStocks((prev) => ({
      ...prev,
      [activeWatchlist]: (prev[activeWatchlist] || []).filter((entry) => entry.symbol !== symbol),
    }));
  };

  return (
    <div>
      {/* Sub-navigation */}
      <div className="flex gap-4 border-b border-gray-700 pb-2 mb-6 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 ${activeTab === tab ? 'border-b-2 border-red-500 text-red-500' : 'text-gray-400'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Watchlist' && (
        <div className={theme.card}>
          <div className="flex justify-between items-center mb-4">
            <select
              className="bg-gray-800 border border-gray-600 text-white p-2 rounded"
              value={activeWatchlist}
              onChange={(e) => setActiveWatchlist(e.target.value)}
            >
              {watchlists.map((w) => (
                <option key={w} value={w}>
                  {w}
                </option>
              ))}
            </select>
            <span className="text-gray-400 text-sm">
              {currentStocks.length} / {MAX_WATCHLIST_STOCKS} stocks
            </span>
          </div>
          <SearchInput
            className="max-w-md mb-4"
            placeholder={`Add a stock to ${activeWatchlist}...`}
            onSelect={handleAddStock}
          />
          {currentStocks.length === 0 ? (
            <p className="text-gray-500">
              No stocks yet. Search above to add stocks to this watchlist.
            </p>
          ) : (
            <ul className="space-y-2">
              {currentStocks.map((stock) => (
                <li
                  key={stock.symbol}
                  className="flex items-center justify-between bg-gray-800 p-2 rounded text-sm cursor-pointer hover:bg-gray-700"
                  onClick={() => setDeepDive(stock)}
                  title="Open deep dive (chart + risk analytics)"
                >
                  <span className="font-bold text-yellow-500">{stock.symbol}</span>
                  <span className="flex-1 text-gray-300 truncate px-3">{stock.name}</span>
                  <span className="text-xs text-gray-500 mr-3">{stock.exchange}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveStock(stock.symbol);
                    }}
                    className="text-xs text-gray-400 hover:text-red-500 border border-gray-700 rounded px-2 py-1"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Stock deep dive (P7-D): pick any stock (watchlist click or search)
          to load its backend chart and the risk analytics panel. */}
      {activeTab === 'Watchlist' && (
        <div className={`${theme.card} mt-6`}>
          <h4 className={`text-lg font-bold ${theme.goldText} mb-4`}>Stock Deep Dive</h4>
          <SearchInput
            className="max-w-md mb-4"
            placeholder="Analyze any stock (chart + risk)..."
            onSelect={(item) => setDeepDive(item)}
          />
          {deepDive ? (
            <>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-400">
                  {deepDive.name} ({deepDive.symbol}
                  {deepDive.exchange ? ` · ${deepDive.exchange}` : ''})
                </p>
                <button
                  onClick={() => setDeepDive(null)}
                  className="text-xs text-gray-400 hover:text-red-500 border border-gray-700 rounded px-2 py-1"
                >
                  Close
                </button>
              </div>
              <ChartImage
                className="w-full rounded bg-gray-950 mb-4"
                src={chartUrl(
                  'stocks',
                  deepDive.symbol,
                  deepDive.exchange ? { exchange: deepDive.exchange } : {}
                )}
                alt={`${deepDive.symbol} chart`}
              />
              <RiskPanel symbol={deepDive.symbol} />
            </>
          ) : (
            <p className="text-gray-500 text-sm">
              Search a stock above or click one in the watchlist to load its chart and risk
              analytics.
            </p>
          )}
        </div>
      )}

      {/* Dual Column Layout for Gainers/Losers/Shockers */}
      {['Top Gainers', 'Top Losers', 'Volume Shockers'].includes(activeTab) && (
        <div className="grid grid-cols-2 gap-8">
          <div className={theme.card}>
            <h4 className="text-white border-b border-gray-700 pb-2 mb-2 font-bold">
              NSE Breakdown
            </h4>
            {/* Data injected from Python Backend */}
          </div>
          <div className={theme.card}>
            <h4 className="text-white border-b border-gray-700 pb-2 mb-2 font-bold">
              BSE Breakdown
            </h4>
            {/* Data injected from Python Backend */}
          </div>
        </div>
      )}

      {activeTab === 'Results' && (
        <div className={theme.card}>
          <h4 className={theme.goldText}>Today&apos;s Quarterly Results</h4>
          {/* Table showing specific day result stocks */}
        </div>
      )}
    </div>
  );
}
