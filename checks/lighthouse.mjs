#!/usr/bin/env node
// Lighthouse, mobile, against the review build (production settings, drafts allowed): Home, Frames and a
// frame page (09-build-plan.md, phase 6). Writes reports to docs/qa/lighthouse/ and prints the scores.
//   node checks/lighthouse.mjs            report only
//   node checks/lighthouse.mjs --assert   exit 1 when a page's performance is under 90
import {mkdirSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';
import lighthouse from 'lighthouse';
import {launch} from 'chrome-launcher';

const ROOT = new URL('..', import.meta.url).pathname;
const BASE = process.env.LH_BASE || 'http://localhost:3000';
const CHROME = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1243/chrome-linux64/chrome';
const PAGES = (process.env.LH_PAGES || '/,/frames,/frames/lou-went-underground').split(',');
const OUT = join(ROOT, 'docs/qa/lighthouse');
const assert = process.argv.includes('--assert');
mkdirSync(OUT, {recursive: true});

const chrome = await launch({chromePath: CHROME, chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']});
let failed = false;
const summary = [];
try {
  for (const path of PAGES) {
    const result = await lighthouse(`${BASE}${path}`, {port: chrome.port, output: ['html', 'json'], logLevel: 'error', formFactor: 'mobile', screenEmulation: {mobile: true, width: 390, height: 844, deviceScaleFactor: 2, disabled: false}, throttlingMethod: 'simulate'});
    const cats = result.lhr.categories;
    const scores = Object.fromEntries(Object.entries(cats).map(([k, v]) => [k, Math.round((v.score ?? 0) * 100)]));
    const slug = path === '/' ? 'home' : path.replace(/^\//, '').replace(/\//g, '-');
    writeFileSync(join(OUT, `${slug}.html`), result.report[0]);
    writeFileSync(join(OUT, `${slug}.json`), result.report[1]);
    const audits = result.lhr.audits;
    const line = `${path}: performance ${scores.performance}, accessibility ${scores.accessibility}, best-practices ${scores['best-practices']}, seo ${scores.seo} | LCP ${audits['largest-contentful-paint']?.displayValue}, CLS ${audits['cumulative-layout-shift']?.displayValue}, TBT ${audits['total-blocking-time']?.displayValue}, transfer ${audits['total-byte-weight']?.displayValue}`;
    console.log(`[lighthouse] ${line}`);
    summary.push({path, scores, lcp: audits['largest-contentful-paint']?.numericValue, cls: audits['cumulative-layout-shift']?.numericValue, tbt: audits['total-blocking-time']?.numericValue, bytes: audits['total-byte-weight']?.numericValue});
    if (scores.performance < 90) failed = true;
  }
} finally {
  await chrome.kill();
}
writeFileSync(join(OUT, 'summary.json'), JSON.stringify({base: BASE, date: new Date().toISOString(), pages: summary}, null, 1));
if (assert && failed) {
  console.error('[lighthouse] a page scored under 90 on performance');
  process.exit(1);
}
