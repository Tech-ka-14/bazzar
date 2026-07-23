import React, { useEffect, useRef, useState } from 'react';
import { apiGet } from '../api.js';

// Reusable stock/index search input implementing the dictionary-method UX:
// as the user types, symbol/name suggestions are fetched (debounced 250ms)
// from GET /api/search and shown in a dropdown with full keyboard navigation
// (ArrowUp/ArrowDown/Enter/Escape). Selecting a suggestion calls onSelect(item)
// with { symbol, name, exchange }.
export default function SearchInput({ onSelect, placeholder = 'Search stocks or indices...', className = '', limit = 10 }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const containerRef = useRef(null);
  const debounceRef = useRef(null);
  const requestRef = useRef(0);

  // Debounced dictionary-method lookup against the backend search endpoint.
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const q = query.trim();
    if (!q) {
      setResults([]);
      setIsOpen(false);
      setIsLoading(false);
      return undefined;
    }
    setIsLoading(true);
    debounceRef.current = setTimeout(async () => {
      const requestId = ++requestRef.current;
      try {
        const data = await apiGet(`/api/search?q=${encodeURIComponent(q)}&limit=${limit}`);
        if (requestId !== requestRef.current) return; // stale response
        const items = Array.isArray(data) ? data : [];
        setResults(items);
        setIsOpen(true);
        setHighlight(items.length > 0 ? 0 : -1);
      } catch (err) {
        if (requestId !== requestRef.current) return;
        console.error('Search failed', err);
        setResults([]);
        setIsOpen(true);
        setHighlight(-1);
      } finally {
        if (requestId === requestRef.current) setIsLoading(false);
      }
    }, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, limit]);

  // Close the dropdown when clicking outside the component.
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const pick = (item) => {
    if (!item) return;
    setQuery(item.symbol);
    setIsOpen(false);
    setHighlight(-1);
    if (typeof onSelect === 'function') onSelect(item);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Escape') {
      setIsOpen(false);
      setHighlight(-1);
      return;
    }
    if (!isOpen || results.length === 0) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setHighlight((prev) => (prev + 1) % results.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlight((prev) => (prev <= 0 ? results.length - 1 : prev - 1));
    } else if (event.key === 'Enter') {
      event.preventDefault();
      pick(results[highlight >= 0 ? highlight : 0]);
    }
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <input
        type="text"
        value={query}
        placeholder={placeholder}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => { if (results.length > 0) setIsOpen(true); }}
        onKeyDown={handleKeyDown}
        className="w-full bg-gray-800 text-white p-2 rounded border border-gray-700 focus:border-yellow-500 outline-none"
      />
      {isOpen && (
        <ul className="absolute z-30 left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded shadow-lg max-h-64 overflow-y-auto">
          {isLoading && (
            <li className="px-3 py-2 text-sm text-gray-500">Searching...</li>
          )}
          {!isLoading && results.length === 0 && (
            <li className="px-3 py-2 text-sm text-gray-500">No matches found</li>
          )}
          {results.map((item, i) => (
            <li
              key={`${item.symbol}-${item.exchange || ''}`}
              onMouseDown={(e) => { e.preventDefault(); pick(item); }}
              onMouseEnter={() => setHighlight(i)}
              className={`px-3 py-2 cursor-pointer flex items-center justify-between gap-2 ${i === highlight ? 'bg-gray-800 border-l-2 border-yellow-500' : 'border-l-2 border-transparent'}`}
            >
              <span className="font-bold text-yellow-500">{item.symbol}</span>
              <span className="flex-1 text-sm text-gray-300 truncate">{item.name}</span>
              <span className="text-xs text-gray-500">{item.exchange}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
