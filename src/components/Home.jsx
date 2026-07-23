import React, { useEffect, useState } from 'react';
import { theme } from '../theme.js';
import { apiGet } from '../api.js';
import SearchInput from './SearchInput.jsx';

export default function Home() {
  const [portfolio, setPortfolio] = useState([]);
  const [newStock, setNewStock] = useState({ symbol: '', date: '', day: '', price: '' });
  const [indices, setIndices] = useState([]);
  const [indicesError, setIndicesError] = useState('');
  const [quotes, setQuotes] = useState({});

  // Live index snapshot cards from the local data platform.
  useEffect(() => {
    let cancelled = false;
    apiGet('/api/home/indices')
      .then((data) => {
        if (!cancelled) setIndices(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error('Failed to load home indices', err);
        if (!cancelled) setIndicesError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Live quotes for portfolio holdings (polled whenever the list changes).
  useEffect(() => {
    if (portfolio.length === 0) {
      setQuotes({});
      return undefined;
    }
    let cancelled = false;
    const symbols = portfolio.map((item) => item.symbol).join(',');
    const load = () => {
      apiGet(`/api/quotes?symbols=${encodeURIComponent(symbols)}`)
        .then((data) => {
          if (!cancelled) setQuotes((data && data.symbols) || {});
        })
        .catch((err) => console.error('Failed to load portfolio quotes', err));
    };
    load();
    const timer = setInterval(load, 60000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [portfolio]);

  const handleAddStock = () => {
    if (newStock.symbol && newStock.price) {
      setPortfolio([...portfolio, newStock]);
      setNewStock({ symbol: '', date: '', day: '', price: '' });
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Portfolio Section */}
      <section className={theme.card}>
        <h3 className={`text-xl mb-4 ${theme.goldText}`}>Manual Portfolio</h3>
        <div className="flex gap-2 mb-4">
          <SearchInput
            className="w-2/5"
            placeholder="Stock"
            onSelect={(item) => setNewStock({ ...newStock, symbol: item.symbol })}
          />
          <input type="date" className="bg-gray-800 p-2 rounded w-1/4" value={newStock.date} onChange={(e) => setNewStock({ ...newStock, date: e.target.value })} />
          <input type="number" placeholder="Entry Price" className="bg-gray-800 p-2 rounded w-1/4" value={newStock.price} onChange={(e) => setNewStock({ ...newStock, price: e.target.value })} />
          <button onClick={handleAddStock} className={`px-4 rounded ${theme.goldBg}`}>Add</button>
        </div>

        <table className="w-full text-left">
          <thead><tr className="border-b border-gray-700 text-gray-400"><th>Stock</th><th>Entry</th><th>Live</th><th>P&L</th></tr></thead>
          <tbody>
            {portfolio.map((item, i) => {
              const quote = quotes[item.symbol];
              const live = quote && typeof quote.value === 'number' ? quote.value : null;
              const entry = Number(item.price);
              const diff = live === null || Number.isNaN(entry) ? null : live - entry;
              return (
                <tr key={`${item.symbol}-${i}`} className="border-b border-gray-800">
                  <td className="py-2">{item.symbol}</td>
                  <td>{item.price}</td>
                  <td>{live === null ? '—' : live.toFixed(2)}</td>
                  <td className={diff === null ? 'text-gray-500' : diff >= 0 ? theme.profit : theme.loss}>
                    {diff === null ? '—' : `${diff > 0 ? '+' : ''}${diff.toFixed(2)}`}
                  </td>
                </tr>
              );
            })}
            {portfolio.length === 0 && (
              <tr><td colSpan="4" className="py-4 text-center text-gray-500">No holdings yet. Search for a stock above to add one.</td></tr>
            )}
          </tbody>
        </table>
      </section>

      {/* Indices Section */}
      <section className={theme.card}>
        <h3 className={`text-xl mb-4 ${theme.goldText}`}>Market Indices</h3>
        {indicesError && <p className="text-gray-500 text-sm mb-4">Live index feed unavailable — awaiting data sync.</p>}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {indices.map((index) => {
            const hasData = index && typeof index.value === 'number';
            const change = hasData && typeof index.change === 'number' ? index.change : null;
            const changePct = hasData && typeof index.changePct === 'number' ? index.changePct : null;
            const up = (change ?? 0) >= 0;
            return (
              <div
                key={index.symbol || index.name}
                className="p-4 bg-gray-800 rounded flex flex-col items-center justify-center text-center"
              >
                <span className="font-semibold text-white">{index.name}</span>
                {hasData ? (
                  <>
                    <span className="text-lg text-white">{index.value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                    <span className={up ? theme.profit : theme.loss}>
                      {up ? '▲' : '▼'} {change === null ? '—' : `${change > 0 ? '+' : ''}${change.toFixed(2)}`}
                      {' '}({changePct === null ? '—' : `${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}%`})
                    </span>
                  </>
                ) : (
                  <>
                    <span className="text-lg text-gray-500">—</span>
                    <span className="text-xs text-gray-500">awaiting data sync</span>
                  </>
                )}
              </div>
            );
          })}
          {indices.length === 0 && !indicesError && (
            <p className="text-gray-500 text-sm col-span-full">Loading indices...</p>
          )}
        </div>
      </section>
    </div>
  );
}
