import React, { useEffect, useState } from 'react';

// Renders a backend matplotlib PNG chart via a plain <img> tag with an
// explicit loading state and an error/empty state (e.g. when the backend
// has no data yet and returns 404/empty).
export default function ChartImage({ src, alt = 'Chart', className = 'w-full rounded bg-gray-950' }) {
  const [status, setStatus] = useState(src ? 'loading' : 'empty');

  useEffect(() => {
    setStatus(src ? 'loading' : 'empty');
  }, [src]);

  if (!src) {
    return (
      <div className="flex items-center justify-center h-48 bg-gray-950 rounded text-gray-500 text-sm">
        No chart selected.
      </div>
    );
  }

  return (
    <div className="relative">
      {status === 'loading' && (
        <div className="flex items-center justify-center h-48 bg-gray-950 rounded text-gray-500 text-sm animate-pulse">
          Loading chart...
        </div>
      )}
      <img
        src={src}
        alt={alt}
        onLoad={() => setStatus('loaded')}
        onError={() => setStatus('error')}
        className={className}
        style={{ display: status === 'loaded' ? 'block' : 'none' }}
      />
      {status === 'error' && (
        <div className="flex items-center justify-center h-48 bg-gray-950 rounded text-gray-500 text-sm">
          Chart unavailable — awaiting data sync.
        </div>
      )}
    </div>
  );
}
