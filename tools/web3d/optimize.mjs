// GLB optimization (DRAWER-WALL.md, The frames in 3D): meshopt geometry, WebP textures (EXT_texture_webp), the
// budgets checked. gltf-transform's library, not its CLI, so the steps are explicit.
//
//   node tools/web3d/optimize.mjs work/glb/F09.glb wall/assets/glb/F09.glb
//   node tools/web3d/optimize.mjs --all            # every work/glb/F0X.glb into wall/assets/glb/
//   node tools/web3d/optimize.mjs --all --manifest # and each one's entry (kind glb) in wall/assets/manifest.json, with
//                                                 # frame_glb.py's --report (triangles, the GCD's length and side, the
//                                                 # front's width) as its checks
import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync, statSync } from 'node:fs';
import { resolve, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(resolve(ROOT, 'wall/package.json'));
const { NodeIO } = require('@gltf-transform/core');
const { ALL_EXTENSIONS, EXTMeshoptCompression, EXTTextureWebP } = require('@gltf-transform/extensions');
const { dedup, prune, reorder, quantize, textureCompress, weld, simplify, resample } = require('@gltf-transform/functions');
const { MeshoptEncoder, MeshoptSimplifier } = require('meshoptimizer');
const sharp = tryRequire('sharp');

function tryRequire(name) { try { return require(name); } catch { return null; } }

const BYTES_AIM = 3 * 1024 * 1024, BYTES_MAX = 6 * 1024 * 1024, TRIS_MAX = 100000, TEX_MAX = 2048;

async function optimize(src, out) {
  await MeshoptEncoder.ready;
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder });
  const doc = await io.read(src);
  await doc.transform(dedup(), prune(), weld());
  if (sharp) await doc.transform(textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [TEX_MAX, TEX_MAX], quality: 86 }));
  await doc.transform(reorder({ encoder: MeshoptEncoder }), quantize({ quantizePosition: 14, quantizeNormal: 10, quantizeTexcoord: 12 }));
  doc.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.FILTER });
  if (sharp) doc.createExtension(EXTTextureWebP).setRequired(true);
  mkdirSync(dirname(out), { recursive: true });
  await io.write(out, doc);
  const bytes = statSync(out).size;
  let tris = 0, textures = [];
  for (const mesh of doc.getRoot().listMeshes()) for (const prim of mesh.listPrimitives()) {
    const idx = prim.getIndices(); tris += idx ? idx.getCount() / 3 : prim.getAttribute('POSITION').getCount() / 3;
  }
  for (const tex of doc.getRoot().listTextures()) { const s = tex.getSize(); textures.push({ name: tex.getName(), mime: tex.getMimeType(), size: s }); }
  const materials = doc.getRoot().listMaterials().map((m) => m.getName());
  const fails = [];
  if (bytes > BYTES_MAX) fails.push(`${bytes} bytes, over ${BYTES_MAX}`);
  if (tris > TRIS_MAX) fails.push(`${tris} triangles, over ${TRIS_MAX}`);
  for (const t of textures) if (t.size && (t.size[0] > TEX_MAX || t.size[1] > TEX_MAX)) fails.push(`${t.name}: ${t.size.join('x')}, over ${TEX_MAX}`);
  const report = { src, out, bytes, overAim: bytes > BYTES_AIM, tris, materials, textures, fails };
  console.log(JSON.stringify(report));
  return report;
}

/** The manifest entry for an optimized GLB: the optimizer's measurements and frame_glb.py's report (work/glb/<frame>.report.json) as its checks. */
function manifestEntry(frame, report) {
  const reportPath = resolve(ROOT, 'work/glb', `${frame}.report.json`);
  const built = existsSync(reportPath) ? JSON.parse(readFileSync(reportPath, 'utf8')) : {};
  const tools = ['tools/blender/frame_glb.py', 'tools/blender/frame3d.py', 'tools/web3d/optimize.mjs'];
  const hash = createHash('sha1');
  for (const t of tools) if (existsSync(resolve(ROOT, t))) hash.update(readFileSync(resolve(ROOT, t)));
  let commit = '0000000';
  try {
    commit = execSync('git rev-parse --short=12 HEAD', { cwd: ROOT, encoding: 'utf8' }).trim();
    if (execSync('git status --porcelain -- tools/blender tools/web3d', { cwd: ROOT, encoding: 'utf8' }).trim()) commit += '-dirty';
  } catch {}
  const checks = {
    bytes: report.bytes, withinAim: !report.overAim, triangles: Math.round(report.tris), textures: report.textures.map((t) => `${t.name} ${t.mime} ${(t.size || []).join('x')}`).join('; ') || 'none',
    materials: report.materials.join(', '),
  };
  if (built.gcdLengthMm != null) checks.gcdLengthMm = Math.round(built.gcdLengthMm * 100) / 100;
  if (built.gcdOnWearersRight != null) checks.gcdOnWearersRight = built.gcdOnWearersRight;
  if (built.frontWidthMm != null) checks.frontWidthMm = Math.round(built.frontWidthMm * 100) / 100;
  if (built.builtTriangles != null) checks.builtTriangles = built.builtTriangles;
  if (built.check != null) checks.frameGlbCheck = built.check;
  // the D4 review's measurements: the band's proportion against the master's, the centre against the brand rule, the lens's source
  if (built.gcdProportion != null) checks.gcdProportion = Math.round(built.gcdProportion * 10000) / 10000;
  if (built.gcdMasterProportion != null) checks.gcdMasterProportion = built.gcdMasterProportion;
  if (built.gcdRule) {   // the manifest's checks are scalars
    checks.gcdRuleFaceMm = built.gcdRule.faceMm;
    checks.gcdBehindHingeMm = Math.round(built.gcdRule.behindHingeMm * 100) / 100;
    checks.gcdBelowTopMm = Math.round(built.gcdRule.belowTopMm * 100) / 100;
  }
  if (built.lensSource) checks.lensSource = built.lensSource;
  const tint = built.tint ? ` --tint ${built.tint.join(' ')}` : '';
  return {
    id: `glb/${frame}`, kind: 'glb', files: [`glb/${frame}.glb`], status: 'mockup', frame,
    tool: 'tools/blender/frame_glb.py', command: `frame_glb.py ${frame} --out work/glb/${frame}.glb${tint} --check --report work/glb/${frame}.report.json; optimize.mjs work/glb/${frame}.glb wall/assets/glb/${frame}.glb (meshopt, WebP textures)`,
    sourceCommit: commit, toolsHash: hash.digest('hex').slice(0, 12), checks,
  };
}

function putManifest(entries) {
  const path = resolve(ROOT, 'wall/assets/manifest.json');
  const m = existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : { $schema: './manifest.schema.json', renderSet: 'wall-v1', assets: [] };
  for (const e of entries) m.assets = m.assets.filter((a) => a.id !== e.id).concat([e]);
  m.assets.sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  writeFileSync(path, JSON.stringify(m, null, 2) + '\n');
  console.log(`manifest: ${entries.length} glb entries written`);
}

const args = process.argv.slice(2);
const manifest = args.includes('--manifest');
const rest = args.filter((a) => a !== '--manifest');
let failures = 0;
const entries = [];
if (rest[0] === '--all') {
  const dir = resolve(ROOT, 'work/glb');
  for (const f of readdirSync(dir).filter((f) => /^F0[1-9]\.glb$/.test(f)).sort()) {
    const r = await optimize(resolve(dir, f), resolve(ROOT, 'wall/assets/glb', f));
    failures += r.fails.length;
    if (manifest && !r.fails.length) entries.push(manifestEntry(basename(f, '.glb'), r));
  }
} else {
  const r = await optimize(resolve(rest[0]), resolve(rest[1]));
  failures += r.fails.length;
  if (manifest && !r.fails.length) entries.push(manifestEntry(basename(rest[1], '.glb'), r));
}
if (manifest && entries.length) putManifest(entries);
process.exit(failures ? 1 : 0);
