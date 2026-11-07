import { describe, it, expect } from 'vitest';
import { springSettled, springStep, springTrace } from '../../src/lib/spring';
import { SETTLE_SPRING } from '../../src/lib/gestures';

describe('the settle spring (180, 26)', () => {
  it('reaches its target and settles within a second, without overshooting much', () => {
    const trace = springTrace(0, 1, SETTLE_SPRING);
    expect(trace.length * 16).toBeLessThan(1000);
    expect(Math.max(...trace)).toBeLessThan(1.05);
    expect(trace[trace.length - 1]).toBeCloseTo(1, 2);
  });
  it('is monotone enough to read as a drawer sliding home', () => {
    const trace = springTrace(1, 0, SETTLE_SPRING);
    let decreasing = 0;
    for (let i = 1; i < trace.length; i++) if (trace[i]! <= trace[i - 1]! + 1e-9) decreasing++;
    expect(decreasing / (trace.length - 1)).toBeGreaterThan(0.9);
  });
  it('steps in substeps so a long frame does not blow up', () => {
    const s = springStep({ x: 0, v: 0 }, 1, 500, SETTLE_SPRING);
    expect(Number.isFinite(s.x)).toBe(true);
    expect(s.x).toBeGreaterThan(0.9);
    expect(s.x).toBeLessThan(1.1);
  });
  it('knows when it is settled', () => {
    expect(springSettled({ x: 1, v: 0 }, 1)).toBe(true);
    expect(springSettled({ x: 0.9, v: 0 }, 1)).toBe(false);
    expect(springSettled({ x: 1, v: 1 }, 1)).toBe(false);
  });
  it('ignores a negative dt', () => {
    expect(springStep({ x: 0.5, v: 2 }, 1, -10, SETTLE_SPRING)).toEqual({ x: 0.5, v: 2 });
  });
});
