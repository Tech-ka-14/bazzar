import React from 'react';
import { theme } from '../theme.js';

export default function Commodities() {
  const categories = {
    'Bullion': ['Gold', 'Silver', 'Platinum', 'Palladium'],
    'Base Metals': ['Copper', 'Aluminium', 'Zinc', 'Lead', 'Nickel', 'Brass'],
    'Ferrous Metals': ['Steel Rebar'],
    'Energy': ['Crude Oil', 'Natural Gas'],
    'Agricultural (Agri)': ['Cotton', 'Kapas', 'Cotton Seed Wash Oil', 'CPO', 'RBD Palmolein', 'Mentha Oil', 'Castor Seed', 'Cardamom', 'Black Pepper'],
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Object.entries(categories).map(([category, items]) => (
        <div key={category} className={theme.card}>
          <h3 className={`text-lg font-bold mb-3 border-b border-gray-700 pb-2 ${theme.goldText}`}>{category}</h3>
          <ul className="space-y-2">
            {items.map((item) => (
              <li key={item} className="flex justify-between text-sm">
                <span className="text-white">{item}</span>
                {/* Mocking change indicators */}
                <span className={Math.random() > 0.5 ? theme.profit : theme.loss}>{(Math.random() * 3).toFixed(2)}%</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
