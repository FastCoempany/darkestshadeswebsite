import { defineConfig } from 'vitest/config';
import { wallData } from './vite.config';

export default defineConfig({
  plugins: [wallData()],
  test: {
    include: ['tests/unit/**/*.test.ts'],
    environment: 'node',
    reporters: ['default'],
  },
});
