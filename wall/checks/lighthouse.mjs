// Lighthouse mobile on the built wall (DRAWER-WALL.md, Budgets): performance >= 90, LCP <= 2.5 s, CLS <= 0.1,
// TBT <= 200 ms. Serves wall/dist with `vite preview`, audits it with the Playwright Chromium, writes the report to
// wall/test-results/lighthouse.json and prints the four numbers. Fails on any budget.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import lighthouse from 'lighthouse';
import { launch } from 'chrome-launcher';

const WALL = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const URL = 'http://127.0.0.1:4173/';
const CHROME = process.env.CHROME_PATH ?? ['/opt/pw-browsers/chromium-1243/chrome-linux/chrome', '/opt/pw-browsers/chromium'].find(existsSync);

if (!existsSync(resolve(WALL, 'dist/index.html'))) { console.error('lighthouse: build the wall first (npm run build)'); process.exit(1); }
const server = spawn('npm', ['run', 'preview'], { cwd: WALL, stdio: 'ignore' });
const ready = async () => { for (let i = 0; i < 60; i++) { try { const r = await fetch(URL); if (r.ok) return; } catch {} await new Promise((r) => setTimeout(r, 500)); } throw new Error('preview server did not start'); };
let code = 1;
try {
  await ready();
  const chrome = await launch({ chromePath: CHROME, chromeFlags: ['--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] });
  try {
    const result = await lighthouse(URL, { port: chrome.port, output: 'json', logLevel: 'error', onlyCategories: ['performance'], formFactor: 'mobile', screenEmulation: { mobile: true, width: 390, height: 844, deviceScaleFactor: 3, disabled: false } });
    const lhr = result.lhr;
    const score = Math.round((lhr.categories.performance.score ?? 0) * 100);
    const n = (id) => lhr.audits[id]?.numericValue ?? NaN;
    const lcp = n('largest-contentful-paint'), cls = n('cumulative-layout-shift'), tbt = n('total-blocking-time');
    const lcpEl = lhr.audits['largest-contentful-paint-element']?.details?.items?.[0]?.items?.[0]?.node?.snippet ?? '?';
    mkdirSync(resolve(WALL, 'test-results'), { recursive: true });
    writeFileSync(resolve(WALL, 'test-results/lighthouse.json'), result.report);
    const fails = [];
    for (const [name, v] of [['LCP', lcp], ['CLS', cls], ['TBT', tbt]]) if (Number.isNaN(v)) fails.push(`${name} not measured`);
    if (score < 90) fails.push(`performance ${score} < 90`);
    if (lcp > 2500) fails.push(`LCP ${lcp.toFixed(0)} ms > 2500`);
    if (cls > 0.1) fails.push(`CLS ${cls.toFixed(3)} > 0.1`);
    if (tbt > 200) fails.push(`TBT ${tbt.toFixed(0)} ms > 200`);
    console.log(`lighthouse: performance ${score}, LCP ${lcp.toFixed(0)} ms, CLS ${cls.toFixed(3)}, TBT ${tbt.toFixed(0)} ms, LCP element ${lcpEl.slice(0, 80)}`);
    for (const f of fails) console.error(`lighthouse: ${f}`);
    code = fails.length ? 1 : 0;
  } finally { await chrome.kill(); }
} catch (e) { console.error('lighthouse:', e.message); }
finally { server.kill('SIGTERM'); }
process.exit(code);
