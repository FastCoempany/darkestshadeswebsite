// Fixtures for the logic tests: frame facts in the shape the wall reads them, and records in metaobject shape.
import type { AssetAvailability, DrawerBayRecord, FrameFacts, FrameId, Metaobject } from '../../src/lib/types';

// The eight frames as content/products/ names them (06-products.md): id, handle, look number, name. No price (#47).
export const FRAMES: Record<FrameId, FrameFacts> = {
  F01: facts('F01', 'lou-went-underground', '01', 'Lou Went Underground'),
  F02: facts('F02', 'holly-wore-them-to-breakfast', '02', 'Holly Wore Them to Breakfast'),
  F03: facts('F03', 'roy-forgot-the-clear-ones', '03', 'Roy Forgot the Clear Ones'),
  F04: facts('F04', 'k-was-never-here', '04', 'K Was Never Here'),
  F05: facts('F05', 'jackie-gave-them-nothing', '05', 'Jackie Gave Them Nothing'),
  F06: facts('F06', 'what-anna-thought', '06', 'What Anna Thought'),
  F08: facts('F08', 'what-arnie-hid', '08', 'What Arnie Hid'),
  F09: facts('F09', 'what-stevie-saw', '09', 'What Stevie Saw'),
};

function facts(id: FrameId, handle: string, lookNumber: string, name: string): FrameFacts {
  return { id, handle, lookNumber, name };
}

export function bay(over: Partial<DrawerBayRecord> = {}): DrawerBayRecord {
  return { id: 'drawer_bay/f09', handle: 'f09', frame: 'F09', state: 'available', light: 'auto', note: '', ...over };
}

export const ALL_ASSETS: AssetAvailability = { hasSequence: () => true, hasLift: () => true };
export const NO_LIFT: AssetAvailability = { hasSequence: () => true, hasLift: () => false };
export const NO_ASSETS: AssetAvailability = { hasSequence: () => false, hasLift: () => false };

export function metaobject(id: string, type: string, fields: Record<string, string | null>, fieldTypes: Record<string, string> = {}): Metaobject {
  return {
    id, handle: id.split('/')[1] ?? id, type,
    fields: Object.entries(fields).map(([key, value]) => ({ key, type: fieldTypes[key] ?? 'single_line_text_field', value })),
  };
}

export function recordsFile(bays: Array<Record<string, string | null>>, wallOver: Partial<Record<'bays' | 'knob_style' | 'render_set', string | null>> = {}) {
  const ids = bays.map((b) => `drawer_bay/${String(b.frame ?? 'x').toLowerCase()}`);
  return {
    records: [
      metaobject('bay_wall/frames', 'bay_wall', { bays: JSON.stringify(ids), knob_style: 'black-relief', render_set: 'wall-v1', ...wallOver }, { bays: 'list.metaobject_reference' }),
      ...bays.map((b, i) => metaobject(ids[i] ?? `drawer_bay/${i}`, 'drawer_bay', { frame: null, state: null, light: null, note: null, ...b }, { note: 'multi_line_text_field' })),
    ],
  };
}
