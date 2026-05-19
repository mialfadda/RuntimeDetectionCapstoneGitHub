import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: {
      '/auth':         { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/scan':         { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/detections':   { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/explanations': { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/dashboard':    { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/admin':        { target: 'http://127.0.0.1:5000', changeOrigin: true },
      '/health':       { target: 'http://127.0.0.1:5000', changeOrigin: true },
    },
  },
})
