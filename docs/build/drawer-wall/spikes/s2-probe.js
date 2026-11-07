// S2: a JS module in a published Artifact. Reports what the host lets a module do: fetch a GLB as bytes,
// decode a WebP with createImageBitmap, use WebGL 2, and read a sibling JSON.
export const loaded = true;
export async function run(report) {
  const out = { module: true, ua: navigator.userAgent, dpr: devicePixelRatio, width: innerWidth };
  // the Artifact host serves no .glb, so the GLB is published under a served extension (.wasm) and fetched as bytes
  for (const [key, name] of [['glb', './F09.glb.wasm'], ['glbPlain', './F09.glb']]) {
    try {
      const r = await fetch(name); const buf = await r.arrayBuffer();
      const magic = new TextDecoder().decode(new Uint8Array(buf, 0, 4));
      out[key] = { ok: r.ok, status: r.status, bytes: buf.byteLength, magic, type: r.headers.get('content-type') };
    } catch (e) { out[key] = { error: String(e) }; }
  }
  try {
    const r = await fetch('./still.webp'); const blob = await r.blob();
    const t0 = performance.now(); const bmp = await createImageBitmap(blob);
    out.webp = { ok: r.ok, bytes: blob.size, type: blob.type, width: bmp.width, height: bmp.height, decodeMs: Math.round(performance.now() - t0) };
    const c = document.getElementById('c'); c.width = bmp.width; c.height = bmp.height; c.getContext('2d').drawImage(bmp, 0, 0);
    bmp.close();
  } catch (e) { out.webp = { error: String(e) }; }
  try {
    const r = await fetch('./still.avif'); const blob = await r.blob();
    const bmp = await createImageBitmap(blob); out.avif = { ok: r.ok, bytes: blob.size, width: bmp.width }; bmp.close();
  } catch (e) { out.avif = { error: String(e) }; }
  try {
    const gl = document.createElement('canvas').getContext('webgl2');
    out.webgl2 = gl ? { ok: true, renderer: (gl.getExtension('WEBGL_debug_renderer_info') ? gl.getParameter(gl.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL) : 'masked') } : { ok: false };
  } catch (e) { out.webgl2 = { error: String(e) }; }
  try { const r = await fetch('./data.json'); out.json = await r.json(); } catch (e) { out.json = { error: String(e) }; }
  out.deviceMemory = navigator.deviceMemory ?? null; out.saveData = navigator.connection?.saveData ?? null;
  out.vibrate = typeof navigator.vibrate === 'function';
  report(out);
}
