import React from 'react';
import { theme } from '../theme.js';

export default function InternationalMarkets() {
  const markets = ['Nasdaq', 'Dow Jones', 'Hang Seng', 'GIFT Nifty'];
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
      {markets.map((market) => (
        <div key={market} className={`${theme.card} text-center py-8`}>
          <h3 className={`text-xl font-bold mb-2 ${theme.goldText}`}>{market}</h3>
          <span className={`text-2xl ${theme.loss}`}>▼ 1.24%</span>
        </div>
      ))}
    </div>
  );
}
