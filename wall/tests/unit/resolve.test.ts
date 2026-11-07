import { describe, it, expect } from 'vitest';
import { priceText, resolveBay, resolveWall } from '../../src/lib/resolve';
import { ALL_ASSETS, FRAMES, NO_ASSETS, NO_LIFT, bay } from './fixtures';

// Every case of "How a drawer's state is resolved" (DRAWER-WALL.md), every override, every missing or unknown value.
describe('resolveBay', () => {
  it('available: lit, the name and the price, opens, lifts when the assets exist', () => {
    const r = resolveBay(bay(), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('available');
    expect(r.light).toBe('lit');
    expect(r.canOpen).toBe(true);
    expect(r.canLift).toBe(true);
    expect(r.focusable).toBe(true);
    expect(r.label).toEqual({ lookNumber: '09', name: 'What Stevie Saw', price: '$100', soldOut: false, notYet: false });
    expect(r.problems).toEqual([]);
  });

  it('sold_out: dark, the name, the price and sold out; it opens and the frame can be lifted', () => {
    const r = resolveBay(bay({ state: 'sold_out' }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('sold_out');
    expect(r.light).toBe('dark');
    expect(r.canOpen).toBe(true);
    expect(r.canLift).toBe(true);
    expect(r.label).toEqual({ lookNumber: '09', name: 'What Stevie Saw', price: '$100', soldOut: true, notYet: false });
  });

  it('locked: dark, not yet with the look number and the price, no name, does not open', () => {
    const r = resolveBay(bay({ state: 'locked' }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('locked');
    expect(r.light).toBe('dark');
    expect(r.canOpen).toBe(false);
    expect(r.canLift).toBe(false);
    expect(r.focusable).toBe(true);
    expect(r.label).toEqual({ lookNumber: '09', name: null, price: '$100', soldOut: false, notYet: true });
  });

  it('hidden: dark, no label, not focusable, does not open', () => {
    const r = resolveBay(bay({ state: 'hidden' }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('hidden');
    expect(r.light).toBe('dark');
    expect(r.label).toBeNull();
    expect(r.focusable).toBe(false);
    expect(r.canOpen).toBe(false);
    expect(r.canLift).toBe(false);
    expect(r.problems).toEqual([]);
  });

  it('no frame: hidden, and logged', () => {
    const r = resolveBay(bay({ frame: null }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('hidden');
    expect(r.label).toBeNull();
    expect(r.problems).toEqual(['drawer_bay/f09: no frame']);
  });

  it('an unknown frame id: hidden, and logged', () => {
    const r = resolveBay(bay({ frame: 'F07' }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('hidden');
    expect(r.frame).toBeNull();
    expect(r.problems).toEqual(['drawer_bay/f09: unknown frame "F07"']);
  });

  it('a frame id that is a prototype property is not a frame', () => {
    const r = resolveBay(bay({ frame: 'constructor' }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('hidden');
    expect(r.problems).toEqual(['drawer_bay/f09: unknown frame "constructor"']);
  });

  it('no state: hidden, and logged', () => {
    const r = resolveBay(bay({ state: null }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('hidden');
    expect(r.problems).toEqual(['drawer_bay/f09: no state']);
  });

  it('an unknown state: hidden, and logged', () => {
    const r = resolveBay(bay({ state: 'coming_soon' }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('hidden');
    expect(r.problems).toEqual(['drawer_bay/f09: unknown state "coming_soon"']);
  });

  it('an unknown light: hidden, and logged', () => {
    const r = resolveBay(bay({ light: 'bright' }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('hidden');
    expect(r.problems).toEqual(['drawer_bay/f09: unknown light "bright"']);
  });

  it('a missing light reads as auto', () => {
    expect(resolveBay(bay({ light: null }), FRAMES, ALL_ASSETS).light).toBe('lit');
    expect(resolveBay(bay({ light: null, state: 'sold_out' }), FRAMES, ALL_ASSETS).light).toBe('dark');
  });

  it('several problems are all logged', () => {
    const r = resolveBay(bay({ frame: null, state: 'x', light: 'y' }), FRAMES, ALL_ASSETS);
    expect(r.problems).toHaveLength(3);
  });

  describe('light overrides the seam light only', () => {
    it('lit on a sold-out drawer lights it and changes nothing else', () => {
      const r = resolveBay(bay({ state: 'sold_out', light: 'lit' }), FRAMES, ALL_ASSETS);
      expect(r.light).toBe('lit');
      expect(r.canOpen).toBe(true);
      expect(r.label?.soldOut).toBe(true);
    });
    it('dark on an available drawer darkens it and it still opens', () => {
      const r = resolveBay(bay({ light: 'dark' }), FRAMES, ALL_ASSETS);
      expect(r.light).toBe('dark');
      expect(r.canOpen).toBe(true);
      expect(r.state).toBe('available');
    });
    it('lit on a locked drawer lights it; it still does not open', () => {
      const r = resolveBay(bay({ state: 'locked', light: 'lit' }), FRAMES, ALL_ASSETS);
      expect(r.light).toBe('lit');
      expect(r.canOpen).toBe(false);
    });
    it('a hidden drawer stays dark whatever light says', () => {
      expect(resolveBay(bay({ state: 'hidden', light: 'lit' }), FRAMES, ALL_ASSETS).light).toBe('dark');
    });
  });

  describe('canOpen and canLift follow the assets', () => {
    it('no sequence: cannot open, cannot lift, but the label and the light stay', () => {
      const r = resolveBay(bay(), FRAMES, NO_ASSETS);
      expect(r.canOpen).toBe(false);
      expect(r.canLift).toBe(false);
      expect(r.light).toBe('lit');
      expect(r.label?.name).toBe('What Stevie Saw');
    });
    it('a sequence but no GLB or still: opens, does not lift', () => {
      const r = resolveBay(bay(), FRAMES, NO_LIFT);
      expect(r.canOpen).toBe(true);
      expect(r.canLift).toBe(false);
    });
  });

  it('locked with no price in the facts: not yet and the look number, no price, nothing made up', () => {
    const frames = { ...FRAMES, F09: { ...FRAMES.F09, price: null } };
    expect(resolveBay(bay({ state: 'locked' }), frames, ALL_ASSETS).label).toEqual({ lookNumber: '09', name: null, price: null, soldOut: false, notYet: true });
  });

  it('sold out with a sequence but no lift assets: opens, does not lift', () => {
    const r = resolveBay(bay({ state: 'sold_out' }), FRAMES, NO_LIFT);
    expect(r.canOpen).toBe(true);
    expect(r.canLift).toBe(false);
    expect(r.light).toBe('dark');
  });

  it('hidden with an unknown frame: hidden, and the frame logged', () => {
    const r = resolveBay(bay({ state: 'hidden', frame: 'F07' }), FRAMES, ALL_ASSETS);
    expect(r.state).toBe('hidden');
    expect(r.problems).toEqual(['drawer_bay/f09: unknown frame "F07"']);
  });

  it('a facts record with null name and look number renders neither', () => {
    const frames = { ...FRAMES, F09: { ...FRAMES.F09, lookNumber: null, name: null } };
    expect(resolveBay(bay(), frames, ALL_ASSETS).label).toEqual({ lookNumber: null, name: null, price: '$100', soldOut: false, notYet: false });
  });

  describe('a missing value renders nothing', () => {
    it('no price in the facts: the label has no price, never a made-up one', () => {
      const frames = { ...FRAMES, F09: { ...FRAMES.F09, price: null } };
      expect(resolveBay(bay(), frames, ALL_ASSETS).label?.price).toBeNull();
    });
    it('no look number or name: nulls', () => {
      const frames = { ...FRAMES, F09: { ...FRAMES.F09, lookNumber: '', name: '' } };
      const label = resolveBay(bay(), frames, ALL_ASSETS).label;
      expect(label?.lookNumber).toBeNull();
      expect(label?.name).toBeNull();
    });
  });
});

describe('priceText', () => {
  it('formats the frames\' price from the record', () => {
    expect(priceText({ amount: '100.00', currencyCode: 'USD' })).toBe('$100');
    expect(priceText({ amount: '100', currencyCode: 'USD' })).toBe('$100');
    expect(priceText({ amount: '99.50', currencyCode: 'USD' })).toBe('$99.50');
    expect(priceText({ amount: '100.00', currencyCode: 'EUR' })).toBe('EUR 100');
  });
  it('renders nothing for a missing or malformed price', () => {
    expect(priceText(null)).toBeNull();
    expect(priceText({ amount: 'one hundred', currencyCode: 'USD' })).toBeNull();
    expect(priceText({ amount: '', currencyCode: 'USD' })).toBeNull();
  });
});

describe('resolveWall', () => {
  it('resolves every drawer in wall order', () => {
    const order = [bay({ id: 'drawer_bay/f01', frame: 'F01' }), bay({ id: 'drawer_bay/f09', state: 'locked' })];
    const r = resolveWall(order, FRAMES, ALL_ASSETS);
    expect(r.map((b) => [b.id, b.state])).toEqual([['drawer_bay/f01', 'available'], ['drawer_bay/f09', 'locked']]);
  });
});
