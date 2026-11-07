// The tiers (DRAWER-WALL.md, "In the browser"). Tier 0 is no JavaScript: the page's <noscript> (the wall plate and a
// plain list of the eight drawers). With JavaScript: tier 1 (no WebGL 2, under 4 GB of device memory where reported,
// Save-Data, or a lost context) is everything but the live frame; tier 2 is everything.

export interface TierSignals {
  webgl2: boolean;
  /** navigator.deviceMemory in GB, where the browser reports it; undefined where it doesn't (Safari). */
  deviceMemory: number | undefined;
  saveData: boolean;
  contextLost: boolean;
}

export type Tier = 1 | 2;

export function tierFor(s: TierSignals): Tier {
  if (!s.webgl2) return 1;
  if (typeof s.deviceMemory === 'number' && s.deviceMemory < 4) return 1;
  if (s.saveData) return 1;
  if (s.contextLost) return 1;
  return 2;
}

/** Why a visit is on tier 1, for the debug log. */
export function tierReasons(s: TierSignals): string[] {
  const r: string[] = [];
  if (!s.webgl2) r.push('no WebGL 2');
  if (typeof s.deviceMemory === 'number' && s.deviceMemory < 4) r.push(`device memory ${s.deviceMemory} GB`);
  if (s.saveData) r.push('Save-Data');
  if (s.contextLost) r.push('WebGL context lost');
  return r;
}

/** The signals read from a browser; `probe` makes the WebGL 2 test replaceable in tests. */
export function readSignals(nav: Partial<Navigator> & { connection?: { saveData?: boolean } }, probeWebGL2: () => boolean, contextLost = false): TierSignals {
  const dm = (nav as { deviceMemory?: number }).deviceMemory;
  return {
    webgl2: safely(probeWebGL2),
    deviceMemory: typeof dm === 'number' ? dm : undefined,
    saveData: !!nav.connection?.saveData,
    contextLost,
  };
}

function safely(f: () => boolean): boolean {
  try { return f(); } catch { return false; }
}

/** The WebGL 2 probe for a real browser: a throwaway canvas. */
export function probeWebGL2(doc: Document): boolean {
  const c = doc.createElement('canvas');
  const gl = c.getContext('webgl2');
  if (!gl) return false;
  const ext = gl.getExtension('WEBGL_lose_context');
  ext?.loseContext();
  return true;
}
