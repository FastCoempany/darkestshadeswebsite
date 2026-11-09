// Lighthouse mobile on the built wall (DRAWER-WALL.md, Budgets): performance >= 90, LCP <= 2.5 s, CLS <= 0.1,
// TBT <= 200 ms. Serves wall/dist with `vite preview`, audits it with the Playwright Chromium, writes the report to
// work/lighthouse/report.json (outside Playwright's output folder, which the next run clears) and prints the four
// numbers and the LCP element (Lighthouse 13 names it in the lcp-discovery insight). Fails on any budget, and refuses
// to run against a server it did not start: port 4173 must be free. The preview is spawned as its own process group
// and the group is killed at the end, so no server is left behind (spawning `npm run preview` left vite orphaned).
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
try { await fetch(URL); console.error('lighthouse: something already answers on 127.0.0.1:4173; stop it first (this check audits only the server it starts)'); process.exit(1); } catch {}
const server = spawn(process.execPath, [resolve(WALL, 'node_modules/vite/bin/vite.js'), 'preview', '--host', '127.0.0.1', '--port', '4173', '--strictPort'], { cwd: WALL, stdio: 'ignore', detached: true });
const ready = async () => { for (let i = 0; i < 60; i++) { if (server.exitCode !== null) throw new Error(`preview server exited with ${server.exitCode}`); try { const r = await fetch(URL); if (r.ok) return; } catch {} await new Promise((r) => setTimeout(r, 500)); } throw new Error('preview server did not start'); };
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
    const lcpNode = (a) => { const items = a?.details?.items ?? []; const walk = (x) => { if (!x || typeof x !== 'object') return null; if (x.type === 'node' && (x.selector || x.snippet)) return x; for (const v of Object.values(x)) { const r = walk(v); if (r) return r; } return null; }; return walk(items); };
    const node = lcpNode(lhr.audits['largest-contentful-paint-element']) ?? lcpNode(lhr.audits['lcp-discovery-insight']) ?? lcpNode(lhr.audits['lcp-breakdown-insight']);
    const lcpEl = node ? `${node.selector ?? ''} ${node.snippet ?? ''}`.trim() : '?';
    const OUT = resolve(WALL, '../work/lighthouse');
    mkdirSync(OUT, { recursive: true });
    writeFileSync(resolve(OUT, 'report.json'), result.report);
    const fails = [];
    for (const [name, v] of [['LCP', lcp], ['CLS', cls], ['TBT', tbt]]) if (Number.isNaN(v)) fails.push(`${name} not measured`);
    if (score < 90) fails.push(`performance ${score} < 90`);
    if (lcp > 2500) fails.push(`LCP ${lcp.toFixed(0)} ms > 2500`);
    if (cls > 0.1) fails.push(`CLS ${cls.toFixed(3)} > 0.1`);
    if (tbt > 200) fails.push(`TBT ${tbt.toFixed(0)} ms > 200`);
    console.log(`lighthouse: performance ${score}, LCP ${lcp.toFixed(0)} ms, CLS ${cls.toFixed(3)}, TBT ${tbt.toFixed(0)} ms, LCP element ${lcpEl.slice(0, 120)}; report work/lighthouse/report.json`);
    if (lcpEl === '?') fails.push('LCP element not found in the report');
    for (const f of fails) console.error(`lighthouse: ${f}`);
    code = fails.length ? 1 : 0;
  } finally { await chrome.kill(); }
} catch (e) { console.error('lighthouse:', e.message); }
finally { try { process.kill(-server.pid, 'SIGTERM'); } catch { try { server.kill('SIGTERM'); } catch {} } }
process.exit(code);
