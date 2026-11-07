// Serve the scratchpad over http, render the S1 page in headless Chromium with WebGL, save the canvas.
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import { chromium } from 'playwright';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.glb': 'model/gltf-binary', '.hdr': 'application/octet-stream', '.png': 'image/png', '.webp': 'image/webp' };
const srv = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
});
await new Promise(r => srv.listen(0, '127.0.0.1', r));
const port = srv.address().port;
const [dir, variant, outPng, rot, hdr] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1100, height: 1100 } });
page.on('console', m => console.error('[page]', m.text()));
page.on('pageerror', e => console.error('[pageerror]', e.message));
await page.goto(`http://127.0.0.1:${port}/s1/web/index.html?dir=${dir}&variant=${variant}&rot=${rot || 0}&hdr=${hdr || 'env.hdr'}`);
const done = await page.waitForFunction(() => window.__done, null, { timeout: 180000 }).then(h => h.jsonValue());
fs.writeFileSync(outPng, Buffer.from(done.png.split(',')[1], 'base64'));
console.log(JSON.stringify(done.info));
await browser.close(); srv.close();
