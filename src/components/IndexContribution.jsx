import React, { useState } from 'react';
import { theme } from '../theme.js';
import { chartUrl } from '../api.js';
import SearchInput from './SearchInput.jsx';
import ChartImage from './ChartImage.jsx';

// Index contribution view. Per-constituent weights are outside the current
// local API contract, so this card provides index selection (dictionary
// search) plus the backend-rendered chart for the chosen index. No
// fabricated contribution numbers are displayed.
const IndexContribution = () => {
  const [selection, setSelection] = useState(null);

  return (
    <section className={theme.card}>
      <header className="flex flex-wrap justify-between items-end gap-4 border-b border-gray-800 pb-4 mb-4">
        <div>
          <h3 className={`text-xl font-bold ${theme.goldText}`}>Index Contribution</h3>
          <p className="text-gray-400 text-sm mt-1">
            Select an index to view its backend chart. Constituent-level point
            contributions will appear here once exposed by the data platform.
          </p>
        </div>
      </header>
      <SearchInput
        className="max-w-md mb-4"
        placeholder="Search index (e.g. NIFTY 50)..."
        onSelect={(item) => setSelection(item)}
      />
      {selection ? (
        <>
          <p className="text-sm text-gray-400 mb-2">
            {selection.name} ({selection.symbol}{selection.exchange ? ` · ${selection.exchange}` : ''})
          </p>
          <ChartImage
            src={chartUrl('indices', selection.symbol)}
            alt={`${selection.name || selection.symbol} chart`}
          />
        </>
      ) : (
        <p className="text-gray-500 text-sm">No index selected.</p>
      )}
    </section>
  );
};

export default IndexContribution;
