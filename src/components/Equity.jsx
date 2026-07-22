import React, { useState } from 'react';
import { theme } from '../theme.js';

export default function Equity() {
  const tabs = ['Watchlist', 'NSE', 'BSE', 'Recommendations', 'Results', 'Top Gainers', 'Top Losers', 'Volume Shockers'];
  const [activeTab, setActiveTab] = useState('Watchlist');
  const [activeWatchlist, setActiveWatchlist] = useState('Watchlist 1');

  // Initialize 20 renamable watchlists
  const watchlists = Array.from({ length: 20 }, (_, i) => `Watchlist ${i + 1}`);

  return (
    <div>
      {/* Sub-navigation */}
      <div className="flex gap-4 border-b border-gray-700 pb-2 mb-6 overflow-x-auto">
        {tabs.map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={`pb-2 ${activeTab === tab ? 'border-b-2 border-red-500 text-red-500' : 'text-gray-400'}`}>
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
              {watchlists.map((w) => <option key={w} value={w}>{w}</option>)}
            </select>
            <span className="text-gray-400 text-sm">Max 50 stocks per list</span>
          </div>
          <p className="text-gray-500">Stock list rendering here... (Ready for graph API integration)</p>
        </div>
      )}

      {/* Dual Column Layout for Gainers/Losers/Shockers */}
      {['Top Gainers', 'Top Losers', 'Volume Shockers'].includes(activeTab) && (
        <div className="grid grid-cols-2 gap-8">
          <div className={theme.card}>
            <h4 className="text-white border-b border-gray-700 pb-2 mb-2 font-bold">NSE Breakdown</h4>
            {/* Data injected from Python Backend */}
          </div>
          <div className={theme.card}>
            <h4 className="text-white border-b border-gray-700 pb-2 mb-2 font-bold">BSE Breakdown</h4>
            {/* Data injected from Python Backend */}
          </div>
        </div>
      )}

      {activeTab === 'Results' && (
        <div className={theme.card}>
          <h4 className={theme.goldText}>Today's Quarterly Results</h4>
          {/* Table showing specific day result stocks */}
        </div>
      )}
    </div>
  );
}
