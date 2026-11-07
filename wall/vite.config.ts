import { defineConfig, type Plugin } from 'vite';
import { copyFileSync, createReadStream, existsSync, mkdirSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, extname, relative, resolve, sep } from 'node:path';
import { copyFrom, framesFrom } from './src/data/extract';

// The wall, alone: two pages (the wall and the states sheet), relative paths so the built folder works from any host
// (a private Artifact, a folder on a phone, GitHub Pages), `noindex` in the pages themselves. three.js never joins the
// initial bundle: it is split into its own chunk and imported on the first lift (DRAWER-WALL.md, Budgets).

const PRIVATE_FONTS = resolve(__dirname, '../brand/fonts/private');
const LOCAL_FACES: Array<[string, string, number]> = [
  ['OwnersWide-Medium.woff2', 'Owners Wide', 500],
  ['Stolzl-Light.woff2', 'Stolzl', 300],
  ['Stolzl-Book.woff2', 'Stolzl', 350],
  ['Stolzl-Regular.woff2', 'Stolzl', 400],
  ['Stolzl-Medium.woff2', 'Stolzl', 500],
];

/** Route B of brand/fonts/README.md: when the licensed font files sit in brand/fonts/private/ (git-ignored), their
 * @font-face rules go into each page's <head> and the files are served in dev and copied to dist/fonts/ at build,
 * with relative URLs so any host (a private Artifact, a folder, a subpath) finds them. Without the files: nothing. */
function fontsLocal(): Plugin {
  const present = () => (existsSync(PRIVATE_FONTS) ? LOCAL_FACES.filter(([file]) => readdirSync(PRIVATE_FONTS).includes(file)) : []);
  const css = () => present()
    .map(([file, family, weight]) => `@font-face{font-family:'${family}';font-weight:${weight};font-display:swap;src:url('./fonts/${file}') format('woff2')}`)
    .join('\n');
  return {
    name: 'wall-fonts-local',
    transformIndexHtml(html) {
      const rules = css();
      return rules ? html.replace('</head>', `  <style data-fonts="local">${rules}</style>\n</head>`) : html;
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const m = req.url?.match(/^\/fonts\/([A-Za-z0-9-]+\.woff2)$/);
        const face = m && present().find(([file]) => file === m[1]);
        if (!face) return next();
        res.setHeader('content-type', 'font/woff2');
        res.end(readFileSync(resolve(PRIVATE_FONTS, face[0])));
      });
    },
    closeBundle() {
      const faces = present();
      if (!faces.length) return;
      mkdirSync(resolve(__dirname, 'dist/fonts'), { recursive: true });
      for (const [file] of faces) copyFileSync(resolve(PRIVATE_FONTS, file), resolve(__dirname, 'dist/fonts', file));
    },
  };
}

/** `PUBLIC_ADOBE_FONTS_KIT`: an Adobe Fonts web project id adds its stylesheet to each page (route A). */
function fontsKit(): Plugin {
  return {
    name: 'wall-fonts-kit',
    transformIndexHtml(html) {
      const kit = process.env.PUBLIC_ADOBE_FONTS_KIT;
      if (!kit || !/^[a-z0-9]+$/i.test(kit)) return html;
      return html.replace('</head>', `  <link rel="stylesheet" href="https://use.typekit.net/${kit}.css">\n</head>`);
    },
  };
}

/** `virtual:wall-frames` and `virtual:wall-copy`: the eight frames' facts from content/products/ and the copy deck's
 * wall section from content/copy/en.json, extracted at build time so the wall ships only what it shows. */
function wallData(): Plugin {
  const PRODUCTS = resolve(__dirname, '../content/products');
  const DECK = resolve(__dirname, '../content/copy/en.json');
  const ids: Record<string, string> = { 'virtual:wall-frames': '\0wall-frames', 'virtual:wall-copy': '\0wall-copy' };
  return {
    name: 'wall-data',
    resolveId(source) { return ids[source] ?? null; },
    load(id) {
      if (id === '\0wall-frames') {
        const files = readdirSync(PRODUCTS).filter((f) => /^f0[1-9]\.json$/.test(f));
        for (const f of files) this.addWatchFile(resolve(PRODUCTS, f));
        const products = files.map((f) => JSON.parse(readFileSync(resolve(PRODUCTS, f), 'utf8')));
        return `export default ${JSON.stringify(framesFrom(products))};`;
      }
      if (id === '\0wall-copy') {
        this.addWatchFile(DECK);
        return `export default ${JSON.stringify(copyFrom(JSON.parse(readFileSync(DECK, 'utf8'))))};`;
      }
      return null;
    },
  };
}

/** wall/assets/ (the committed renders, GLBs, cameras and the manifest) served at ./assets/ in dev and copied there
 * in the build, as they are, no hashing: the manifest names them. The zoom images in public/zoom/ ride on publicDir. */
function wallAssets(): Plugin {
  const SRC = resolve(__dirname, 'assets');
  const types: Record<string, string> = { '.json': 'application/json', '.avif': 'image/avif', '.webp': 'image/webp', '.glb': 'model/gltf-binary', '.hdr': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg' };
  return {
    name: 'wall-assets',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const m = req.url?.match(/^\/assets\/(wall|seq|glb|stills|env|camera|manifest\.json|lens-tints\.json)([^?]*)/);
        if (!m) return next();
        const rel = decodeURIComponent((m[1] ?? '') + (m[2] ?? ''));
        const file = resolve(SRC, rel);
        if (!file.startsWith(SRC + sep) || !existsSync(file) || !statSync(file).isFile()) return next();
        res.setHeader('content-type', types[extname(file)] ?? 'application/octet-stream');
        res.setHeader('cache-control', 'no-cache');
        createReadStream(file).pipe(res);
      });
    },
    closeBundle() {
      const out = resolve(__dirname, 'dist/assets');
      const copy = (dir: string) => {
        for (const name of readdirSync(dir)) {
          const p = resolve(dir, name);
          if (statSync(p).isDirectory()) copy(p);
          else if (!name.endsWith('.schema.json')) { const dest = resolve(out, relative(SRC, p)); mkdirSync(dirname(dest), { recursive: true }); copyFileSync(p, dest); }
        }
      };
      if (existsSync(SRC)) copy(SRC);
    },
  };
}

export default defineConfig({
  base: './',
  plugins: [fontsLocal(), fontsKit(), wallData(), wallAssets()],
  publicDir: 'public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2022',
    sourcemap: false,
    rollupOptions: {
      input: {
        index: resolve(__dirname, 'index.html'),
        states: resolve(__dirname, 'states.html'),
      },
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/three/')) return 'three';
          return undefined;
        },
      },
    },
  },
  server: { host: '127.0.0.1', port: 5173, strictPort: true, fs: { allow: ['..'] } },   // the tokens live in design/, above wall/
});
