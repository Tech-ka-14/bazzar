import React, { useState } from 'react';

// Global Theme Classes
const theme = {
  bg: "bg-black text-white min-h-screen font-sans",
  goldText: "text-yellow-500",
  goldBg: "bg-yellow-500 text-black hover:bg-yellow-400 transition-colors",
  redAccent: "text-red-500 border-red-500",
  whiteAccent: "text-white border-white",
  card: "bg-gray-900 border border-gray-800 p-4 rounded-lg shadow-lg",
  profit: "text-green-500 font-bold",
  loss: "text-red-500 font-bold",
};

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activePage, setActivePage] = useState('Home');

  if (!isAuthenticated) return <Login onLogin={() => setIsAuthenticated(true)} />;

  return (
    <div className={theme.bg}>
      <Topbar activePage={activePage} setActivePage={setActivePage} />
      <main className="p-6">
        {activePage === 'Home' && <Home />}
        {activePage === 'Equity' && <Equity />}
        {activePage === 'Commodities' && <Commodities />}
        {activePage === 'Currency' && <Currency />}
        {activePage === 'Market Analysis' && <MarketAnalysis />}
        {activePage === 'International Markets' && <InternationalMarkets />}
      </main>
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
  const pages = ['Home', 'Equity', 'Commodities', 'Currency', 'Market Analysis', 'International Markets'];
  return (
    <nav className="bg-gray-900 border-b-2 border-yellow-500 p-4 flex gap-6 overflow-x-auto">
      {pages.map(page => (
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