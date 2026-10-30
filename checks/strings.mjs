#!/usr/bin/env node
// Banned strings in app/ and content/copy/ (docs/brief/09-build-plan.md, phase 0). Names match as whole
// words in any case; the other phrases match anywhere, in any case. This file lives outside both folders
// so it never flags itself. Hydrogen's generated API types are excluded: they mention discounts.
import {readdirSync, readFileSync, statSync} from 'node:fs';
import {join, relative} from 'node:path';

const ROOT = new URL('..', import.meta.url).pathname;
const FOLDERS = ['app', 'content/copy'];
const SKIP = /(\.generated\.d\.ts$|\.react-router\/|node_modules\/|\.(avif|webp|jpg|jpeg|png|ico|woff2?)$)/;

// [pattern, label]. Names as whole words; phrases as plain substrings.
const BANNED = [
  [/\blorem\b/i, 'lorem'],
  [/\bipsum\b/i, 'ipsum'],
  [/% ?off\b/i, '% off'],
  [/\bdiscount/i, 'discount'],
  [/#DarkestShade(?!s)/, '#DarkestShade (without the s)'],
  [/\bZara in in\b/i, 'Zara in in'],
  [/\bModel 07\b/i, 'Model 07'],
  [/\bRaf\b/i, 'Raf'],
  [/\bSimons\b/i, 'Simons'],
  [/\bPrada\b/i, 'Prada'],
];

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (SKIP.test(p + (statSync(p).isDirectory() ? '/' : ''))) continue;
    if (statSync(p).isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

const findings = [];
for (const folder of FOLDERS) {
  let files = [];
  try {
    files = walk(join(ROOT, folder));
  } catch {
    continue;
  }
  for (const file of files) {
    const text = readFileSync(file, 'utf8');
    const lines = text.split('\n');
    lines.forEach((line, i) => {
      for (const [re, label] of BANNED) {
        if (re.test(line)) findings.push(`${relative(ROOT, file)}:${i + 1}: "${label}"`);
      }
    });
  }
}

if (findings.length) {
  console.error(`[check:strings] ${findings.length} banned string(s):\n  ${findings.join('\n  ')}`);
  process.exit(1);
}
console.log(`[check:strings] ok: none of ${BANNED.length} banned strings in ${FOLDERS.join(', ')}`);
