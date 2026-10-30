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
if (findings.length) {
  console.error(`[check:layers] base imports house:\n  ${findings.join('\n  ')}`);
  process.exit(1);
}
console.log('[check:layers] ok: app/components/base imports nothing from app/components/house');
