import React, { useState, useEffect } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react'; // Assuming lucide-react for icons

const IndexContribution = () => {
  const [contributions, setContributions] = useState([]);
  const [indexValue, setIndexValue] = useState(0);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('');

  useEffect(() => {
    // Dynamic 1st-of-the-month check
    const today = new Date();
    if (today.getDate() === 1) {
      // Check local storage to ensure we only prompt once per month
      const monthKey = `${today.getFullYear()}-${today.getMonth()}`;
      if (localStorage.getItem('indexUpdatePrompted') !== monthKey) {
        setShowUpdateModal(true);
        localStorage.setItem('indexUpdatePrompted', monthKey);
      }
    }
    
    fetchContributionData();
  }, []);

  const fetchContributionData = async () => {
    // In production, this fetches from your Python backend which queries DuckDB
    try {
      const response = await fetch('/api/index-contribution?index=NIFTY50');
      const data = await response.json();
      setContributions(data.stocks);
      setIndexValue(data.current_index_value);
      setLastUpdated(data.last_updated);
    } catch (error) {
      console.error("Failed to fetch database data", error);
    }
  };

  const handleOfficialUpdate = async () => {
    setIsUpdating(true);
    try {
      // This triggers fundamental_analyzer.py to fetch new NSE weights and constituent changes
      await fetch('/api/update-index-weights', { method: 'POST' });
      await fetchContributionData();
      setShowUpdateModal(false);
    } catch (error) {
      console.error("Update failed", error);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-6 font-sans">
      
      {/* Monthly Update Modal Popup */}
      {showUpdateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-yellow-500 rounded-lg p-8 max-w-md w-full shadow-2xl">
            <div className="flex items-center space-x-4 mb-6">
              <AlertCircle className="text-yellow-500 w-8 h-8" />
              <h2 className="text-2xl font-bold text-yellow-500">Monthly Index Update</h2>
            </div>
            <p className="text-gray-300 mb-6">
              It is the 1st of the month. Official NSE index constituents and Investable Weight Factors (IWF) may have changed. Update your DuckDB database now to ensure accurate point contributions.
            </p>
            <div className="flex justify-end space-x-4">
              <button 
                onClick={() => setShowUpdateModal(false)}
                className="px-4 py-2 text-white bg-gray-700 hover:bg-gray-600 rounded transition"
              >
                Dismiss
              </button>
              <button 
                onClick={handleOfficialUpdate}
                disabled={isUpdating}
                className="px-4 py-2 bg-yellow-500 text-black font-bold rounded hover:bg-yellow-400 flex items-center transition"
              >
                {isUpdating ? <RefreshCw className="animate-spin mr-2 w-5 h-5" /> : null}
                {isUpdating ? 'Updating...' : 'Update Now'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Dashboard UI */}
      <div className="max-w-6xl mx-auto">
        <header className="flex justify-between items-end border-b border-gray-800 pb-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-yellow-500">NIFTY 50 Point Contribution</h1>
            <p className="text-gray-400 mt-1">Real-time point drag/lift based on Free-Float MCap</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">{indexValue.toFixed(2)}</div>
            <div className="text-sm text-gray-500">Last Synced: {lastUpdated}</div>
          </div>
        </header>

        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-950 border-b border-gray-800">
              <tr>
                <th className="p-4 font-semibold text-yellow-500">Ticker</th>
                <th className="p-4 font-semibold text-yellow-500">Sector</th>
                <th className="p-4 font-semibold text-yellow-500 text-right">Weight (%)</th>
                <th className="p-4 font-semibold text-yellow-500 text-right">Pts Contributed</th>
                <th className="p-4 font-semibold text-yellow-500 text-right">Daily Pt Impact</th>
              </tr>
            </thead>
            <tbody>
              {contributions.map((stock, idx) => (
                <tr key={stock.ticker} className="border-b border-gray-800 hover:bg-gray-800 transition">
                  <td className="p-4 font-bold text-white">{stock.ticker}</td>
                  <td className="p-4 text-gray-400">{stock.sector}</td>
                  <td className="p-4 text-right">{stock.weight.toFixed(2)}%</td>
                  <td className="p-4 text-right font-medium text-white">
                    {(indexValue * (stock.weight / 100)).toFixed(2)}
                  </td>
                  <td className={`p-4 text-right font-bold ${stock.daily_impact >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {stock.daily_impact > 0 ? '+' : ''}{stock.daily_impact.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default IndexContribution;