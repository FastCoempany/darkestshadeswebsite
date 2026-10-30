#!/usr/bin/env node
// app/components/base/ must not import from app/components/house/ (CLAUDE.md, docs/brief/05-components.md).
import {readdirSync, readFileSync, statSync} from 'node:fs';
import {join, relative} from 'node:path';

const ROOT = new URL('..', import.meta.url).pathname;
const BASE = join(ROOT, 'app/components/base');

function walk(dir, out = []) {
  let names = [];
  try {
    names = readdirSync(dir);
  } catch {
    return out;
  }
  for (const name of names) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (/\.(tsx?|mdx?)$/.test(p)) out.push(p);
  }
  return out;
}

const findings = [];
for (const file of walk(BASE)) {
  readFileSync(file, 'utf8').split('\n').forEach((line, i) => {
    if (/from\s+['"][^'"]*(components\/house|\.\.\/house)/.test(line) || /import\(['"][^'"]*components\/house/.test(line)) {
      findings.push(`${relative(ROOT, file)}:${i + 1}: ${line.trim()}`);
    }
  });
}
// Fixture numbers (states today's data lacks) live in stories and tests only, never in a route or a
// page component (docs/build/RUN.md, phase 1).
for (const file of [...walk(join(ROOT, 'app/routes')), ...walk(join(ROOT, 'app/components'))]) {
  if (file.includes('/stories/') || /\.stories\.tsx?$/.test(file)) continue;
  readFileSync(file, 'utf8').split('\n').forEach((line, i) => {
    if (/from\s+['"][^'"]*mock\/fixtures['"]/.test(line)) findings.push(`${relative(ROOT, file)}:${i + 1}: imports mock/fixtures`);
  });
}
if (findings.length) {
  console.error(`[check:layers] layer rule broken:\n  ${findings.join('\n  ')}`);
  process.exit(1);
}
console.log('[check:layers] ok: base imports nothing from house; no route or page component imports mock/fixtures');
