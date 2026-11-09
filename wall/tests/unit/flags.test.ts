import { describe, it, expect } from 'vitest';
import { readFlags } from '../../src/lib/flags';

// The switches from the query (the plan's names) and from the hash (the phone link: an Artifact passes a plain #name,
// hyphens joining more than one), the query winning where both speak.
describe('readFlags', () => {
  it('reads nothing as tap first with nothing on', () => {
    expect(readFlags('', '')).toEqual({ mech: 'tap', panel: false, debug: false, open: null, from: { query: [], hash: [] } });
  });
  it('reads the query as the plan names it', () => {
    const f = readFlags('?mech=pull&panel=1&debug=1&open=what-arnie-hid', '');
    expect(f.mech).toBe('pull'); expect(f.panel).toBe(true); expect(f.debug).toBe(true); expect(f.open).toBe('what-arnie-hid');
    expect(f.from.query).toEqual(['mech', 'panel', 'debug', 'open']);
  });
  it('reads a plain hash name, and several joined with hyphens', () => {
    expect(readFlags('', '#pull').mech).toBe('pull');
    expect(readFlags('', '#debug').debug).toBe(true);
    const f = readFlags('', '#pull-debug-panel');
    expect([f.mech, f.debug, f.panel]).toEqual(['pull', true, true]);
    expect(f.from.hash).toEqual(['mech', 'debug', 'panel']);
  });
  it('reads #open-f09 as the frame to open, lower-cased, with other names around it', () => {
    expect(readFlags('', '#open-F09').open).toBe('f09');
    const f = readFlags('', '#debug-open-f09-pull');
    expect(f.open).toBe('f09'); expect(f.debug).toBe(true); expect(f.mech).toBe('pull');
  });
  it('ignores names it does not know and a bare open', () => {
    const f = readFlags('', '#nothing-open');
    expect(f).toEqual({ mech: 'tap', panel: false, debug: false, open: null, from: { query: [], hash: [] } });
  });
  it('lets the query win where both speak, both ways', () => {
    const f = readFlags('?open=F01', '#open-f09-pull');
    expect(f.open).toBe('F01'); expect(f.mech).toBe('pull');
    expect(readFlags('?mech=tap', '#pull').mech).toBe('tap');
    expect(readFlags('?debug=0', '#debug').debug).toBe(false);
    expect(readFlags('?panel=0', '#panel').panel).toBe(false);
  });
  it('takes the frame id after open in the hash, not a handle (handles are hyphenated and the hash splits on hyphens)', () => {
    expect(readFlags('', '#open-what-stevie-saw').open).toBe('what');   // documented: the hash form is #open-f09
    expect(readFlags('', '#open-pull').open).toBe('pull');              // the token after open is always the frame
    expect(readFlags('?open=what-stevie-saw', '').open).toBe('what-stevie-saw');
  });
});
