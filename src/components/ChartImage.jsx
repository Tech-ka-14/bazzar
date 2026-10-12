import React, { useEffect, useState } from 'react';
import { fetchChartObjectUrl } from '../api.js';

// Renders a backend matplotlib PNG chart. The API requires a bearer token
// (P5) and <img> tags cannot send headers, so the chart is fetched as an
// authenticated blob and rendered through a (revoked-on-cleanup) object URL.
// Keeps the explicit loading and error/empty states (e.g. when the backend
// has no data yet and returns 404).
export default function ChartImage({
  src,
  alt = 'Chart',
  className = 'w-full rounded bg-gray-950',
}) {
  const [objectUrl, setObjectUrl] = useState(null);
  const [status, setStatus] = useState(src ? 'loading' : 'empty');

  useEffect(() => {
    if (!src) {
      setObjectUrl(null);
      setStatus('empty');
      return undefined;
    }
    let revoked = false;
    let url = null;
    setStatus('loading');
    fetchChartObjectUrl(src)
      .then((created) => {
        if (revoked) {
          URL.revokeObjectURL(created);
          return;
        }
        url = created;
        setObjectUrl(created);
        setStatus('loaded');
      })
      .catch(() => {
        if (!revoked) setStatus('error');
      });
    return () => {
      revoked = true;
      if (url) URL.revokeObjectURL(url);
    };
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
      {objectUrl && (
        <img
          src={objectUrl}
          alt={alt}
          className={className}
          style={{ display: status === 'loaded' ? 'block' : 'none' }}
        />
      )}
      {status === 'error' && (
        <div className="flex items-center justify-center h-48 bg-gray-950 rounded text-gray-500 text-sm">
          Chart unavailable — awaiting data sync.
        </div>
      )}
    </div>
  );
}
