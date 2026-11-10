import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest';
import { readFileSync } from 'node:fs';
import { WallStore } from '../../src/data/store';
import { AssetIndex, isManifest, type Manifest } from '../../src/lib/manifest';
import type { Metaobject } from '../../src/lib/types';

// The store (DRAWER-WALL.md, Every drawer is its own thing): the committed records and manifest in, every drawer
// resolved; update() re-resolves and its one `change` event names only the drawers whose resolution changed.
const manifestJson: unknown = JSON.parse(readFileSync(new URL('../../assets/manifest.json', import.meta.url), 'utf8'));

function withField(rec: Metaobject, key: string, value: string): Metaobject {
  return { ...rec, fields: rec.fields.map((f) => (f.key === key ? { ...f, value } : f)) };
}

describe('WallStore', () => {
  let warn: ReturnType<typeof vi.spyOn>;
  beforeAll(() => { warn = vi.spyOn(console, 'warn').mockImplementation(() => {}); });
  afterAll(() => { warn.mockRestore(); });

  const make = () => {
    expect(isManifest(manifestJson)).toBe(true);
    const store = new WallStore(new AssetIndex(manifestJson as Manifest, './assets/'));
    const events: string[][] = [];
    store.addEventListener('change', (ev) => { events.push((ev as CustomEvent<{ changed: string[] }>).detail.changed); });
    return { store, events };
  };

  it('resolves the eight committed drawers, each with its frame and no price (#47)', () => {
    const { store } = make();
    expect(store.resolved).toHaveLength(8);
    for (const b of store.resolved) {
      expect(b.frame?.id).toMatch(/^F0[1-9]$/);
      expect(b.label).not.toHaveProperty('price');
      expect(b.problems).toEqual([]);
    }
    expect(store.bay('drawer_bay/f04')?.state).toBe('available');
    expect(store.bay('drawer_bay/nope')).toBeNull();
  });

  it('update() changes one drawer and names only it', () => {
    const { store, events } = make();
    const f04 = store.record('drawer_bay/f04')!;
    store.update(withField(f04, 'state', 'sold_out'));
    expect(events).toEqual([['drawer_bay/f04']]);
    expect(store.bay('drawer_bay/f04')?.state).toBe('sold_out');
    expect(store.bay('drawer_bay/f04')?.label?.soldOut).toBe(true);
    expect(store.bay('drawer_bay/f01')?.state).toBe('available');
  });

  it('an update that changes nothing names no drawer', () => {
    const { store, events } = make();
    store.update(store.record('drawer_bay/f04')!);
    store.update(store.record('drawer_bay/f01')!);
    expect(events).toEqual([[], []]);
  });

  it('a locked drawer cannot open and a hidden one has no control; the record read back carries the change', () => {
    const { store, events } = make();
    store.update(withField(store.record('drawer_bay/f04')!, 'state', 'locked'));
    expect(store.bay('drawer_bay/f04')?.canOpen).toBe(false);
    expect(store.bay('drawer_bay/f04')?.label?.notYet).toBe(true);
    store.update(withField(store.record('drawer_bay/f04')!, 'state', 'hidden'));
    expect(store.bay('drawer_bay/f04')?.focusable).toBe(false);
    expect(store.record('drawer_bay/f04')?.fields.find((f) => f.key === 'state')?.value).toBe('hidden');
    expect(events).toEqual([['drawer_bay/f04'], ['drawer_bay/f04']]);
  });

  it('the mechanic is tap first until set, and setting it fires once', () => {
    const { store } = make();
    const got: string[] = [];
    store.addEventListener('mechanic', (ev) => { got.push((ev as CustomEvent<{ mechanic: string }>).detail.mechanic); });
    expect(store.mechanic).toBe('tap');
    store.setMechanic('pull');
    store.setMechanic('pull');
    expect(store.mechanic).toBe('pull');
    expect(got).toEqual(['pull']);
  });
});
