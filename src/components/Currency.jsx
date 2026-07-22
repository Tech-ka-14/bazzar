import React from 'react';
import { theme } from '../theme.js';

export default function Currency() {
  const mainRates = ['USDINR', 'EURINR', 'USDJPY', 'JPYINR'];
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <section className={theme.card}>
        <div className="flex justify-between items-center mb-4">
          <h3 className={`text-xl ${theme.goldText}`}>Live Currency Rates</h3>
          {/* Search Dropdown - No data storage */}
          <input type="search" placeholder="Search currency..." className="bg-gray-800 p-1 rounded text-white border border-gray-600" list="currencies" />
          <datalist id="currencies"><option value="GBPUSD" /><option value="AUDUSD" /></datalist>
        </div>
        <div className="space-y-4">
          {mainRates.map((rate) => (
            <div key={rate} className="flex justify-between items-center bg-gray-800 p-3 rounded">
              <span className="font-bold">{rate}</span>
              {/* Placeholder for the tiny daily candle graph */}
              <div className="w-32 h-8 bg-gray-700 rounded flex items-center justify-center text-xs text-gray-400 border border-gray-600">
                [Daily Candle Graph]
              </div>
              <span className={theme.profit}>+0.12%</span>
            </div>
          ))}
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
