// The springs, a few lines (DRAWER-WALL.md, "The stack"): a damped spring stepped at the frame rate, used for the
// drawer's settle (stiffness 180, damping 26) and the lift. Pure: state in, state out.

export interface SpringParams { stiffness: number; damping: number; mass?: number }
export interface SpringState { x: number; v: number }

/** One step of `dtMs` toward `target`. Semi-implicit Euler in substeps of at most 16 ms, so a long frame does not
 * blow the spring up. */
export function springStep(s: SpringState, target: number, dtMs: number, p: SpringParams): SpringState {
  const mass = p.mass ?? 1;
  let { x, v } = s;
  let left = Math.max(0, dtMs) / 1000;
  while (left > 0) {
    const h = Math.min(left, 0.016);
    const a = (-p.stiffness * (x - target) - p.damping * v) / mass;
    v += a * h;
    x += v * h;
    left -= h;
  }
  return { x, v };
}

/** Settled: within `eps` of the target and nearly still. */
export function springSettled(s: SpringState, target: number, eps = 0.001, vEps = 0.01): boolean {
  return Math.abs(s.x - target) < eps && Math.abs(s.v) < vEps;
}

/** The whole motion at once: positions sampled every `stepMs` until settled (a test helper, and the reduced-motion
 * path, which takes only the last). */
export function springTrace(from: number, target: number, p: SpringParams, stepMs = 16, maxMs = 5000): number[] {
  let s: SpringState = { x: from, v: 0 };
  const out: number[] = [];
  for (let t = 0; t < maxMs; t += stepMs) {
    s = springStep(s, target, stepMs, p);
    out.push(s.x);
    if (springSettled(s, target)) break;
  }
  return out;
}
