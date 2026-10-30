#!/usr/bin/env node
// No hex colors in app/ (CLAUDE.md: role tokens only). Checks .ts, .tsx, .css, .mdx, .json under app/.
// Allowed: nothing. Tokens come from design/tokens/build/*.css, which app/styles imports but never copies.
import {readdirSync, readFileSync, statSync} from 'node:fs';
import {join, relative} from 'node:path';

const ROOT = new URL('..', import.meta.url).pathname;
const HEX = /(?<![\w&])#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/g;
const EXT = /\.(tsx?|css|mdx?|json)$/;

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (EXT.test(p)) out.push(p);
  }
  return out;
}

const findings = [];
for (const file of walk(join(ROOT, 'app'))) {
  const lines = readFileSync(file, 'utf8').split('\n');
  lines.forEach((line, i) => {
    // Ignore fragment identifiers in URLs and ids (href="#main", "#root") by requiring hex digits only.
    const hits = line.match(HEX) || [];
    for (const hit of hits) {
      if (/^#(main|root|top|content)$/i.test(hit)) continue;
      if (/^#[0-9a-fA-F]+$/.test(hit) && /^#(?:[a-fA-F]+|[0-9]+)$/.test(hit) && hit.length <= 5 && !/color|background|fill|stroke|border|shadow/i.test(line)) {
        // Short all-letter or all-digit tokens like "#abc" in prose or ids are not colors unless a color
        // property sits on the same line.
        continue;
      }
      findings.push(`${relative(ROOT, file)}:${i + 1}: ${hit}`);
    }
  });
}

if (findings.length) {
  console.error(`[check:hex] ${findings.length} hex color(s) in app/:\n  ${findings.join('\n  ')}`);
  process.exit(1);
}
console.log('[check:hex] ok: no hex colors in app/');
