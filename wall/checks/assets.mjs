// The asset check (DRAWER-WALL.md, Budgets): every manifest entry has its file, every file under wall/assets has its
// manifest entry, every AVIF and WebP has the size its entry says (read from the file's own header), and no asset is
// over its budget. Fails on any of the four.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, resolve, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const WALL = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ASSETS = join(WALL, 'assets');
const MANIFEST = join(ASSETS, 'manifest.json');
const KB = 1024, MB = 1024 * 1024;

// Budgets by kind (bytes), per file, AVIF and WebP alike. From DRAWER-WALL.md's Budgets table: the wall plate
// (160 KB at 1170 px, 380 KB at 2880 px), a sequence frame (45 KB at 720 px, 80 KB at 1200 px), a GLB (6 MB hard),
// the environment map (600 KB). The run's own, where the table has none (WALL-PROGRESS.md, decision log): a dark
// crop 60 KB, a lifted still 200 KB, a JSON asset 20 KB.
const BUDGET = {
  'wall-plate': (e) => (e.width >= 2000 ? 380 * KB : 160 * KB),
  'wall-dark': () => 60 * KB,
  'sequence-frame': (e) => (e.width >= 1000 ? 80 * KB : 45 * KB),
  'glb': () => 6 * MB,
  'still': () => 200 * KB,
  'env': () => 600 * KB,
  'camera': () => 20 * KB,
  'rects': () => 20 * KB,
  'tints': () => 20 * KB,
};

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else yield p;
  }
}

// An AVIF's or WebP's pixel size from its header (no decoder here): AVIF from its ispe boxes (the largest is the
// primary image's; an alpha plane carries the same size), WebP from the VP8, VP8L or VP8X header.
function imageSize(p) {
  const b = readFileSync(p);
  if (b.length > 30 && b.toString('latin1', 0, 4) === 'RIFF' && b.toString('latin1', 8, 12) === 'WEBP') {
    const chunk = b.toString('latin1', 12, 16);
    if (chunk === 'VP8 ') return { w: b.readUInt16LE(26) & 0x3fff, h: b.readUInt16LE(28) & 0x3fff };
    if (chunk === 'VP8L') { const x = b.readUInt32LE(21); return { w: (x & 0x3fff) + 1, h: ((x >>> 14) & 0x3fff) + 1 }; }
    if (chunk === 'VP8X') return { w: b.readUIntLE(24, 3) + 1, h: b.readUIntLE(27, 3) + 1 };
    return null;
  }
  let best = null;
  for (let i = b.indexOf('ispe'); i !== -1 && i + 16 <= b.length; i = b.indexOf('ispe', i + 4)) {
    const w = b.readUInt32BE(i + 8), h = b.readUInt32BE(i + 12);
    if (!best || w * h > best.w * best.h) best = { w, h };
  }
  return best;
}

if (!existsSync(MANIFEST)) { console.error('assets: no manifest at wall/assets/manifest.json'); process.exit(1); }
const manifest = JSON.parse(readFileSync(MANIFEST, 'utf8'));
const entries = manifest.assets ?? [];
const listed = new Set();
let failures = 0;
for (const e of entries) {
  for (const file of e.files ?? []) {
    listed.add(file);
    const p = join(ASSETS, file);
    if (!existsSync(p)) { console.error(`assets: ${file} is in the manifest but not on disk`); failures++; continue; }
    const budgetOf = BUDGET[e.kind];
    if (!budgetOf) { console.error(`assets: ${file} has an unknown kind "${e.kind}"`); failures++; continue; }
    // the file's own dimensions against the entry's, so the budget is sized by the width the file really has
    if (/\.(avif|webp)$/.test(file)) {
      const dim = imageSize(p);
      if (!dim) { console.error(`assets: ${file}: its dimensions could not be read from its header`); failures++; continue; }
      if (dim.w !== e.width || dim.h !== e.height) { console.error(`assets: ${file} is ${dim.w}x${dim.h}, the manifest says ${e.width}x${e.height}`); failures++; continue; }
    }
    const budget = budgetOf(e);
    const size = statSync(p).size;
    if (size > budget) { console.error(`assets: ${file} is ${(size / KB).toFixed(0)} KB, over its ${(budget / KB).toFixed(0)} KB budget`); failures++; }
  }
}
const onDisk = [...walk(ASSETS)].map((p) => relative(ASSETS, p)).filter((f) => !/^manifest(\.schema)?\.json$/.test(f) && !f.endsWith('.gitkeep'));
for (const f of onDisk) if (!listed.has(f)) { console.error(`assets: ${f} is on disk but not in the manifest`); failures++; }
console.log(`assets: ${entries.length} entries, ${listed.size} files listed, ${onDisk.length} files on disk, ${failures} failures`);
process.exit(failures ? 1 : 0);
