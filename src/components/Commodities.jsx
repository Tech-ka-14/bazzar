import React, { useEffect, useState } from 'react';
import { theme } from '../theme.js';
import { apiGet } from '../api.js';

// Display name -> tradable symbol used by the data platform.
const SYMBOL_MAP = {
  'Gold': 'GOLD',
  'Silver': 'SILVER',
  'Crude Oil': 'CRUDEOIL',
  'Natural Gas': 'NATURALGAS',
  'Copper': 'COPPER',
  'Aluminium': 'ALUMINIUM',
  'Zinc': 'ZINC',
  'Lead': 'LEAD',
  'Nickel': 'NICKEL',
};

const CATEGORIES = {
  'Bullion': ['Gold', 'Silver', 'Platinum', 'Palladium'],
  'Base Metals': ['Copper', 'Aluminium', 'Zinc', 'Lead', 'Nickel', 'Brass'],
  'Ferrous Metals': ['Steel Rebar'],
  'Energy': ['Crude Oil', 'Natural Gas'],
  'Agricultural (Agri)': ['Cotton', 'Kapas', 'Cotton Seed Wash Oil', 'CPO', 'RBD Palmolein', 'Mentha Oil', 'Castor Seed', 'Cardamom', 'Black Pepper'],
};

export default function Commodities() {
  const [quotes, setQuotes] = useState({});

  useEffect(() => {
    let cancelled = false;
    const symbols = [...new Set(Object.values(SYMBOL_MAP))].join(',');
    apiGet(`/api/quotes?symbols=${encodeURIComponent(symbols)}`)
      .then((data) => {
        if (!cancelled) setQuotes((data && data.symbols) || {});
      })
      .catch((err) => console.error('Failed to load commodity quotes', err));
    return () => {
      cancelled = true;
    };
  }, []);

  const renderQuote = (name) => {
    const symbol = SYMBOL_MAP[name];
    const quote = symbol ? quotes[symbol] : null;
    if (!quote || typeof quote.value !== 'number') {
      return <span className="text-gray-500">—</span>;
    }
    const pct = typeof quote.changePct === 'number' ? quote.changePct : null;
    const up = (pct ?? 0) >= 0;
    return (
      <span className="flex items-center gap-2">
        <span className="text-white">{quote.value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
        {pct !== null && (
          <span className={up ? theme.profit : theme.loss}>
            {up ? '▲' : '▼'} {pct > 0 ? '+' : ''}{pct.toFixed(2)}%
          </span>
        )}
      </span>
    );
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Object.entries(CATEGORIES).map(([category, items]) => (
        <div key={category} className={theme.card}>
          <h3 className={`text-lg font-bold mb-3 border-b border-gray-700 pb-2 ${theme.goldText}`}>{category}</h3>
          <ul className="space-y-2">
            {items.map((item) => (
              <li key={item} className="flex justify-between text-sm">
                <span className="text-white">{item}</span>
                {renderQuote(item)}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
