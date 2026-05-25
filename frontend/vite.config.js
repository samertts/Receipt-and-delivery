import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [vue(), VitePWA({
    registerType: 'autoUpdate',
    manifest: {
      name: 'نظام إدارة معاملات المختبرات',
      short_name: 'معاملات المختبر',
      display: 'standalone',
      background_color: '#ffffff',
      theme_color: '#1f3a5f',
      lang: 'ar-IQ',
      start_url: '/',
      icons: [{ src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' }]
    }
  })]
})
