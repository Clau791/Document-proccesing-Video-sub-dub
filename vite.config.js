/// for github pages

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/Document-proccesing-Video-sub-dub/', // ← numele repo-ului (exact)
})
