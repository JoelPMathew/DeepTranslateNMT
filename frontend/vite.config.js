import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:6000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
        // Enhanced error handling
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.error('[PROXY ERROR]', err.message);
            res.writeHead(503, {
              'Content-Type': 'application/json',
            });
            res.end(JSON.stringify({
              detail: `Backend connection failed: ${err.message}. Ensure server is running at http://127.0.0.1:6000`,
            }));
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            if (proxyRes.statusCode >= 500) {
              console.error(`[PROXY] 5xx response: ${proxyRes.statusCode}`);
            }
          });
        },
        ws: false,
      },
      '/ws': {
        target: 'ws://127.0.0.1:6000',
        ws: true,
        rewrite: (path) => path.replace(/^\/ws/, '/ws'),
      },
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
})
