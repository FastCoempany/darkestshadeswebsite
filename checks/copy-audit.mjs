#!/usr/bin/env node
// The copy audit against docs/brief/08-copy.md: every string in content/copy/en.json.
//   - no exclamation marks; no hype words; no gendered address; no name-dropping;
//   - sentence case (a sentence starts with a capital, no Title Case runs) except keys that are names or labels;
//   - the fixed names: @darkestshades, darkestshades.com, #DarkestShades (with the s), never "Zara in in";
//   - the price is written "$100"; the tagline is exact; no "ultra-dark" per frame; no lorem ipsum.
// A string the founder has a logged question about is noted, not failed (NOTED below, with the reason).
// Sections without a status are the draft-copy gate's business (checks/copy-gate.mjs), listed here as a note.
import {readFileSync, readdirSync} from 'node:fs';
import {join} from 'node:path';

const ROOT = new URL('..', import.meta.url).pathname;
const copy = JSON.parse(readFileSync(join(ROOT, 'content/copy/en.json'), 'utf8'));

const HYPE = ['must-have', 'obsessed', 'run, don’t walk', "run, don't walk", 'tag your bestie', 'you need these', 'fire', 'iconic', 'game-changer', 'elevate', 'unleash', 'limited time', 'hurry', 'don’t miss', "don't miss", 'last chance', 'exclusive deal', 'ends tonight', 'selling fast', 'people are viewing', 'sold in the last hour', 'almost gone'];
const GENDERED = ['bro', 'babe', 'girlboss', 'dude', 'guys', 'ladies'];
const NAMES = ['prada', 'simons', 'runway', 'celebrity', 'as seen at'];

/**
 * Strings with a logged question in docs/build/PROGRESS.md: reported, never failed, until the founder answers.
 * A key is honoured only while PROGRESS.md's questions name it, so the list cannot silence a finding quietly.
 */
const NOTED = {
  'alt.scenes.S01': 'the S01 set is a bare runway (07-photography.md); no picture uses it yet; logged as a question',
};
const progress = readFileSync(join(ROOT, 'docs/build/PROGRESS.md'), 'utf8');
const questions = progress.slice(progress.indexOf('## Questions for Antaeus'), progress.indexOf('## Copy to sign off'));
for (const key of Object.keys(NOTED)) {
  if (!questions.includes(`\`${key}\``)) {
    console.error(`[copy-audit] ${key} is exempted but docs/build/PROGRESS.md's questions do not name it`);
    process.exit(1);
  }
}

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
function check(text, path, {isName = false} = {}) {
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
  // Set uppercase by style, never typed in caps (08): two or more words typed in capitals.
  if (/^[A-Z0-9 .·:,'’!?-]+$/.test(text) && text.trim().split(/\s+/).filter((w) => /[A-Z]{2,}/.test(w)).length >= 2 && !/^(HELP|STOP|START|UV400|TAC|SMS|UVA|UVB|GCD)( |$)/.test(text)) push(`${path}: typed in capitals ("${text.slice(0, 60)}")`);
  // Sentence case: a Title Case run of three or more capitalised words inside a sentence.
  if (!isName && !/^[A-Z0-9 .·:,'’-]+$/.test(text) && /\b([A-Z][a-z]+ ){2,}[A-Z][a-z]+\b/.test(text.replace(/Darkest Shades|God Cloud Device|Privacy Policy|SMS Terms|Date to be announced|HELP|STOP|START|UVA|UVB|UV400|TAC|E\.164/g, ''))) push(`${path}: Title Case run ("${text.slice(0, 60)}")`);
}
walk(copy, '');

// The founder's product and drop words go through the same rules (08 Claims: "ultra-dark" never on F01, F03, F06 or F08).
const NEVER_ULTRA_DARK = new Set(['F01', 'F03', 'F06', 'F08']);
for (const file of readdirSync(join(ROOT, 'content/products')).filter((f) => /^f\d\d\.json$/.test(f))) {
  const product = JSON.parse(readFileSync(join(ROOT, 'content/products', file), 'utf8'));
  const id = String(product.id ?? file.replace('.json', '').toUpperCase());
  const fields = {name: product.name, descriptor: product.descriptor, 'lens.color': product.lens?.color, 'copy.line': product.copy?.line, 'copy.story': product.copy?.story};
  for (const [k, v] of Object.entries(fields)) {
    if (typeof v !== 'string') continue;
    check(v, `${file}:${k}`, {isName: k === 'name'});
    if (NEVER_ULTRA_DARK.has(id) && /ultra-dark/i.test(v)) findings.push(`${file}:${k}: "ultra-dark" never on ${id} (08 Claims)`);
  }
}
for (const file of readdirSync(join(ROOT, 'content/drops')).filter((f) => f.endsWith('.json'))) {
  const drop = JSON.parse(readFileSync(join(ROOT, 'content/drops', file), 'utf8'));
  if (typeof drop.statement === 'string') check(drop.statement, `${file}:statement`);
}

// Legal and safety copy (08): the strings the site must carry, with their required elements.
const need = (path, text, parts) => {
  if (typeof text !== 'string' || !text) return findings.push(`${path}: missing`);
  for (const [what, re] of parts) if (!re.test(text)) findings.push(`${path}: lacks ${what}`);
};
need('entry.notice.text', copy.entry?.notice?.text, [['the flashing-images warning', /rapidly changing images|flashing/i], ['the way out', /skip/i]]);
need('entry.notice.continue', copy.entry?.notice?.continue, [['a Continue button', /^Continue$/]]);
need('entry.notice.skip', copy.entry?.notice?.skip, [['a Skip intro button', /^Skip intro$/]]);
need('list.emailConsent', copy.list?.emailConsent, [['what they will get', /about drops/i], ['unsubscribe any time', /unsubscribe any time/i], ['the privacy link', /privacy policy/i]]);
need('list.smsConsent', copy.list?.smsConsent, [
  ['recurring automated marketing texts', /recurring automated marketing text/i],
  ['consent not a condition of purchase', /not a condition of purchase/i],
  ['frequency varies', /frequency varies/i],
  ['message and data rates', /data rates may apply/i],
  ['HELP', /\bHELP\b/],
  ['STOP', /\bSTOP\b/],
  ['the SMS terms link', /SMS Terms/],
  ['the privacy link', /Privacy Policy/],
]);
for (const [k, v] of Object.entries(copy.sms ?? {})) {
  if (k === 'status' || typeof v !== 'string') continue;
  need(`sms.${k}`, v, [['the brand first', /^Darkest Shades/], ...(k === 'stop' ? [] : [['the opt-out last', /STOP to cancel\.?$/]])]);
}
need('product.imageDisclosure', copy.product?.imageDisclosure, [['the disclosure of generated models', /generated models/i]]);

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
