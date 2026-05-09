import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:5000',
      '/scan': 'http://127.0.0.1:5000',
      '/detections': 'http://127.0.0.1:5000',
      '/explanations': 'http://127.0.0.1:5000',
      '/dashboard': 'http://127.0.0.1:5000',
      '/admin': 'http://127.0.0.1:5000',
      '/health': 'http://127.0.0.1:5000',
    },
  },
})
