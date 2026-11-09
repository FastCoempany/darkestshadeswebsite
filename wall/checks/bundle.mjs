// The bundle budgets (DRAWER-WALL.md, Budgets), read from the build: the initial JavaScript, every script and
// modulepreload dist/index.html names (in any attribute order; the entry must be among them), gzipped, at most 60 KB,
// with none of it three.js and none of it naming the three.js chunk even in a preload map (the view's own chunks, which
// the entry imports on the first open, may be named); the 3D chunk (three.js, lifted-three and lifted-frame together) at most 200 KB
// gzipped, three.js imported statically by lifted-three alone and named by neither page. Prints the sizes; fails on any
// budget. The runtime side (what the browser requests before the first open) is perf.spec.ts's. Needs the build.
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
const attr = (tag, name) => tag.match(new RegExp(`\\s${name}="([^"]*)"`))?.[1] ?? null;
const named = (html) => {
  const out = [];
  for (const [tag] of html.matchAll(/<(?:script|link)\b[^>]*>/g)) {
    const src = tag.startsWith('<script') ? attr(tag, 'src') : attr(tag, 'rel') === 'modulepreload' ? attr(tag, 'href') : null;
    if (src && /\.js$/.test(src)) out.push(src.replace(/^\.\//, ''));
  }
  return out;
};
const initial = [...new Set(named(index))];
if (!initial.length) fails.push('index.html names no script: the page would run nothing');
if (!initial.some((f) => /^assets\/index-/.test(f))) fails.push(`the entry chunk (assets/index-*.js) is not among index.html's scripts: ${initial.join(', ') || 'none'}`);
let initialBytes = 0;
const parts = [];
const lateChunks = readdirSync(resolve(DIST, 'assets')).filter((f) => /^three-.*\.js$/.test(f));
for (const rel of initial) {
  const file = resolve(DIST, rel);
  if (!existsSync(file)) { fails.push(`${rel} named by index.html is not in dist`); continue; }
  const size = gz(file);
  initialBytes += size;
  parts.push(`${rel.replace('assets/', '')} ${kb(size)} kB`);
  if (/\/three-/.test(rel)) fails.push(`three.js (${rel}) is in the initial bundle`);
  // the entry's preload map names the view's chunks (drawer-view, photo-zoom, lifted-frame), which it imports on the first
  // open: that is the design. It must not name the three.js chunk itself: that would mean a dynamic import reachable from
  // the entry pulls three.js directly. What the browser requests before the first open is perf.spec.ts's measure.
  const text = readFileSync(file, 'utf8');
  for (const late of lateChunks) if (/^three-/.test(late) && text.includes(late)) fails.push(`${rel} names ${late}: three.js is reachable from the entry`);
}
console.log(`bundle: initial JavaScript ${kb(initialBytes)} kB gzipped in ${initial.length} files (${parts.join(', ')})`);
if (initialBytes > INITIAL_KB * 1024) fails.push(`initial JavaScript ${kb(initialBytes)} kB gzipped > ${INITIAL_KB} kB`);
// an inline module in the page must not import the live frame's chunks either
for (const [, body] of index.matchAll(/<script[^>]*type="module"[^>]*>([\s\S]*?)<\/script>/g)) if (/three-|lifted-/.test(body)) fails.push('an inline module in index.html names a three.js or lifted chunk');

const threeFiles = readdirSync(resolve(DIST, 'assets')).filter((f) => /^three-.*\.js$/.test(f));
if (threeFiles.length !== 1) fails.push(`${threeFiles.length} three.js chunks in dist/assets (expected one)`);
for (const f of threeFiles) {
  const size = gz(resolve(DIST, 'assets', f));
  const liftFiles = readdirSync(resolve(DIST, 'assets')).filter((x) => /^(lifted-three|lifted-frame)-.*\.js$/.test(x));
  const liftBytes = liftFiles.reduce((a, x) => a + gz(resolve(DIST, 'assets', x)), 0);
  console.log(`bundle: 3D chunk ${f} ${kb(size)} kB gzipped (zlib; Vite's own estimate differs by a few kB), with ${liftFiles.join(' + ')} ${kb(liftBytes)} kB: ${kb(size + liftBytes)} kB for the live frame`);
  if (size + liftBytes > THREE_KB * 1024) fails.push(`the live frame's code ${kb(size + liftBytes)} kB gzipped > ${THREE_KB} kB`);
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
