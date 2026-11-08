// The wall's store: the records (wall/data/wall.json now, a store later) through the adapter, the asset manifest
// through its index, the frames' facts, and every drawer resolved; one `change` event names the drawers whose
// resolution changed, so each <drawer-bay> re-renders on its own (DRAWER-WALL.md, Every drawer is its own thing).
import recordsJson from '../../data/wall.json';
import { FRAMES } from './frames';
import { readRecords, withRecord, type WallRecords } from './adapter';
import { AssetIndex, isManifest, type Manifest } from '../lib/manifest';
import { resolveWall } from '../lib/resolve';
import { problem, log } from '../lib/log';
import type { Metaobject, ResolvedBay } from '../lib/types';

export type Mechanic = 'tap' | 'pull';

export class WallStore extends EventTarget {
  records: WallRecords;
  resolved: ResolvedBay[] = [];
  mechanic: Mechanic = 'tap';

  constructor(readonly assets: AssetIndex, input: unknown = recordsJson) {
    super();
    this.records = readRecords(input);
    for (const p of this.records.problems) problem(p);
    this.resolve();
  }

  /** The manifest fetched from the assets folder (relative to the page), or an empty index when it is missing. */
  static async load(base = './assets/'): Promise<WallStore> {
    let manifest: Manifest = { renderSet: 'none', assets: [] };
    try {
      const r = await fetch(base + 'manifest.json');
      const j: unknown = r.ok ? await r.json() : null;
      if (isManifest(j)) manifest = j;
      else problem(`manifest: ${base}manifest.json is missing or not a manifest`);
    } catch (e) {
      problem(`manifest: ${String(e)}`);
    }
    return new WallStore(new AssetIndex(manifest, base));
  }

  get knobStyle(): 'black-relief' | 'gold' | 'plain' {
    const k = this.records.wall?.knobStyle;
    return k === 'gold' || k === 'plain' ? k : 'black-relief';
  }

  private resolve(): string[] {
    const before = new Map(this.resolved.map((b) => [b.id, JSON.stringify(b)]));
    this.resolved = resolveWall(this.records.order, FRAMES, this.assets);
    const changed: string[] = [];
    for (const b of this.resolved) {
      for (const p of b.problems) problem(p);
      if (before.get(b.id) !== JSON.stringify(b)) changed.push(b.id);
    }
    return changed;
  }

  bay(id: string): ResolvedBay | null {
    return this.resolved.find((b) => b.id === id) ?? null;
  }

  /** A drawer's record changed (the panel now, a store later): re-resolve, tell only the drawers that changed. */
  update(record: Metaobject): void {
    this.records = withRecord(this.records, record);
    const changed = this.resolve();
    log('records.update', { id: record.id, changed });
    this.dispatchEvent(new CustomEvent('change', { detail: { changed } }));
  }

  /** The record of a drawer, in metaobject shape, for the panel to edit. */
  record(id: string): Metaobject | null {
    const b = this.records.bays.get(id);
    if (!b) return null;
    return { id: b.id, handle: b.handle, type: 'drawer_bay', fields: [
      { key: 'frame', type: 'single_line_text_field', value: b.frame },
      { key: 'state', type: 'single_line_text_field', value: b.state },
      { key: 'light', type: 'single_line_text_field', value: b.light },
      { key: 'note', type: 'multi_line_text_field', value: b.note },
    ] };
  }

  setMechanic(m: Mechanic): void {
    if (m === this.mechanic) return;
    this.mechanic = m;
    log('mechanic', { mechanic: m });
    this.dispatchEvent(new CustomEvent('mechanic', { detail: { mechanic: m } }));
  }
}
