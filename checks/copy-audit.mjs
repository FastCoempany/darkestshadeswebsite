#!/usr/bin/env node
// The copy audit against docs/brief/08-copy.md: every string in content/copy/en.json.
//   - no exclamation marks; no hype words; no gendered address; no name-dropping;
//   - sentence case (a sentence starts with a capital, no Title Case runs) except keys that are names or labels;
//   - the fixed names: @darkestshades, darkestshades.com, #DarkestShades (with the s), never "Zara in in";
//   - the price is written "$100"; the tagline is exact; no "ultra-dark" per frame; no lorem ipsum.
// A string the founder has a logged question about is noted, not failed (NOTED below, with the reason).
// Sections without a status are the draft-copy gate's business (checks/copy-gate.mjs), listed here as a note.
import {readFileSync} from 'node:fs';
import {join} from 'node:path';

const ROOT = new URL('..', import.meta.url).pathname;
const copy = JSON.parse(readFileSync(join(ROOT, 'content/copy/en.json'), 'utf8'));

const HYPE = ['must-have', 'obsessed', 'run, don’t walk', "run, don't walk", 'tag your bestie', 'you need these', 'fire', 'iconic', 'game-changer', 'elevate', 'unleash', 'limited time', 'hurry', 'don’t miss', "don't miss", 'last chance', 'exclusive deal'];
const GENDERED = ['bro', 'babe', 'girlboss', 'dude', 'guys', 'ladies'];
const NAMES = ['prada', 'simons', 'runway', 'celebrity', 'as seen at'];

/** Strings with a logged question in docs/build/PROGRESS.md: reported, never failed, until the founder answers. */
const NOTED = {
  'alt.scenes.S01': 'the S01 set is a bare runway (07-photography.md); no picture uses it yet; logged as a question',
};

const findings = [];
const notes = [];
function walk(node, path) {
  if (typeof node === 'string') return check(node, path);
  if (Array.isArray(node)) return node.forEach((v, i) => walk(v, `${path}[${i}]`));
  if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) {
      if (k.startsWith('$') || k === 'status') continue;
      walk(v, path ? `${path}.${k}` : k);
    }
  }
}
function check(text, path) {
  const lower = text.toLowerCase();
  const out = NOTED[path] ? notes : findings;
  const push = (f) => out.push(NOTED[path] ? `${f} (noted: ${NOTED[path]})` : f);
  if (text.includes('!')) push(`${path}: exclamation mark`);
  for (const w of HYPE) if (new RegExp(`\\b${w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i').test(text)) push(`${path}: hype ("${w}")`);
  for (const w of GENDERED) if (new RegExp(`\\b${w}\\b`, 'i').test(text)) push(`${path}: gendered address ("${w}")`);
  for (const w of NAMES) if (lower.includes(w)) push(`${path}: name-dropping ("${w}")`);
  if (/#DarkestShade(?!s)/.test(text)) push(`${path}: #DarkestShade without the s`);
  if (/Zara in in/.test(text)) push(`${path}: "Zara in in"`);
  if (/lorem|ipsum/i.test(text)) push(`${path}: lorem ipsum`);
  if (/\$\s?100(?:\.00)?\b/.test(text) && !/\$100\b/.test(text)) push(`${path}: the price is written "$100"`);
  if (/ultra-dark/i.test(text)) push(`${path}: "ultra-dark" is a brand line, never a per-frame spec`);
  // Sentence case: a Title Case run of three or more capitalised words inside a sentence.
  if (!/^[A-Z0-9 .·:,'’-]+$/.test(text) && /\b([A-Z][a-z]+ ){2,}[A-Z][a-z]+\b/.test(text.replace(/Darkest Shades|God Cloud Device|Privacy Policy|SMS Terms|Date to be announced|HELP|STOP|START|UVA|UVB|UV400|TAC|E\.164/g, ''))) push(`${path}: Title Case run ("${text.slice(0, 60)}")`);
}
walk(copy, '');

// Section statuses: the gate counts a section without one as draft; here it is a note.
for (const [section, value] of Object.entries(copy)) {
  if (section.startsWith('$') || typeof value !== 'object') continue;
  if (!['draft', 'placeholder', 'approved'].includes(value.status)) notes.push(`${section}: no status (the gate counts it as draft)`);
}
// The fixed names and the tagline.
if (copy.meta.instagram !== '@darkestshades') findings.push('meta.instagram is not @darkestshades');
if (copy.meta.domain !== 'darkestshades.com') findings.push('meta.domain is not darkestshades.com');
if (copy.meta.hashtag !== '#DarkestShades') findings.push('meta.hashtag is not #DarkestShades');
if (copy.meta.tagline !== 'See Everything. Reveal Nothing.') findings.push('meta.tagline is not the tagline');

if (notes.length) console.log(`[copy-audit] ${notes.length} note(s):\n  ${notes.join('\n  ')}`);
if (findings.length) {
  console.error(`[copy-audit] ${findings.length} finding(s):\n  ${findings.join('\n  ')}`);
  process.exit(1);
}
console.log('[copy-audit] ok: no exclamation marks, hype, gendered address or name-dropping; the fixed names and the tagline exact; the price written $100');
