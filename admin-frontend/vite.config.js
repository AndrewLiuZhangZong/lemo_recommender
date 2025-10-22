import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 19080,
    proxy: {
      '/api': {
        target: 'http://localhost:18081',
        changeOrigin: true
      }
    }
  }
})

