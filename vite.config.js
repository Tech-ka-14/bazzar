import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base: './' is required so the production build loads correctly
// from the file:// protocol inside Electron.
export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    strictPort: true,
  },
});
