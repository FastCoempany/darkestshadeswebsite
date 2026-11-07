import { describe, it, expect } from 'vitest';
import { initialContext, reduce, type ViewContext, type ViewEvent, type ViewState, DRAWER_OPEN_STATES, VIEW_OPEN_STATES } from '../../src/lib/machine';

// Every transition of the drawer's state machine (DRAWER-WALL.md), every impossible one, Esc stepping back, the pull
// carried from the wall, and a record changing mid-view.
const go = (ctx: ViewContext, ...events: ViewEvent[]): ViewContext => events.reduce(reduce, ctx);
const at = (state: ViewState, over: Partial<ViewContext> = {}): ViewContext => ({ ...initialContext(true, true), state, ...over });

describe('the happy path', () => {
  it('wall → entering → shut → pulling → opening → open → lifting → lifted → photos → lifted → returning → open → shutting → shut → leaving → wall', () => {
    let c = initialContext(true, true);
    const steps: Array<[ViewEvent, ViewState]> = [
      [{ type: 'OPEN' }, 'entering'], [{ type: 'ENTERED' }, 'shut'], [{ type: 'DRAG', p: 0.2 }, 'pulling'], [{ type: 'DRAG', p: 0.7 }, 'pulling'],
      [{ type: 'RELEASE', v: 0, p: 0.7 }, 'opening'], [{ type: 'SETTLED' }, 'open'], [{ type: 'LIFT' }, 'lifting'], [{ type: 'LIFTED' }, 'lifted'],
      [{ type: 'PHOTOS' }, 'photos'], [{ type: 'BACK' }, 'lifted'], [{ type: 'PUT_BACK' }, 'returning'], [{ type: 'RETURNED' }, 'open'],
      [{ type: 'SHUT_DRAWER' }, 'shutting'], [{ type: 'SETTLED' }, 'shut'], [{ type: 'CLOSE' }, 'leaving'], [{ type: 'LEFT' }, 'wall'],
    ];
    for (const [ev, state] of steps) { c = reduce(c, ev); expect(c.state, ev.type).toBe(state); }
    expect(c.p).toBe(0);
  });
});

describe('each state', () => {
  it('wall: OPEN enters only if canOpen; a knob pull carries the pointer', () => {
    expect(reduce(initialContext(true, true), { type: 'OPEN' }).state).toBe('entering');
    expect(reduce(initialContext(true, true), { type: 'OPEN', pointer: { x: 1, y: 2 } }).pointerCarried).toBe(true);
    expect(reduce(initialContext(true, true), { type: 'OPEN' }).pointerCarried).toBe(false);
    const locked = initialContext(false, false);
    expect(reduce(locked, { type: 'OPEN' })).toBe(locked);
  });
  it('shut: DRAG pulls, OPEN_DRAWER opens, CLOSE leaves', () => {
    expect(reduce(at('shut'), { type: 'DRAG', p: 0.1 })).toMatchObject({ state: 'pulling', p: 0.1 });
    expect(reduce(at('shut'), { type: 'OPEN_DRAWER' })).toMatchObject({ state: 'opening', target: 'open' });
    expect(reduce(at('shut'), { type: 'CLOSE' })).toMatchObject({ state: 'leaving' });
  });
  it('pulling: DRAG moves, RELEASE decides by velocity then position', () => {
    expect(reduce(at('pulling', { p: 0.3 }), { type: 'DRAG', p: 0.4 }).p).toBe(0.4);
    expect(reduce(at('pulling'), { type: 'RELEASE', v: 0.5, p: 0.1 }).state).toBe('opening');     // fast down wins
    expect(reduce(at('pulling'), { type: 'RELEASE', v: -0.5, p: 0.9 }).state).toBe('shutting');   // fast up wins
    expect(reduce(at('pulling'), { type: 'RELEASE', v: 0.1, p: 0.5 }).state).toBe('opening');     // slow: position
    expect(reduce(at('pulling'), { type: 'RELEASE', v: 0.1, p: 0.49 }).state).toBe('shutting');
  });
  it('opening and shutting: SETTLED lands; a new DRAG catches the drawer mid-settle', () => {
    expect(reduce(at('opening'), { type: 'SETTLED' })).toMatchObject({ state: 'open', p: 1 });
    expect(reduce(at('shutting'), { type: 'SETTLED' })).toMatchObject({ state: 'shut', p: 0 });
    expect(reduce(at('opening'), { type: 'DRAG', p: 0.6 })).toMatchObject({ state: 'pulling', p: 0.6 });
    expect(reduce(at('shutting'), { type: 'DRAG', p: 0.2 })).toMatchObject({ state: 'pulling', p: 0.2 });
  });
  it('open: DRAG pulls, SHUT_DRAWER shuts, LIFT lifts only if canLift, CLOSE leaves', () => {
    expect(reduce(at('open'), { type: 'DRAG', p: 0.9 }).state).toBe('pulling');
    expect(reduce(at('open'), { type: 'SHUT_DRAWER' })).toMatchObject({ state: 'shutting', target: 'shut' });
    expect(reduce(at('open'), { type: 'LIFT' }).state).toBe('lifting');
    const noLift = at('open', { canLift: false });
    expect(reduce(noLift, { type: 'LIFT' })).toBe(noLift);
    expect(reduce(at('open'), { type: 'CLOSE' }).state).toBe('leaving');
  });
  it('lifted: TURN turns with pitch clamped, ZOOM clamps, RESET resets, PHOTOS and PUT_BACK move on', () => {
    const t = reduce(at('lifted'), { type: 'TURN', dx: 100, dy: -400 });
    expect(t.yaw).toBeCloseTo(40);
    expect(t.pitch).toBe(-30);
    expect(reduce(at('lifted'), { type: 'ZOOM', zoom: 9 }).zoom).toBe(3);
    expect(reduce(at('lifted'), { type: 'ZOOM', zoom: 0.2 }).zoom).toBe(1);
    expect(reduce(at('lifted', { yaw: 50, pitch: 10, zoom: 2 }), { type: 'RESET' })).toMatchObject({ yaw: 0, pitch: 0, zoom: 1, state: 'lifted' });
    expect(reduce(at('lifted'), { type: 'PHOTOS' }).state).toBe('photos');
    expect(reduce(at('lifted'), { type: 'PUT_BACK' }).state).toBe('returning');
  });
  it('photos: BACK returns to lifted', () => {
    expect(reduce(at('photos'), { type: 'BACK' }).state).toBe('lifted');
  });
  it('returning: RETURNED lands in open with the pose reset', () => {
    expect(reduce(at('returning', { yaw: 30, zoom: 2 }), { type: 'RETURNED' })).toMatchObject({ state: 'open', yaw: 0, zoom: 1 });
  });
  it('leaving: LEFT lands on the wall with everything reset', () => {
    expect(reduce(at('leaving', { p: 1, yaw: 30, pointerCarried: true }), { type: 'LEFT' })).toMatchObject({ state: 'wall', p: 0, yaw: 0, pointerCarried: false });
  });
});

describe('every impossible transition returns the same context', () => {
  const all: ViewEvent['type'][] = ['OPEN', 'ENTERED', 'DRAG', 'RELEASE', 'OPEN_DRAWER', 'SHUT_DRAWER', 'CLOSE', 'SETTLED', 'LIFT', 'LIFTED', 'TURN', 'ZOOM', 'RESET', 'PHOTOS', 'BACK', 'PUT_BACK', 'RETURNED', 'LEFT'];
  const allowed: Record<ViewState, ViewEvent['type'][]> = {
    wall: ['OPEN'], entering: ['ENTERED'], shut: ['DRAG', 'OPEN_DRAWER', 'CLOSE'], pulling: ['DRAG', 'RELEASE'],
    opening: ['SETTLED', 'DRAG'], shutting: ['SETTLED', 'DRAG'], open: ['DRAG', 'SHUT_DRAWER', 'LIFT', 'CLOSE'],
    lifting: ['LIFTED'], lifted: ['TURN', 'ZOOM', 'RESET', 'PHOTOS', 'PUT_BACK'], photos: ['BACK'], returning: ['RETURNED'], leaving: ['LEFT'],
  };
  const make = (type: ViewEvent['type']): ViewEvent => {
    switch (type) {
      case 'DRAG': return { type, p: 0.5 };
      case 'RELEASE': return { type, v: 0, p: 0.5 };
      case 'TURN': return { type, dx: 1, dy: 1 };
      case 'ZOOM': return { type, zoom: 2 };
      case 'RECORD': return { type, canOpen: true, canLift: true };
      default: return { type } as ViewEvent;
    }
  };
  for (const state of Object.keys(allowed) as ViewState[]) {
    for (const type of all) {
      if (allowed[state].includes(type)) continue;
      it(`${type} in ${state} does nothing`, () => {
        const ctx = at(state);
        expect(reduce(ctx, make(type))).toBe(ctx);
      });
    }
  }
  it('LIFT from shut and OPEN on a locked drawer, named in the doc, do nothing', () => {
    const shut = at('shut');
    expect(reduce(shut, { type: 'LIFT' })).toBe(shut);
    const locked = initialContext(false, false);
    expect(reduce(locked, { type: 'OPEN' })).toBe(locked);
  });
});

describe('Esc steps back', () => {
  it('photos → lifted → returning (put back) and open → shutting → shut → leaving', () => {
    expect(reduce(at('photos'), { type: 'ESC' }).state).toBe('lifted');
    expect(reduce(at('lifted'), { type: 'ESC' }).state).toBe('returning');
    expect(reduce(at('open'), { type: 'ESC' }).state).toBe('shutting');
    expect(reduce(at('shut'), { type: 'ESC' }).state).toBe('leaving');
    expect(reduce(at('pulling', { p: 0.4 }), { type: 'ESC' })).toMatchObject({ state: 'shutting', target: 'shut' });
  });
  it('does nothing mid-transition or on the wall', () => {
    for (const s of ['wall', 'entering', 'opening', 'shutting', 'lifting', 'returning', 'leaving'] as ViewState[]) {
      const ctx = at(s);
      expect(reduce(ctx, { type: 'ESC' }), s).toBe(ctx);
    }
  });
});

describe('pull first carries the pointer', () => {
  it('the same drag goes on as DRAG without a second touch, and a release clears the carry', () => {
    let c = go(initialContext(true, true), { type: 'OPEN', pointer: { x: 10, y: 20 } }, { type: 'ENTERED' });
    expect(c.pointerCarried).toBe(true);
    c = reduce(c, { type: 'DRAG', p: 0.3 });
    expect(c).toMatchObject({ state: 'pulling', p: 0.3, pointerCarried: true });
    c = reduce(c, { type: 'RELEASE', v: 1, p: 0.3 });
    expect(c).toMatchObject({ state: 'opening', pointerCarried: false });
  });
});

describe('a record changing mid-view', () => {
  it('closes the view only if the drawer can no longer open', () => {
    expect(reduce(at('lifted'), { type: 'RECORD', canOpen: false, canLift: false })).toMatchObject({ state: 'leaving', canOpen: false });
    expect(reduce(at('open'), { type: 'RECORD', canOpen: true, canLift: false })).toMatchObject({ state: 'open', canLift: false });
    expect(reduce(at('shut'), { type: 'RECORD', canOpen: true, canLift: true }).state).toBe('shut');
  });
  it('updates the flags on the wall without opening anything', () => {
    expect(reduce(initialContext(false, false), { type: 'RECORD', canOpen: true, canLift: true })).toMatchObject({ state: 'wall', canOpen: true, canLift: true });
    expect(reduce(initialContext(true, true), { type: 'RECORD', canOpen: false, canLift: false })).toMatchObject({ state: 'wall', canOpen: false });
  });
  it('a view already leaving keeps leaving', () => {
    expect(reduce(at('leaving'), { type: 'RECORD', canOpen: false, canLift: false }).state).toBe('leaving');
  });
});

describe('the state sets', () => {
  it('name the view-open and drawer-open states', () => {
    expect(VIEW_OPEN_STATES.has('wall')).toBe(false);
    expect(VIEW_OPEN_STATES.has('shut')).toBe(true);
    expect(DRAWER_OPEN_STATES.has('open')).toBe(true);
    expect(DRAWER_OPEN_STATES.has('shut')).toBe(false);
  });
});
