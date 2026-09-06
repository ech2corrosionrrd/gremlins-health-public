import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Backend origin for the dev proxy. Override when the API is not local.
const API_TARGET = process.env.VITE_DEV_API_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,

    // Telegram only opens Mini Apps over HTTPS, so development happens
    // through a tunnel (cloudflared / ngrok). Vite blocks requests whose Host
    // header it does not recognise, which would otherwise show up as a bare
    // "Blocked request. This host is not allowed." page inside Telegram.
    allowedHosts: [
      // Named Cloudflare tunnel for this project.
      '.example.com',
      '.trycloudflare.com',
      '.ngrok-free.app',
      '.ngrok.io',
      '.loca.lt',
    ],

    // Proxy the API through the same origin as the app. One tunnel then
    // covers both, the browser performs no cross-origin request, and
    // VITE_API_URL can stay at its default "/api".
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
})
