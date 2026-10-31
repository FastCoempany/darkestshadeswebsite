#!/usr/bin/env node
// Lighthouse, mobile, against the review build (production settings, drafts allowed): Home, Frames and a
// frame page (09-build-plan.md, phase 6). Writes reports to docs/qa/lighthouse/ and prints the scores.
// Home is measured twice: as a first visit (the photosensitivity notice over the page; the opening itself
// plays only after Continue and is not measured) and as every later visit (the `ds_entry=seen` cookie).
//   node checks/lighthouse.mjs            report only
//   node checks/lighthouse.mjs --assert   exit 1 when a page's performance is under 90 (npm run lighthouse)
import {mkdirSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';
import lighthouse from 'lighthouse';
import {launch} from 'chrome-launcher';

const ROOT = new URL('..', import.meta.url).pathname;
const BASE = process.env.LH_BASE || 'http://localhost:3000';
const CHROME = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome';
const PAGES = (process.env.LH_PAGES || '/,/,/frames,/frames/lou-went-underground').split(',');
/** The second home run carries the cookie of a returning visitor. */
const SEEN = 'ds_entry=seen';
const OUT = join(ROOT, 'docs/qa/lighthouse');
const assert = process.argv.includes('--assert');
mkdirSync(OUT, {recursive: true});

const chrome = await launch({chromePath: CHROME, chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']});
let failed = false;
const summary = [];
try {
  let homeRuns = 0;
  for (const path of PAGES) {
    const seen = path === '/' && homeRuns++ > 0;
    const result = await lighthouse(`${BASE}${path}`, {port: chrome.port, output: ['html', 'json'], logLevel: 'error', formFactor: 'mobile', screenEmulation: {mobile: true, width: 390, height: 844, deviceScaleFactor: 2, disabled: false}, throttlingMethod: 'simulate', extraHeaders: seen ? {Cookie: SEEN} : undefined});
    const cats = result.lhr.categories;
    const scores = Object.fromEntries(Object.entries(cats).map(([k, v]) => [k, Math.round((v.score ?? 0) * 100)]));
    const slug = path === '/' ? (seen ? 'home-seen' : 'home') : path.replace(/^\//, '').replace(/\//g, '-');
    writeFileSync(join(OUT, `${slug}.html`), result.report[0]);
    writeFileSync(join(OUT, `${slug}.json`), result.report[1]);
    const audits = result.lhr.audits;
    const line = `${path}${seen ? ' (returning visitor)' : path === '/' ? ' (first visit: the notice over the page)' : ''}: performance ${scores.performance}, accessibility ${scores.accessibility}, best-practices ${scores['best-practices']}, seo ${scores.seo} | LCP ${audits['largest-contentful-paint']?.displayValue}, CLS ${audits['cumulative-layout-shift']?.displayValue}, TBT ${audits['total-blocking-time']?.displayValue}, transfer ${audits['total-byte-weight']?.displayValue}`;
    console.log(`[lighthouse] ${line}`);
    summary.push({path, state: path === '/' ? (seen ? 'returning visitor (ds_entry=seen): the home page itself' : 'first visit: the photosensitivity notice over the page; the opening is not measured') : 'deep link', scores, lcp: audits['largest-contentful-paint']?.numericValue, cls: audits['cumulative-layout-shift']?.numericValue, tbt: audits['total-blocking-time']?.numericValue, bytes: audits['total-byte-weight']?.numericValue});
    if (scores.performance < 90) failed = true;
  }
} finally {
  await chrome.kill();
}
writeFileSync(join(OUT, 'summary.json'), JSON.stringify({base: BASE, date: new Date().toISOString(), note: 'Mobile, simulated throttling, against the review build (production settings, drafts allowed). Home as a first visit shows the photosensitivity notice; the opening plays only after Continue and is not measured. Home as a returning visitor is the page every deep link and later visit gets.', pages: summary}, null, 1));
if (assert && failed) {
  console.error('[lighthouse] a page scored under 90 on performance');
  process.exit(1);
}
