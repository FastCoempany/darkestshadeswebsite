// The adapter (DRAWER-WALL.md, "Every drawer is its own thing"): records in metaobject shape in, typed drawers out.
// JSON now (wall/data/wall.json); a store's Storefront API later, through the same function. The adapter is
// tolerant and honest: a missing field is null, an unknown field is ignored, a reference that points nowhere is
// reported; it never fills a value in.
import type { BayWallRecord, DrawerBayRecord, Metaobject, MetaobjectField } from '../lib/types';

export interface RecordsFile {
  records: Metaobject[];
}

export interface WallRecords {
  wall: BayWallRecord | null;
  /** The drawer records, by id. */
  bays: Map<string, DrawerBayRecord>;
  /** The drawers in wall order: the wall's `bays` list resolved; an id that points nowhere is left out and reported. */
  order: DrawerBayRecord[];
  problems: string[];
}

export function field(record: Metaobject, key: string): MetaobjectField | null {
  if (!Array.isArray(record.fields)) return null;
  return record.fields.find((f) => f && f.key === key) ?? null;
}

export function textField(record: Metaobject, key: string): string | null {
  const f = field(record, key);
  return f && typeof f.value === 'string' ? f.value : null;
}

/** A list field's ids: its value is a JSON array of strings; anything else is an empty list and a problem. */
export function listField(record: Metaobject, key: string, problems: string[]): string[] {
  const f = field(record, key);
  if (!f || f.value == null) return [];
  try {
    const parsed: unknown = JSON.parse(f.value);
    if (Array.isArray(parsed) && parsed.every((v) => typeof v === 'string')) return parsed as string[];
    problems.push(`${record.id}: ${key} is not a list of ids`);
  } catch {
    problems.push(`${record.id}: ${key} is not JSON`);
  }
  return [];
}

export function toDrawerBay(record: Metaobject): DrawerBayRecord {
  return {
    id: record.id,
    handle: record.handle,
    frame: textField(record, 'frame'),
    state: textField(record, 'state'),
    light: textField(record, 'light'),
    note: textField(record, 'note'),
  };
}

export function toBayWall(record: Metaobject, problems: string[]): BayWallRecord {
  return {
    id: record.id,
    handle: record.handle,
    bays: listField(record, 'bays', problems),
    knobStyle: textField(record, 'knob_style'),
    renderSet: textField(record, 'render_set'),
  };
}

function isMetaobject(x: unknown): x is Metaobject {
  return !!x && typeof x === 'object' && typeof (x as Metaobject).id === 'string' && typeof (x as Metaobject).type === 'string';
}

/** The records file (or a store's answer in the same shape) as typed records. `wallHandle` picks the bay_wall
 * record when a store holds more than one. */
export function readRecords(input: unknown, wallHandle = 'frames'): WallRecords {
  const problems: string[] = [];
  const list = (input && typeof input === 'object' && Array.isArray((input as RecordsFile).records)) ? (input as RecordsFile).records : [];
  if (!list.length) problems.push('no records');
  const bays = new Map<string, DrawerBayRecord>();
  let wall: BayWallRecord | null = null;
  for (const r of list) {
    if (!isMetaobject(r)) { problems.push('a record without an id or a type'); continue; }
    if (r.type === 'drawer_bay') {
      if (bays.has(r.id)) problems.push(`${r.id}: listed twice`);
      bays.set(r.id, toDrawerBay(r));
    } else if (r.type === 'bay_wall') {
      if (r.handle === wallHandle || !wall) wall = toBayWall(r, problems);
    } else {
      problems.push(`${r.id}: unknown record type "${r.type}"`);
    }
  }
  const order: DrawerBayRecord[] = [];
  if (!wall) problems.push(`no bay_wall record with handle "${wallHandle}"`);
  for (const id of wall?.bays ?? []) {
    const bay = bays.get(id);
    if (bay) order.push(bay);
    else problems.push(`${wall?.id}: bays lists ${id}, which is not a drawer_bay record`);
  }
  return { wall, bays, order, problems };
}

/** A changed record (the panel now, a store later) applied to the set: the same drawer, new values. */
export function withRecord(records: WallRecords, record: Metaobject): WallRecords {
  if (record.type !== 'drawer_bay') return records;
  const bays = new Map(records.bays);
  bays.set(record.id, toDrawerBay(record));
  const order = (records.wall?.bays ?? []).map((id) => bays.get(id)).filter((b): b is DrawerBayRecord => !!b);
  return { ...records, bays, order };
}
