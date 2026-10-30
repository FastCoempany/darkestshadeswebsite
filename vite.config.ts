import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {defineConfig, type Plugin} from 'vite';
import {hydrogen} from '@shopify/hydrogen/vite';
import {oxygen} from '@shopify/mini-oxygen/vite';
import {reactRouter} from '@react-router/dev/vite';
import tailwindcss from '@tailwindcss/vite';
import {blockingSections} from './checks/lib/copy-status.mjs';

const root = fileURLToPath(new URL('.', import.meta.url));
const reviewBuild = process.env.DS_REVIEW_BUILD === '1';
const localFonts = fs.existsSync(path.join(root, 'brand/fonts/private/OwnersWide-Medium.woff2'));

/**
 * Static folders served as they are, in dev and from the client build:
 *   /photography/*  <- assets/photography/   the image library (MANIFEST.csv registers it)
 *   /entry/*        <- assets/entry/         the entry's graded stills (phase 3)
 *   /fonts/*        <- brand/fonts/private/  licensed font files, when present (never committed)
 */
function dsStaticAssets(): Plugin {
  const mounts: [string, string][] = [
    ['/photography/', 'assets/photography'],
    ['/entry/', 'assets/entry'],
    ['/fonts/', 'brand/fonts/private'],
  ];
  const types: Record<string, string> = {
    '.avif': 'image/avif',
    '.webp': 'image/webp',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.json': 'application/json',
    '.csv': 'text/csv',
    '.woff2': 'font/woff2',
    '.woff': 'font/woff',
  };
  let isSsrBuild = false;
  const serve = (server: {middlewares: {use: (fn: (req: any, res: any, next: () => void) => void) => void}}) => {
    server.middlewares.use((req, res, next) => {
      const url = (req.url ?? '').split('?')[0];
      for (const [mount, dir] of mounts) {
        if (url.startsWith(mount)) {
          const rel = decodeURIComponent(url.slice(mount.length));
          const file = path.join(root, dir, rel);
          if (!file.startsWith(path.join(root, dir)) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) break;
          res.setHeader('Content-Type', types[path.extname(file)] ?? 'application/octet-stream');
          res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
          fs.createReadStream(file).pipe(res);
          return;
        }
      }
      next();
    });
  };
  return {
    name: 'ds-static-assets',
    configResolved(config) {
      isSsrBuild = Boolean(config.build.ssr);
    },
    configureServer: serve,
    configurePreviewServer: serve,
    writeBundle(options) {
      if (isSsrBuild || !options.dir) return;
      for (const [mount, dir] of mounts) {
        const src = path.join(root, dir);
        if (!fs.existsSync(src)) continue;
        const dest = path.join(options.dir, mount.replace(/\//g, ''));
        fs.cpSync(src, dest, {recursive: true, filter: (p) => !p.endsWith('MANIFEST.csv') && !p.endsWith('.md')});
      }
    },
  };
}

/**
 * The draft-copy gate (docs/brief/09-build-plan.md): a production build refuses while any section of
 * content/copy/en.json is draft or placeholder. The review build (DS_REVIEW_BUILD=1) carries production
 * settings and allows drafts; Lighthouse and the review screenshots run on it.
 */
function draftCopyGate(): Plugin {
  return {
    name: 'ds-draft-copy-gate',
    // Rollup's first hook: before any plugin's buildStart, so the refusal is the one error the build
    // prints (typegen only resolves the config and never gets here).
    options() {
      // Only a real build: the dev server, `react-router typegen` and the CLI's own config resolution
      // also create environments and run this hook, with mode 'dev'.
      if (this.environment?.mode !== 'build') return;
      if (process.argv.some((a) => a.includes('typegen'))) return;
      const copy = JSON.parse(fs.readFileSync(path.join(root, 'content/copy/en.json'), 'utf8')) as Record<string, unknown>;
      const blocking = blockingSections(copy);
      if (!blocking.length) return;
      if (reviewBuild) {
        console.warn(`[copy-gate] review build: ${blocking.length} copy section(s) still draft or placeholder (${blocking.join(', ')})`);
        return;
      }
      const message =
        `[copy-gate] production build refused: ${blocking.length} section(s) of content/copy/en.json are not approved ` +
        `(${blocking.join(', ')}). The founder signs them off, or run the review build: npm run build:review.`;
      console.error(message);
      throw new Error(message);
    },
  };
}

export default defineConfig({
  plugins: [dsStaticAssets(), draftCopyGate(), tailwindcss(), hydrogen(), oxygen(), reactRouter()],
  envPrefix: ['VITE_', 'PUBLIC_', 'DS_'],
  define: {
    'import.meta.env.DS_REVIEW_BUILD': JSON.stringify(reviewBuild ? '1' : ''),
    'import.meta.env.DS_LOCAL_FONTS': JSON.stringify(localFonts ? '1' : ''),
  },
  resolve: {
    alias: {
      '~': fileURLToPath(new URL('./app', import.meta.url)),
    },
    tsconfigPaths: true,
  },
  build: {
    // Allow a strict Content-Security-Policy without inlining assets as base64:
    assetsInlineLimit: 0,
  },
  ssr: {
    optimizeDeps: {
      include: ['react-router > set-cookie-parser', 'react-router > cookie', 'react-router'],
    },
  },
  server: {
    allowedHosts: ['.tryhydrogen.dev'],
    fs: {allow: [root]},
    watch: {
      // The masters (dam/, 0.8 GB), the film project and the study material never enter the bundle or the watcher.
      ignored: ['**/dam/**', '**/work/**', '**/takes/**', '**/reference/**', '**/.claude/**', '**/storybook-static/**', '**/test-results/**', '**/playwright-report/**', '**/docs/**'],
    },
  },
});
