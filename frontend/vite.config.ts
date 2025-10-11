import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,        // Portul pe care rulează frontend-ul
    open: true,        // Deschide browser-ul automat
    host: true         // Permite accesul de pe alte dispozitive din rețea
  }
})