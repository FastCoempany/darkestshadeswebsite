// The bundle budgets (DRAWER-WALL.md, Budgets), read from the build: the initial JavaScript, every script and
// modulepreload dist/index.html names, gzipped, at most 60 KB and none of it three.js; the 3D chunk at most 200 KB
// gzipped and named by neither page (it is reached only through lifted-frame's dynamic import at a tier-2 lift).
// Prints the sizes; fails on any budget. Needs the build (npm run build).
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const WALL = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DIST = resolve(WALL, 'dist');
const INITIAL_KB = 60, THREE_KB = 200;

if (!existsSync(resolve(DIST, 'index.html'))) { console.error('bundle: build the wall first (npm run build)'); process.exit(1); }
const gz = (file) => gzipSync(readFileSync(file)).length;
const kb = (n) => (n / 1024).toFixed(2);
const fails = [];

const index = readFileSync(resolve(DIST, 'index.html'), 'utf8');
const states = readFileSync(resolve(DIST, 'states.html'), 'utf8');
const named = (html) => [...html.matchAll(/<(?:script[^>]+src|link[^>]+rel="modulepreload"[^>]+href)="\.\/(assets\/[^"]+\.js)"/g)].map((m) => m[1]);
const initial = [...new Set(named(index))];
let initialBytes = 0;
const parts = [];
for (const rel of initial) {
  const file = resolve(DIST, rel);
  if (!existsSync(file)) { fails.push(`${rel} named by index.html is not in dist`); continue; }
  const size = gz(file);
  initialBytes += size;
  parts.push(`${rel.replace('assets/', '')} ${kb(size)} kB`);
  if (/\/three-/.test(rel)) fails.push(`three.js (${rel}) is in the initial bundle`);
}
console.log(`bundle: initial JavaScript ${kb(initialBytes)} kB gzipped in ${initial.length} files (${parts.join(', ')})`);
if (initialBytes > INITIAL_KB * 1024) fails.push(`initial JavaScript ${kb(initialBytes)} kB gzipped > ${INITIAL_KB} kB`);

const threeFiles = readdirSync(resolve(DIST, 'assets')).filter((f) => /^three-.*\.js$/.test(f));
if (threeFiles.length !== 1) fails.push(`${threeFiles.length} three.js chunks in dist/assets (expected one)`);
for (const f of threeFiles) {
  const size = gz(resolve(DIST, 'assets', f));
  console.log(`bundle: 3D chunk ${f} ${kb(size)} kB gzipped`);
  if (size > THREE_KB * 1024) fails.push(`3D chunk ${f} ${kb(size)} kB gzipped > ${THREE_KB} kB`);
  for (const [name, html] of [['index.html', index], ['states.html', states]]) if (html.includes(f)) fails.push(`${name} names the three.js chunk ${f}`);
  // only lifted-three's chunk imports it statically (`from "./three-….js"`); the chunks that import lifted-three dynamically
  // carry its name in their preload map (__vite__mapDeps), which loads it only when that import runs
  const staticImport = new RegExp(`(?:from|import)\\s*"\\./${f.replace(/[.]/g, '\\.')}"`);
  const chunks = readdirSync(resolve(DIST, 'assets')).filter((x) => x.endsWith('.js') && x !== f);
  const importers = chunks.filter((x) => staticImport.test(readFileSync(resolve(DIST, 'assets', x), 'utf8')));
  const preloaders = chunks.filter((x) => !importers.includes(x) && readFileSync(resolve(DIST, 'assets', x), 'utf8').includes(f));
  console.log(`bundle: ${f} is imported by ${importers.join(', ') || 'nothing'}; in the preload map of ${preloaders.join(', ') || 'nothing'}`);
  if (importers.length !== 1 || !importers.every((x) => /^lifted-three-/.test(x))) fails.push(`the three.js chunk is imported by ${importers.join(', ') || 'nothing'} (lifted-three alone may)`);
}
for (const f of fails) console.error(`bundle: ${f}`);
process.exit(fails.length ? 1 : 0);
