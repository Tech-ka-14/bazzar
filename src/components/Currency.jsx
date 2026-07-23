import React, { useEffect, useState } from 'react';
import { theme } from '../theme.js';
import { apiGet } from '../api.js';

const MAIN_RATES = ['USDINR', 'EURINR', 'USDJPY', 'JPYINR'];

export default function Currency() {
  const [quotes, setQuotes] = useState({});

  useEffect(() => {
    let cancelled = false;
    apiGet(`/api/quotes?symbols=${encodeURIComponent(MAIN_RATES.join(','))}`)
      .then((data) => {
        if (!cancelled) setQuotes((data && data.symbols) || {});
      })
      .catch((err) => console.error('Failed to load currency quotes', err));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <section className={theme.card}>
        <div className="flex justify-between items-center mb-4">
          <h3 className={`text-xl ${theme.goldText}`}>Live Currency Rates</h3>
          <input type="search" placeholder="Search currency..." className="bg-gray-800 p-1 rounded text-white border border-gray-600" list="currencies" />
          <datalist id="currencies"><option value="GBPUSD" /><option value="AUDUSD" /></datalist>
        </div>
        <div className="space-y-4">
          {MAIN_RATES.map((rate) => {
            const quote = quotes[rate];
            const hasData = quote && typeof quote.value === 'number';
            const pct = hasData && typeof quote.changePct === 'number' ? quote.changePct : null;
            const up = (pct ?? 0) >= 0;
            return (
              <div key={rate} className="flex justify-between items-center bg-gray-800 p-3 rounded">
                <span className="font-bold">{rate}</span>
                {hasData ? (
                  <span className="flex items-center gap-3">
                    <span className="text-white">{quote.value.toLocaleString('en-IN', { maximumFractionDigits: 4 })}</span>
                    {pct !== null && (
                      <span className={up ? theme.profit : theme.loss}>
                        {up ? '▲' : '▼'} {pct > 0 ? '+' : ''}{pct.toFixed(2)}%
                      </span>
                    )}
                  </span>
                ) : (
                  <span className="text-gray-500">—</span>
                )}
              </div>
            );
          })}
        </div>
      </section>

      <section className={theme.card}>
        <h3 className={`text-xl mb-4 ${theme.goldText}`}>Online Converter</h3>
        <div className="flex flex-col gap-4">
          <input type="number" placeholder="Amount" className="p-2 bg-gray-800 rounded border border-gray-700" />
          <div className="flex gap-4">
            <select className="p-2 bg-gray-800 rounded w-1/2 text-white"><option>USD</option><option>INR</option></select>
            <span className="text-white pt-2">to</span>
            <select className="p-2 bg-gray-800 rounded w-1/2 text-white"><option>INR</option><option>EUR</option></select>
          </div>
          <button className={`p-2 rounded mt-2 ${theme.goldBg} font-bold`}>CONVERT</button>
        </div>
      </section>
    </div>
  );
}
