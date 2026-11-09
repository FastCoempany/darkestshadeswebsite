// The banned-strings check (DRAWER-WALL.md, Testing): nothing that ships names Raf Simons, Prada, the film behind #43,
// its maker or FOOH, or shows a price (00-decisions.md #47). Scans wall/src, wall/index.html, wall/states.html, wall/data and the copy deck's `wall` section.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const WALL = resolve(dirname(fileURLToPath(import.meta.url)), '..');
// The names are the check's data, not the wall's: each pattern takes any spacing or punctuation between its parts.
const BANNED = [
  [/raf[\s_.-]*simons|simons[\s_.,-]*raf\b/i, '00-decisions.md #5'],
  [/\bprada\b/i, '08-copy.md, no name-dropping'],
  [/prelude[\s_.-]*to[\s_.-]*forever/i, '00-decisions.md #43, the title'],
  [/adele[\s_.-]*dejak/i, '00-decisions.md #43, the maker'],
  [/\bfooh\b/i, '00-decisions.md #43, the genre word'],
  // the wall shows no price (00-decisions.md #47, the founder's "remove pricing"): no dollar amount in anything that ships. The
  // third-party three.js chunk is the one file left out: its minified code holds a "$1" replacement token, and none of the
  // wall's own strings enter it.
  [/\$\s?\d/, '00-decisions.md #47, no price on the wall', /[\\/]three-[^\\/]*\.js$/],
];

function* walk(dir) {
  if (!existsSync(dir)) return;
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else if (/\.(ts|js|mjs|css|html|json|md|txt|svg|webmanifest)$/.test(name)) yield p;
  }
}

// wall/src, wall/data, the pages, the manifest (its alt and note fields are metadata), wall/public and, when a build
// exists, wall/dist (what ships); plus the copy deck's wall section
const files = [...walk(join(WALL, 'src')), ...walk(join(WALL, 'data')), join(WALL, 'index.html'), join(WALL, 'states.html'),
  join(WALL, 'assets', 'manifest.json'), ...walk(join(WALL, 'public')), ...walk(join(WALL, 'dist'))].filter(existsSync);
const texts = files.map((f) => [f, readFileSync(f, 'utf8')]);
const deck = resolve(WALL, '../content/copy/en.json');
if (existsSync(deck)) {
  const wall = JSON.parse(readFileSync(deck, 'utf8')).wall;
  if (wall) texts.push([deck + '#wall', JSON.stringify(wall)]);
}

let failures = 0;
for (const [file, text] of texts) {
  for (const [re, why, except] of BANNED) {
    if (except && except.test(file)) continue;
    const m = text.match(re);
    if (m) {
      failures++;
      const line = text.slice(0, m.index).split('\n').length;
      console.error(`strings: ${file}:${line} contains "${m[0]}" (${why})`);
    }
  }
}
console.log(`strings: ${texts.length} files scanned, ${failures} banned strings`);
process.exit(failures ? 1 : 0);
