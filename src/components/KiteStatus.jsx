import React, { useCallback, useEffect, useState } from 'react';

// Kite Connect status pill (P3). Polls the sidecar's /api/auth/kite/status
// every 30s and renders one of:
//   * "Kite: API offline"      — sidecar unreachable
//   * "Kite: not configured"   — no KITE_API_KEY in .env (grey)
//   * "Connect Kite"           — configured, no session (gold button)
//   * "● Kite: <user>"         — authenticated (green; click to reconnect)
// The button asks the API for the login URL, then opens it in the system
// browser via the Electron shell bridge (window.open fallback in dev).

const API = 'http://127.0.0.1:8787';

export default function KiteStatus() {
  const [status, setStatus] = useState(null);
  const [offline, setOffline] = useState(false);

  const refresh = useCallback(() => {
    fetch(`${API}/api/auth/kite/status`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`HTTP ${res.status}`))))
      .then((data) => {
        setStatus(data);
        setOffline(false);
      })
      .catch(() => setOffline(true));
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 30000);
    return () => clearInterval(timer);
  }, [refresh]);

  const connect = useCallback(() => {
    fetch(`${API}/api/auth/kite/login-url`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`HTTP ${res.status}`))))
      .then(({ url }) => {
        if (window.bazzar && typeof window.bazzar.openExternal === 'function') {
          window.bazzar.openExternal(url);
        } else {
          window.open(url, '_blank', 'noopener'); // dev-browser fallback
        }
        // The session lands in the keyring via the callback; the next poll
        // (30s) picks it up — poll once sooner for snappier UX.
        setTimeout(refresh, 5000);
      })
      .catch((err) => console.error('Kite login-url failed', err));
  }, [refresh]);

  const base = 'ml-auto px-3 py-1 rounded text-xs font-semibold whitespace-nowrap border';

  if (offline) {
    return <span className={`${base} border-gray-700 text-gray-500`}>Kite: API offline</span>;
  }
  if (!status) return null;
  if (!status.api_key_set) {
    return <span className={`${base} border-gray-700 text-gray-500`}>Kite: not configured</span>;
  }
  if (status.authenticated) {
    return (
      <button
        onClick={connect}
        title={`Kite session active (login ${status.login_time || 'unknown'}) — click to reconnect`}
        className={`${base} border-green-600 text-green-400 hover:bg-green-900/30 transition-colors`}
      >
        {'\u25CF'} Kite: {status.user || 'connected'}
      </button>
    );
  }
  return (
    <button
      onClick={connect}
      className={`${base} border-yellow-500 text-yellow-500 hover:bg-yellow-500 hover:text-black transition-colors`}
    >
      Connect Kite
    </button>
  );
}
