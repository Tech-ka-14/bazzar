// Bazzar Terminal - Electron preload script.
// Exposes a minimal, context-isolated API to the renderer. The renderer has
// no Node.js access (nodeIntegration: false, contextIsolation: true,
// sandbox: true). Only the narrow IPC surface below is reachable.
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('bazzar', {
  // Returns { name, version, electron, chrome, node, platform, arch, repository }.
  getAppInfo: () => ipcRenderer.invoke('app:get-info'),

  // --- Sidecar API auth (P5) ---
  // Per-launch bearer token generated in the main process; the renderer
  // attaches it as `Authorization: Bearer <token>` on every API request.
  getApiToken: () => ipcRenderer.invoke('get-api-token'),

  // --- Scraper test-bench ---
  // start({ mode: 'sample' | 'url', url? }) -> status snapshot.
  scraperStart: (options) => ipcRenderer.invoke('scraper:start', options),
  scraperPause: () => ipcRenderer.invoke('scraper:pause'),
  scraperResume: () => ipcRenderer.invoke('scraper:resume'),
  scraperCancel: () => ipcRenderer.invoke('scraper:cancel'),
  scraperGetStatus: () => ipcRenderer.invoke('scraper:status'),
  // analyze({ path? }) -> { ok, path, skippedRows, analysis, preview }.
  scraperAnalyze: (options) => ipcRenderer.invoke('scraper:analyze', options),
  // Subscribe to scraper status/progress pushes. Returns an unsubscribe fn.
  onScraperStatus: (callback) => {
    const listener = (_event, snapshot) => callback(snapshot);
    ipcRenderer.on('scraper:status', listener);
    return () => ipcRenderer.removeListener('scraper:status', listener);
  },

  // --- Update notification ---
  // -> { enabled, updateAvailable, currentVersion, latestVersion, message,
  //     url, publishedAt, source, error }
  checkForUpdates: () => ipcRenderer.invoke('update:check'),

  // --- External browser (P3: Kite Connect login) ---
  // Opens an allowlisted https URL (kite.trade domains only) in the system
  // browser; new windows inside the app stay denied.
  openExternal: (url) => ipcRenderer.invoke('shell:open-external', url),
});
