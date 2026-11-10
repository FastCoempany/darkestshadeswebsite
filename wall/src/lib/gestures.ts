// Interaction constants and the gesture math (DRAWER-WALL.md, "Interaction constants"). Pure functions: the elements
// feed them pointer deltas and get decisions back, so every rule has a unit test.

/** A tap: under 8 px of movement and 400 ms. Longer presses do nothing. */
export const TAP_MAX_PX = 8;
export const TAP_MAX_MS = 400;
/** The knob's touch target, pull first: 44 × 44 px or more. */
export const KNOB_MIN_PX = 44;
/** A full pull is 45% of the view's height; past the ends the drawer rubber-bands at most 12 px. */
export const FULL_PULL = 0.45;
export const RUBBER_MAX_PX = 12;
/** Release: velocity over 0.35 px/ms wins; otherwise position >= 0.5 opens. */
export const RELEASE_VELOCITY = 0.35;
export const RELEASE_POSITION = 0.5;
/** The settle spring; reduced motion snaps with a 160 ms cross-fade instead. */
export const SETTLE_SPRING = { stiffness: 180, damping: 26 } as const;
export const REDUCED_FADE_MS = 160;
/** The lift: a spring to the inspect pose, about 900 ms; 200 ms cross-fade under reduced motion. */
export const LIFT_MS = 900;
export const LIFT_REDUCED_MS = 200;
/** Turning (00-decisions.md #48): one finger turns the lifted frame about any axis, 0.4° a pixel, with no limit in any
 * direction; inertia friction 0.92 a frame, none under reduced motion. */
export const TURN_PER_PX = 0.4;
export const INERTIA_FRICTION = 0.92;
/** Zoom 1× to 3×; double-tap 1× ↔ 2.2× toward the tap; wheel 1.1× a step. */
export const ZOOM_MIN = 1;
export const ZOOM_MAX = 3;
export const DOUBLE_TAP_ZOOM = 2.2;
export const WHEEL_STEP = 1.1;
/** Hints: after 1.2 s idle in a state; gone after the first success of that gesture, for the session. */
export const HINT_IDLE_MS = 1200;
/** Haptics: a 10 ms tick at the open and shut stops where navigator.vibrate exists; never the only signal. */
export const HAPTIC_MS = 10;
/** The handoff cross-fade from the rendered frame to the live one. */
export const HANDOFF_FADE_MS = 120;
/** Decoded sequence frames held: the current one ± 2. */
export const DECODE_WINDOW = 2;

export const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

/** A pointer that moved under 8 px and lifted under 400 ms is a tap. */
export function isTap(dx: number, dy: number, dtMs: number): boolean {
  return Math.hypot(dx, dy) < TAP_MAX_PX && dtMs < TAP_MAX_MS;
}

/** The rubber band past an end: `overPx` of overshoot becomes at most `maxPx` of movement, easing toward it. */
export function rubberBand(overPx: number, maxPx = RUBBER_MAX_PX): number {
  if (overPx <= 0) return 0;
  return maxPx * (1 - 1 / (1 + overPx / maxPx));
}

/** The drawer's position (0 shut, 1 open) for a finger that moved `dyPx` down from where the pull began at
 * position `from`, in a view `viewHeightPx` tall. Past the ends the position carries the rubber band, so the
 * drawer can sit a little past 0 or 1 while the finger holds it. */
export function pullPosition(from: number, dyPx: number, viewHeightPx: number): number {
  const reach = Math.max(1, viewHeightPx * FULL_PULL);
  const raw = from + dyPx / reach;
  if (raw > 1) return 1 + rubberBand((raw - 1) * reach) / reach;
  if (raw < 0) return -rubberBand(-raw * reach) / reach;
  return raw;
}

/** At release: velocity (px/ms, positive pulling out) over 0.35 wins; otherwise position >= 0.5 opens. */
export function releaseDecision(velocityPxPerMs: number, position: number): 'open' | 'shut' {
  if (Math.abs(velocityPxPerMs) > RELEASE_VELOCITY) return velocityPxPerMs > 0 ? 'open' : 'shut';
  return position >= RELEASE_POSITION ? 'open' : 'shut';
}

/** A rotation as a unit quaternion, x y z w, in view space: x is the viewer's right, y up, z toward the viewer. */
export type Quat = readonly [number, number, number, number];
export const IDENTITY_ROT: Quat = [0, 0, 0, 1];

export function quatFromAxisAngle(axis: readonly [number, number, number], deg: number): Quat {
  const h = (deg * Math.PI) / 360, s = Math.sin(h);
  return [axis[0] * s, axis[1] * s, axis[2] * s, Math.cos(h)];
}

/** a · b: b's rotation first, then a's. */
export function quatMultiply(a: Quat, b: Quat): Quat {
  const [ax, ay, az, aw] = a, [bx, by, bz, bw] = b;
  return [
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by - ax * bz + ay * bw + az * bx,
    aw * bz + ax * by - ay * bx + az * bw,
    aw * bw - ax * bx - ay * by - az * bz,
  ];
}

export function quatNormalize(q: Quat): Quat {
  const n = Math.hypot(q[0], q[1], q[2], q[3]) || 1;
  return [q[0] / n, q[1] / n, q[2] / n, q[3] / n];
}

/** A vector turned by the rotation. */
export function rotateVector(q: Quat, v: readonly [number, number, number]): [number, number, number] {
  const [x, y, z, w] = q;
  const [vx, vy, vz] = v;
  // t = 2 (q.xyz × v); v' = v + w t + q.xyz × t
  const tx = 2 * (y * vz - z * vy), ty = 2 * (z * vx - x * vz), tz = 2 * (x * vy - y * vx);
  return [vx + w * tx + (y * tz - z * ty), vy + w * ty + (z * tx - x * tz), vz + w * tz + (x * ty - y * tx)];
}

/** One finger turns the frame freely (#48): a drag of `dxPx` to the right turns it about the view's vertical axis, a drag
 * of `dyPx` down turns it about the view's horizontal axis, 0.4° a pixel each, applied in view space on top of the turn
 * so far, so the frame always follows the finger whatever way it is already facing, and no direction has a limit. */
export function turnFree(rot: Quat, dxPx: number, dyPx: number): Quat {
  const aboutUp = quatFromAxisAngle([0, 1, 0], dxPx * TURN_PER_PX);
  const aboutRight = quatFromAxisAngle([1, 0, 0], dyPx * TURN_PER_PX);
  return quatNormalize(quatMultiply(quatMultiply(aboutRight, aboutUp), rot));
}

/** The turn as angles, for the tests: yaw about the vertical, pitch about the horizontal, roll about the line
 * of sight, in degrees (three.js's YXZ order), each in −180 to 180. */
export function turnAngles(q: Quat): { yaw: number; pitch: number; roll: number } {
  const [x, y, z, w] = q;
  const m11 = 1 - 2 * (y * y + z * z), m13 = 2 * (x * z + y * w);
  const m21 = 2 * (x * y + z * w), m22 = 1 - 2 * (x * x + z * z), m23 = 2 * (y * z - x * w);
  const m31 = 2 * (x * z - y * w), m33 = 1 - 2 * (x * x + y * y);
  const deg = (r: number) => (r * 180) / Math.PI;
  const pitch = Math.asin(-clamp(m23, -1, 1));
  if (Math.abs(m23) < 0.9999999) return { yaw: deg(Math.atan2(m13, m33)), pitch: deg(pitch), roll: deg(Math.atan2(m21, m22)) };
  return { yaw: deg(Math.atan2(-m31, m11)), pitch: deg(pitch), roll: 0 };
}

/** Inertia after the finger lifts: the angular velocity decays by 0.92 a frame; under reduced motion there is none. */
export function inertiaStep(velocity: number, reducedMotion: boolean): number {
  if (reducedMotion) return 0;
  const v = velocity * INERTIA_FRICTION;
  return Math.abs(v) < 0.01 ? 0 : v;
}

export const clampZoom = (z: number): number => clamp(z, ZOOM_MIN, ZOOM_MAX);

/** A pinch scales directly. */
export function pinchZoom(zoom: number, scale: number): number {
  return clampZoom(zoom * scale);
}

/** A double tap goes to 2.2× from 1×, and back to 1× from anywhere above 1×. */
export function doubleTapZoom(zoom: number): number {
  return zoom > 1 + 1e-6 ? ZOOM_MIN : DOUBLE_TAP_ZOOM;
}

/** The wheel: 1.1× a step, in by scrolling up. */
export function wheelZoom(zoom: number, deltaY: number): number {
  if (deltaY === 0) return zoom;
  return clampZoom(deltaY < 0 ? zoom * WHEEL_STEP : zoom / WHEEL_STEP);
}

/** Zooming toward a point keeps that point still: the new pan for a zoom from `z0` to `z1` about `(px, py)`
 * (view coordinates, from the view's centre). */
export function zoomAbout(pan: { x: number; y: number }, z0: number, z1: number, px: number, py: number): { x: number; y: number } {
  const k = z1 / z0;
  return { x: px - (px - pan.x) * k, y: py - (py - pan.y) * k };
}
