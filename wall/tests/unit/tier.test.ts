import { describe, it, expect } from 'vitest';
import { readSignals, tierFor, tierReasons } from '../../src/lib/tier';

describe('tierFor', () => {
  const ok = { webgl2: true, deviceMemory: 8, saveData: false, contextLost: false };
  it('is tier 2 with WebGL 2, enough memory, no Save-Data and a live context', () => {
    expect(tierFor(ok)).toBe(2);
    expect(tierFor({ ...ok, deviceMemory: undefined })).toBe(2);   // Safari reports nothing: not a reason
    expect(tierFor({ ...ok, deviceMemory: 4 })).toBe(2);
  });
  it('falls to tier 1 for each reason', () => {
    expect(tierFor({ ...ok, webgl2: false })).toBe(1);
    expect(tierFor({ ...ok, deviceMemory: 2 })).toBe(1);
    expect(tierFor({ ...ok, saveData: true })).toBe(1);
    expect(tierFor({ ...ok, contextLost: true })).toBe(1);
  });
  it('names the reasons', () => {
    expect(tierReasons(ok)).toEqual([]);
    expect(tierReasons({ webgl2: false, deviceMemory: 2, saveData: true, contextLost: true })).toEqual(['no WebGL 2', 'device memory 2 GB', 'Save-Data', 'WebGL context lost']);
  });
});

describe('readSignals', () => {
  it('reads a browser\'s signals and tolerates a probe that throws', () => {
    expect(readSignals({ deviceMemory: 4, connection: { saveData: true } } as never, () => true)).toEqual({ webgl2: true, deviceMemory: 4, saveData: true, contextLost: false });
    expect(readSignals({}, () => { throw new Error('no canvas'); }, true)).toEqual({ webgl2: false, deviceMemory: undefined, saveData: false, contextLost: true });
  });
});
