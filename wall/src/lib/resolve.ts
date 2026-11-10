// How a drawer's state is resolved (DRAWER-WALL.md, "Every drawer is its own thing"): a pure function of the record
// and the frame's facts.
//
//   1. hidden: a dark drawer, no label, not focusable, doesn't open.
//   2. locked: dark, wall.notYet with the look number, doesn't open.
//   3. sold_out: dark, the name and wall.soldOut; it opens, and the frame can be seen, lifted and turned.
//   4. available: lit, the name; it opens.
//   No price in any state (00-decisions.md #47): the facts carry none and the label has no slot for one.
//   5. No frame, an unknown frame id or an unknown value: hidden, and logged.
//   6. `light` overrides the seam light only; it never changes what a drawer does.
//   7. The output: the state, the light, canOpen, canLift (the assets exist), the label. A missing value renders nothing.
import { BAY_LIGHTS, BAY_STATES, type AssetAvailability, type BayLightSetting, type BayState, type DrawerBayRecord, type FrameFacts, type FrameId, type ResolvedBay, type SeamLight } from './types';

export function isBayState(v: unknown): v is BayState {
  return typeof v === 'string' && (BAY_STATES as readonly string[]).includes(v);
}

export function isBayLight(v: unknown): v is BayLightSetting {
  return typeof v === 'string' && (BAY_LIGHTS as readonly string[]).includes(v);
}

function hidden(bay: DrawerBayRecord, frame: FrameFacts | null, problems: string[]): ResolvedBay {
  return { id: bay.id, handle: bay.handle, state: 'hidden', light: 'dark', frame, canOpen: false, canLift: false, focusable: false, label: null, problems };
}

export function resolveBay(bay: DrawerBayRecord, frames: Readonly<Partial<Record<FrameId, FrameFacts>>>, assets: AssetAvailability): ResolvedBay {
  const problems: string[] = [];
  const frame = bay.frame && Object.prototype.hasOwnProperty.call(frames, bay.frame) ? (frames[bay.frame as FrameId] ?? null) : null;
  if (!bay.frame) problems.push(`${bay.id}: no frame`);
  else if (!frame) problems.push(`${bay.id}: unknown frame "${bay.frame}"`);
  if (bay.state == null) problems.push(`${bay.id}: no state`);
  else if (!isBayState(bay.state)) problems.push(`${bay.id}: unknown state "${bay.state}"`);
  if (bay.light != null && !isBayLight(bay.light)) problems.push(`${bay.id}: unknown light "${bay.light}"`);
  if (problems.length) return hidden(bay, frame, problems);

  const state = bay.state as BayState;
  const f = frame as FrameFacts;
  if (state === 'hidden') return hidden(bay, f, problems);

  const lookNumber = f.lookNumber || null;
  const name = f.name || null;
  const auto: SeamLight = state === 'available' ? 'lit' : 'dark';
  const light: SeamLight = bay.light === 'lit' ? 'lit' : bay.light === 'dark' ? 'dark' : auto;
  const canOpen = state !== 'locked' && assets.hasSequence(f.id);
  const canLift = canOpen && assets.hasLift(f.id);
  const label = state === 'locked'
    ? { lookNumber, name: null, soldOut: false, notYet: true }
    : { lookNumber, name, soldOut: state === 'sold_out', notYet: false };
  return { id: bay.id, handle: bay.handle, state, light, frame: f, canOpen, canLift, focusable: true, label, problems };
}

/** Every drawer of the wall, in wall order. */
export function resolveWall(order: DrawerBayRecord[], frames: Readonly<Partial<Record<FrameId, FrameFacts>>>, assets: AssetAvailability): ResolvedBay[] {
  return order.map((bay) => resolveBay(bay, frames, assets));
}
