import {fileURLToPath} from 'node:url';
import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

/** Storybook's own Vite config: the app's styles and alias without the Hydrogen, Oxygen and React Router plugins. */
export default defineConfig({
  plugins: [tailwindcss(), react()],
  resolve: {alias: {'~': fileURLToPath(new URL('../app', import.meta.url))}},
  define: {
    'import.meta.env.DS_REVIEW_BUILD': JSON.stringify(''),
    'import.meta.env.DS_LOCAL_FONTS': JSON.stringify(''),
  },
  server: {fs: {allow: [fileURLToPath(new URL('..', import.meta.url))]}},
});
