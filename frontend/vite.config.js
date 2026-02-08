import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3004,
    strictPort: true,  // 禁止自动更换端口，端口被占用时直接报错
    proxy: {
      '/api': {
        target: 'http://localhost:5002',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:5002',
        ws: true
      }
    }
  }
})
