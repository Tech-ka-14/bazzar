import React, { useState } from 'react';
import { theme } from '../theme.js';

export default function Home() {
  const [portfolio, setPortfolio] = useState([]);
  const [newStock, setNewStock] = useState({ symbol: '', date: '', day: '', price: '' });

  const indices = ['Sensex', 'Nifty', 'Banknifty', 'Midcapnifty', 'Crudeoil', 'Natural gas', 'India VIX', 'Gold', 'Silver'];
  const clickableIndices = ['Sensex', 'Nifty', 'Banknifty', 'Midcapnifty'];

  const handleAddStock = () => {
    if (newStock.symbol && newStock.price) {
      setPortfolio([...portfolio, { ...newStock, currentPrice: Number(newStock.price) * 1.05 }]); // Mocking a 5% live movement
      setNewStock({ symbol: '', date: '', day: '', price: '' });
    }
  };

  const handleDoubleClick = (index) => {
    if (clickableIndices.includes(index)) {
      alert(`Opening deep dive view for ${index} constituent stocks...`); // Ready for chart/graph rendering integration
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Portfolio Section */}
      <section className={theme.card}>
        <h3 className={`text-xl mb-4 ${theme.goldText}`}>Manual Portfolio</h3>
        <div className="flex gap-2 mb-4">
          <input type="text" placeholder="Stock" className="bg-gray-800 p-2 rounded w-1/4" value={newStock.symbol} onChange={(e) => setNewStock({ ...newStock, symbol: e.target.value })} />
          <input type="date" className="bg-gray-800 p-2 rounded w-1/4" value={newStock.date} onChange={(e) => setNewStock({ ...newStock, date: e.target.value })} />
          <input type="number" placeholder="Entry Price" className="bg-gray-800 p-2 rounded w-1/4" value={newStock.price} onChange={(e) => setNewStock({ ...newStock, price: e.target.value })} />
          <button onClick={handleAddStock} className={`px-4 rounded ${theme.goldBg}`}>Add</button>
        </div>

        <table className="w-full text-left">
          <thead><tr className="border-b border-gray-700 text-gray-400"><th>Stock</th><th>Entry</th><th>Live</th><th>P&L</th></tr></thead>
          <tbody>
            {portfolio.map((item, i) => {
              const diff = item.currentPrice - item.price;
              const isProfit = diff >= 0;
              return (
                <tr key={i} className="border-b border-gray-800">
                  <td className="py-2">{item.symbol}</td>
                  <td>{item.price}</td>
                  <td>{item.currentPrice.toFixed(2)}</td>
                  <td className={isProfit ? theme.profit : theme.loss}>{diff > 0 ? '+' : ''}{diff.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      {/* Indices Section */}
      <section className={theme.card}>
        <h3 className={`text-xl mb-4 ${theme.goldText}`}>Market Indices</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {indices.map((index) => {
            const isClickable = clickableIndices.includes(index);
            // Mocking live data changes
            const mockChange = (Math.random() * 2 - 1).toFixed(2);
            return (
              <div
                key={index}
                onDoubleClick={() => handleDoubleClick(index)}
                className={`p-4 bg-gray-800 rounded flex flex-col items-center justify-center ${isClickable ? 'cursor-pointer hover:border-yellow-500 border border-transparent select-none' : ''}`}
              >
                <span className="font-semibold text-white">{index}</span>
                <span className={mockChange >= 0 ? theme.profit : theme.loss}>{mockChange > 0 ? '▲' : '▼'} {mockChange}%</span>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
