import { describe, it, expect } from 'vitest';
import * as g from '../../src/lib/gestures';

// The gesture math (DRAWER-WALL.md, "Interaction constants"): release decisions, the rubber band, the clamps.
describe('constants', () => {
  it('are the doc\'s', () => {
    expect([g.TAP_MAX_PX, g.TAP_MAX_MS, g.KNOB_MIN_PX, g.FULL_PULL, g.RUBBER_MAX_PX]).toEqual([8, 400, 44, 0.45, 12]);
    expect([g.RELEASE_VELOCITY, g.RELEASE_POSITION]).toEqual([0.35, 0.5]);
    expect(g.SETTLE_SPRING).toEqual({ stiffness: 180, damping: 26 });
    expect([g.REDUCED_FADE_MS, g.LIFT_MS, g.LIFT_REDUCED_MS]).toEqual([160, 900, 200]);
    expect([g.YAW_PER_PX, g.PITCH_PER_PX, g.PITCH_MIN, g.PITCH_MAX, g.INERTIA_FRICTION]).toEqual([0.4, 0.25, -30, 35, 0.92]);
    expect([g.ZOOM_MIN, g.ZOOM_MAX, g.DOUBLE_TAP_ZOOM, g.WHEEL_STEP]).toEqual([1, 3, 2.2, 1.1]);
    expect([g.HINT_IDLE_MS, g.HAPTIC_MS]).toEqual([1200, 10]);
  });
});

describe('isTap', () => {
  it('is under 8 px and 400 ms', () => {
    expect(g.isTap(3, 4, 120)).toBe(true);
    expect(g.isTap(6, 6, 120)).toBe(false);     // 8.49 px
    expect(g.isTap(0, 0, 400)).toBe(false);     // a long press does nothing
    expect(g.isTap(7.9, 0, 399)).toBe(true);
  });
});

describe('rubberBand', () => {
  it('eases toward at most 12 px and gives nothing for no overshoot', () => {
    expect(g.rubberBand(0)).toBe(0);
    expect(g.rubberBand(-5)).toBe(0);
    expect(g.rubberBand(12)).toBeCloseTo(6);
    expect(g.rubberBand(1e6)).toBeLessThan(12);
    expect(g.rubberBand(1e6)).toBeGreaterThan(11.99);
    expect(g.rubberBand(5)).toBeLessThan(5);
  });
});

describe('pullPosition', () => {
  it('reaches 1 at 45% of the view height', () => {
    expect(g.pullPosition(0, 0.45 * 800, 800)).toBeCloseTo(1);
    expect(g.pullPosition(0, 0.225 * 800, 800)).toBeCloseTo(0.5);
    expect(g.pullPosition(1, -0.45 * 800, 800)).toBeCloseTo(0);
  });
  it('rubber-bands past both ends, never more than 12 px', () => {
    const reach = 0.45 * 800;
    const over = g.pullPosition(0, reach + 200, 800);
    expect(over).toBeGreaterThan(1);
    expect((over - 1) * reach).toBeLessThan(12);
    const under = g.pullPosition(0, -200, 800);
    expect(under).toBeLessThan(0);
    expect(-under * reach).toBeLessThan(12);
  });
  it('survives a zero-height view', () => {
    expect(Number.isFinite(g.pullPosition(0, 10, 0))).toBe(true);
  });
});

describe('releaseDecision', () => {
  it('velocity over 0.35 px/ms wins, either way', () => {
    expect(g.releaseDecision(0.36, 0.1)).toBe('open');
    expect(g.releaseDecision(-0.36, 0.9)).toBe('shut');
  });
  it('otherwise position at or past 0.5 opens', () => {
    expect(g.releaseDecision(0.35, 0.5)).toBe('open');
    expect(g.releaseDecision(0, 0.5)).toBe('open');
    expect(g.releaseDecision(0, 0.499)).toBe('shut');
    expect(g.releaseDecision(-0.3, 0.6)).toBe('open');
  });
});

describe('turn', () => {
  it('yaws 0.4°/px without bound and pitches 0.25°/px within −30 and +35', () => {
    expect(g.turn(0, 0, 10, 0)).toEqual({ yaw: 4, pitch: 0 });
    expect(g.turn(350, 0, 100, 0).yaw).toBeCloseTo(390);
    expect(g.turn(0, 0, 0, 1000).pitch).toBe(35);
    expect(g.turn(0, 0, 0, -1000).pitch).toBe(-30);
    expect(g.turn(0, 10, 0, 8).pitch).toBeCloseTo(12);
  });
});

describe('inertiaStep', () => {
  it('decays by 0.92 a frame and stops when small; none under reduced motion', () => {
    expect(g.inertiaStep(10, false)).toBeCloseTo(9.2);
    expect(g.inertiaStep(0.01, false)).toBe(0);
    expect(g.inertiaStep(10, true)).toBe(0);
  });
});

describe('zoom', () => {
  it('pinch scales directly within 1× to 3×', () => {
    expect(g.pinchZoom(1, 2)).toBe(2);
    expect(g.pinchZoom(2, 2)).toBe(3);
    expect(g.pinchZoom(1, 0.5)).toBe(1);
  });
  it('double tap goes 1× ↔ 2.2×', () => {
    expect(g.doubleTapZoom(1)).toBe(2.2);
    expect(g.doubleTapZoom(2.2)).toBe(1);
    expect(g.doubleTapZoom(1.5)).toBe(1);
  });
  it('the wheel steps 1.1× each way, in by scrolling up', () => {
    expect(g.wheelZoom(1, -100)).toBeCloseTo(1.1);
    expect(g.wheelZoom(1.1, 100)).toBeCloseTo(1);
    expect(g.wheelZoom(1, 100)).toBe(1);
    expect(g.wheelZoom(3, -100)).toBe(3);
    expect(g.wheelZoom(2, 0)).toBe(2);
  });
  it('zooming about a point keeps that point still', () => {
    const pan = g.zoomAbout({ x: 0, y: 0 }, 1, 2, 100, 50);
    expect(pan).toEqual({ x: -100, y: -50 });
    const back = g.zoomAbout(pan, 2, 1, 100, 50);
    expect(back.x).toBeCloseTo(0);
    expect(back.y).toBeCloseTo(0);
  });
});
