import {fileURLToPath} from 'node:url';
import react from '@vitejs/plugin-react';
import {defineConfig} from 'vitest/config';

/** Unit tests (logic, honesty rules, the mock adapter) run in jsdom without the Hydrogen plugins. */
export default defineConfig({
  plugins: [react()],
  resolve: {alias: {'~': fileURLToPath(new URL('./app', import.meta.url))}},
  define: {
    'import.meta.env.DS_REVIEW_BUILD': JSON.stringify(''),
    'import.meta.env.DS_LOCAL_FONTS': JSON.stringify(''),
  },
  test: {
    environment: 'jsdom',
    include: ['tests/unit/**/*.test.{ts,tsx}', 'app/**/*.test.{ts,tsx}'],
    css: false,
  },
});
