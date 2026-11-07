// The drawer's state machine (DRAWER-WALL.md, "The drawer's state machine"): a pure reducer, one instance per open
// drawer view. Impossible transitions return the same context object, so a caller (and a test) can tell by identity.
//
//   wall      OPEN (tap, Enter, knob pull) → entering, only if canOpen
//   entering  ENTERED → shut
//   shut      DRAG(p) → pulling; OPEN_DRAWER → opening; CLOSE → leaving
//   pulling   DRAG(p) → pulling; RELEASE(v, p) → opening or shutting
//   opening / shutting   SETTLED → open / shut
//   open      DRAG(p) → pulling; LIFT → lifting, only if canLift; CLOSE → leaving
//   lifting   LIFTED → lifted
//   lifted    TURN, ZOOM, RESET → lifted; PHOTOS → photos; PUT_BACK → returning
//   photos    BACK → lifted
//   returning RETURNED → open
//   leaving   LEFT → wall (focus back on the drawer)
//
// Esc steps back: photos → lifted → open → shut → wall. Pull first: OPEN carries the pointer and the same drag goes on
// as DRAG(p). A record changing while its drawer is open (RECORD) closes the view only if the drawer can no longer
// open; otherwise the view stays and its label updates.
import { clampZoom, releaseDecision, turn } from './gestures';

export type ViewState =
  | 'wall' | 'entering' | 'shut' | 'pulling' | 'opening' | 'shutting' | 'open'
  | 'lifting' | 'lifted' | 'photos' | 'returning' | 'leaving';

export type ViewEvent =
  | { type: 'OPEN'; pointer?: { x: number; y: number } }
  | { type: 'ENTERED' }
  | { type: 'DRAG'; p: number }
  | { type: 'RELEASE'; v: number; p: number }
  | { type: 'OPEN_DRAWER' }
  | { type: 'SHUT_DRAWER' }
  | { type: 'CLOSE' }
  | { type: 'SETTLED' }
  | { type: 'LIFT' }
  | { type: 'LIFTED' }
  | { type: 'TURN'; dx: number; dy: number }
  | { type: 'ZOOM'; zoom: number }
  | { type: 'RESET' }
  | { type: 'PHOTOS' }
  | { type: 'BACK' }
  | { type: 'PUT_BACK' }
  | { type: 'RETURNED' }
  | { type: 'LEFT' }
  | { type: 'ESC' }
  | { type: 'RECORD'; canOpen: boolean; canLift: boolean };

export interface ViewContext {
  state: ViewState;
  /** The drawer's position, 0 shut to 1 open (a little past either end while a finger holds it). */
  p: number;
  /** Where a settle is heading. */
  target: 'open' | 'shut' | null;
  /** The pull that opened the view carries on without a second touch (pull first). */
  pointerCarried: boolean;
  yaw: number;
  pitch: number;
  zoom: number;
  canOpen: boolean;
  canLift: boolean;
}

export function initialContext(canOpen: boolean, canLift: boolean): ViewContext {
  return { state: 'wall', p: 0, target: null, pointerCarried: false, yaw: 0, pitch: 0, zoom: 1, canOpen, canLift };
}

const INSPECT = { yaw: 0, pitch: 0, zoom: 1 };

export function reduce(ctx: ViewContext, ev: ViewEvent): ViewContext {
  if (ev.type === 'RECORD') {
    const next = { ...ctx, canOpen: ev.canOpen, canLift: ev.canLift };
    if (!ev.canOpen && ctx.state !== 'wall' && ctx.state !== 'leaving') return { ...next, state: 'leaving', target: null };
    return next;
  }
  if (ev.type === 'ESC') return escape(ctx);
  switch (ctx.state) {
    case 'wall':
      if (ev.type === 'OPEN' && ctx.canOpen) return { ...ctx, state: 'entering', p: 0, target: null, pointerCarried: !!ev.pointer };
      return ctx;
    case 'entering':
      if (ev.type === 'ENTERED') return { ...ctx, state: 'shut', p: 0 };
      return ctx;
    case 'shut':
      if (ev.type === 'DRAG') return { ...ctx, state: 'pulling', p: ev.p };
      if (ev.type === 'OPEN_DRAWER') return { ...ctx, state: 'opening', target: 'open' };
      if (ev.type === 'CLOSE') return { ...ctx, state: 'leaving', target: null, pointerCarried: false };
      return ctx;
    case 'pulling':
      if (ev.type === 'DRAG') return { ...ctx, p: ev.p };
      if (ev.type === 'RELEASE') {
        const to = releaseDecision(ev.v, ev.p);
        return { ...ctx, state: to === 'open' ? 'opening' : 'shutting', p: ev.p, target: to, pointerCarried: false };
      }
      return ctx;
    case 'opening':
      if (ev.type === 'SETTLED') return { ...ctx, state: 'open', p: 1, target: null };
      if (ev.type === 'DRAG') return { ...ctx, state: 'pulling', p: ev.p, target: null };
      return ctx;
    case 'shutting':
      if (ev.type === 'SETTLED') return { ...ctx, state: 'shut', p: 0, target: null };
      if (ev.type === 'DRAG') return { ...ctx, state: 'pulling', p: ev.p, target: null };
      return ctx;
    case 'open':
      if (ev.type === 'DRAG') return { ...ctx, state: 'pulling', p: ev.p };
      if (ev.type === 'SHUT_DRAWER') return { ...ctx, state: 'shutting', target: 'shut' };
      if (ev.type === 'LIFT' && ctx.canLift) return { ...ctx, state: 'lifting', ...INSPECT };
      if (ev.type === 'CLOSE') return { ...ctx, state: 'leaving', target: null };
      return ctx;
    case 'lifting':
      if (ev.type === 'LIFTED') return { ...ctx, state: 'lifted' };
      return ctx;
    case 'lifted':
      if (ev.type === 'TURN') return { ...ctx, ...turn(ctx.yaw, ctx.pitch, ev.dx, ev.dy) };
      if (ev.type === 'ZOOM') return { ...ctx, zoom: clampZoom(ev.zoom) };
      if (ev.type === 'RESET') return { ...ctx, ...INSPECT };
      if (ev.type === 'PHOTOS') return { ...ctx, state: 'photos' };
      if (ev.type === 'PUT_BACK') return { ...ctx, state: 'returning' };
      return ctx;
    case 'photos':
      if (ev.type === 'BACK') return { ...ctx, state: 'lifted' };
      return ctx;
    case 'returning':
      if (ev.type === 'RETURNED') return { ...ctx, state: 'open', ...INSPECT };
      return ctx;
    case 'leaving':
      if (ev.type === 'LEFT') return { ...ctx, state: 'wall', p: 0, target: null, pointerCarried: false, ...INSPECT };
      return ctx;
  }
}

/** Esc steps back one state: photos → lifted → open → shut → wall. */
function escape(ctx: ViewContext): ViewContext {
  switch (ctx.state) {
    case 'photos': return reduce(ctx, { type: 'BACK' });
    case 'lifted': return reduce(ctx, { type: 'PUT_BACK' });
    case 'open': return reduce(ctx, { type: 'SHUT_DRAWER' });
    case 'pulling': return { ...ctx, state: 'shutting', target: 'shut', pointerCarried: false };
    case 'shut': return reduce(ctx, { type: 'CLOSE' });
    default: return ctx;
  }
}

/** The states in which the view is on screen (a dialog over the wall). */
export const VIEW_OPEN_STATES: ReadonlySet<ViewState> = new Set(['entering', 'shut', 'pulling', 'opening', 'shutting', 'open', 'lifting', 'lifted', 'photos', 'returning', 'leaving']);
/** The states in which the drawer is open and the frame can be seen. */
export const DRAWER_OPEN_STATES: ReadonlySet<ViewState> = new Set(['open', 'lifting', 'lifted', 'photos', 'returning']);
