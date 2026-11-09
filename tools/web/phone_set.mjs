#!/usr/bin/env node
// The phone set (DRAWER-WALL.md, On a phone; O18): the built wall (wall/dist) as a private Artifact's files, in
// work/phone/. The Artifact host wraps the page in its own document skeleton and serves a fixed list of file types
// (D0's S2 spike: no .glb or .hdr under any type, .wasm yes), and a version holds at most 511 files, so the set is:
//   - index.html stripped of <!doctype>, <html>, <head> and <body>: the metas, the module script and its preloads,
//     the stylesheet inlined (its font URLs pointed at ./assets/), the <drawer-wall> and the <noscript> list;
//   - the assets the wall needs at phone sizes: the 1200 px sequences in WebP only (the 720 px set is for low-density
//     screens, AVIF is a saving, not a need), the plates, dark crops and rects for both layouts, the stills, the GLBs
//     and the environment map renamed to .wasm (fetched as bytes; GLTFLoader and HDRLoader read the bytes, not the
//     name), the cameras, the tints, the manifest rewritten to list only the files that ship, under their shipped names;
//   - the zoom photographs (wall/public/zoom), the favicon and the touch icon.
// Writes work/phone/publish-plan.json: the files in batches of at most 255 for the Artifact tool, with sizes.
// Usage: node tools/web/phone_set.mjs [--width 1200] [--formats webp] [--out work/phone]
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, readdirSync, statSync, rmSync, existsSync } from 'node:fs';
import { resolve, dirname, join, relative, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const args = Object.fromEntries(process.argv.slice(2).map((a, i, all) => (a.startsWith('--') ? [a.slice(2), all[i + 1] ?? ''] : [])).filter((x) => x.length));
const WIDTH = Number(args.width ?? 1200);
const FORMATS = (args.formats ?? 'webp').split(',');
const DIST = resolve(ROOT, 'wall/dist');
const OUT = resolve(ROOT, args.out ?? 'work/phone');
const RENAME = { '.glb': '.glb.wasm', '.hdr': '.hdr.wasm', '.bin': '.bin.wasm' };   // the host's served types (S2)
const BATCH = 255;

if (!existsSync(join(DIST, 'index.html'))) { console.error('phone set: build the wall first (cd wall && npm run build)'); process.exit(1); }
rmSync(OUT, { recursive: true, force: true });
mkdirSync(join(OUT, 'assets'), { recursive: true });

const files = [];   // { published, source, bytes }
const add = (published, source) => { files.push({ published, source, bytes: statSync(source).size }); const dest = join(OUT, published); mkdirSync(dirname(dest), { recursive: true }); copyFileSync(source, dest); };
const shipName = (f) => { const ext = extname(f); return RENAME[ext] ? f.slice(0, -ext.length) + RENAME[ext] : f; };

// 1. the manifest: keep the entries the phone needs, their files filtered to the formats that ship, renamed
const manifest = JSON.parse(readFileSync(join(DIST, 'assets/manifest.json'), 'utf8'));
const kept = [];
for (const e of manifest.assets) {
  if (e.kind === 'sequence-frame' && e.width !== WIDTH) continue;
  let list = e.files;
  if (['sequence-frame', 'still', 'wall-plate', 'wall-dark'].includes(e.kind)) {
    const chosen = list.filter((f) => FORMATS.includes(extname(f).slice(1)));
    if (chosen.length) list = chosen;
  }
  const shipped = list.map(shipName);
  for (let i = 0; i < list.length; i++) add(join('assets', shipped[i]), join(DIST, 'assets', list[i]));
  kept.push({ ...e, files: shipped });
}
const out = { ...manifest, assets: kept, phoneSet: { from: 'wall/dist', width: WIDTH, formats: FORMATS, renamed: RENAME, builtAt: new Date().toISOString().slice(0, 10) } };
writeFileSync(join(OUT, 'assets/manifest.json'), JSON.stringify(out));
files.push({ published: 'assets/manifest.json', source: join(OUT, 'assets/manifest.json'), bytes: statSync(join(OUT, 'assets/manifest.json')).size });

// 2. the page's scripts, styles and fonts (everything in dist/assets that is not a wall asset)
const WALL_DIRS = new Set(['wall', 'seq', 'glb', 'stills', 'env', 'camera']);
let css = '';
for (const name of readdirSync(join(DIST, 'assets'))) {
  const p = join(DIST, 'assets', name);
  if (statSync(p).isDirectory()) continue;
  if (name === 'manifest.json' || name === 'lens-tints.json') continue;
  if (/^states-.*\.js$/.test(name)) continue;   // the states sheet's script: the sheet is the review's, not the phone's
  if (name.endsWith('.css')) { css += readFileSync(p, 'utf8').replace(/url\((['"]?)\.\//g, 'url($1./assets/'); add(join('assets', name), p); continue; }   // inlined below (its font URLs from the page) and carried as a file too
  if (/\.(js|woff2|json)$/.test(name)) add(join('assets', name), p);
  else if (WALL_DIRS.has(name)) continue;
  else add(join('assets', name), p);   // the plates' hashed copies used by the noscript list
}
for (const name of ['favicon.svg', 'apple-touch-icon.png', 'favicon.ico']) if (existsSync(join(DIST, name))) add(name, join(DIST, name));

// 3. the photographs
const ZOOM = join(DIST, 'zoom');
if (existsSync(ZOOM)) for (const name of readdirSync(ZOOM)) add(join('zoom', name), join(ZOOM, name));

// 4. the page: the head's useful lines and the body, no skeleton; the stylesheet inline
const html = readFileSync(join(DIST, 'index.html'), 'utf8');
const head = html.match(/<head>([\s\S]*?)<\/head>/)[1];
const body = html.match(/<body>([\s\S]*?)<\/body>/)[1];
const keep = head.split('\n').map((l) => l.trim()).filter((l) => l && !/^<meta charset|^<meta name="viewport"|<link rel="stylesheet"/.test(l));
const page = [
  ...keep.filter((l) => /^<title/.test(l)),
  '<meta name="claude:viewport-fit-sides" content="cover">',
  ...keep.filter((l) => !/^<title/.test(l)),
  '<style>', css.trim(), '</style>',
  body.trim(),
  '',
].join('\n');
writeFileSync(join(OUT, 'index.html'), page);

// 5. the plan
const total = files.reduce((a, f) => a + f.bytes, 0);
const batches = [];
for (let i = 0; i < files.length; i += BATCH) batches.push(files.slice(i, i + BATCH).map((f) => f.published));
writeFileSync(join(OUT, 'publish-plan.json'), JSON.stringify({ page: 'index.html', root: relative(ROOT, OUT), files: files.map(({ published, bytes }) => ({ published, bytes })), batches, total }, null, 1));
const byExt = {};
for (const f of files) { const e = extname(f.published) || f.published; byExt[e] = (byExt[e] ?? 0) + 1; }
console.log(`phone set: ${files.length} files, ${(total / 1048576).toFixed(1)} MB, in ${batches.length} batches of at most ${BATCH}; ${Object.entries(byExt).map(([k, v]) => `${v} ${k}`).join(', ')}`);
console.log(`phone set: ${kept.length} manifest entries (of ${manifest.assets.length}); the page ${page.length} bytes with ${css.length} bytes of style inline`);
if (files.length > 511) { console.error(`phone set: ${files.length} files is over the Artifact's 511`); process.exit(1); }
