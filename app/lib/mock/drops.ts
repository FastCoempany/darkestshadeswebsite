/**
 * Drops from content/drops/*.json (a `drop` metaobject in Shopify, docs/brief/06-products.md).
 * Every field the founder has not set is null, and the UI shows nothing for it.
 */
import drop001 from '../../../content/drops/drop-001.json';
import type {Drop, DropState, FrameId, StorefrontMetaobject} from './types';

interface DropFile {
  number: string;
  state: string;
  startsAt: string | null;
  endsAt: string | null;
  timezone: string;
  frames: string[];
  pairsPerFrame: number | null;
  limitPerCustomer: number | null;
  earlyAccess?: {enabled: boolean; hoursBeforePublic?: number | null};
  copy?: {statement: string | null};
}

function state(v: string): DropState {
  if (v === 'live' || v === 'ended' || v === 'announced') return v;
  if (v === 'sold-out' || v === 'soldOut' || v === 'sold_out') return 'sold-out';
  throw new Error(`Unknown drop state "${v}"`);
}

export function toDrop(file: DropFile): Drop {
  return {
    number: file.number,
    state: state(file.state),
    startsAt: file.startsAt,
    endsAt: file.endsAt,
    timezone: file.timezone,
    frames: file.frames as FrameId[],
    pairsPerFrame: file.pairsPerFrame,
    limitPerCustomer: file.limitPerCustomer,
    earlyAccess: {
      enabled: file.earlyAccess?.enabled ?? false,
      hoursBeforePublic: file.earlyAccess?.hoursBeforePublic ?? null,
    },
    statement: file.copy?.statement ?? null,
  };
}

export const drops: Drop[] = [toDrop(drop001)];

/**
 * The state the drop is in at `now`, given its set times: an announced drop whose start has passed is
 * live; a drop whose end has passed has ended. Without times the stored state stands.
 */
export function effectiveState(drop: Drop, now: Date = new Date()): DropState {
  if (drop.state === 'sold-out' || drop.state === 'ended') return drop.state;
  const start = drop.startsAt ? Date.parse(drop.startsAt) : NaN;
  const end = drop.endsAt ? Date.parse(drop.endsAt) : NaN;
  if (Number.isFinite(end) && now.getTime() >= end) return 'ended';
  if (drop.state === 'announced' && Number.isFinite(start) && now.getTime() >= start) return 'live';
  return drop.state;
}

/** The drop `/drop` points at: the live one, else the next announced, else the most recent. */
export function currentDrop(all: Drop[] = drops, now: Date = new Date()): Drop | null {
  const withState = all.map((d) => ({...d, state: effectiveState(d, now)}));
  return (
    withState.find((d) => d.state === 'live') ??
    withState.find((d) => d.state === 'announced') ??
    withState[withState.length - 1] ??
    null
  );
}

/** The Storefront-API shape this becomes at launch (metaobject fields are strings or null). */
export function toMetaobject(d: Drop): StorefrontMetaobject {
  const field = (key: string, type: string, value: string | number | boolean | null) => ({
    key,
    type,
    value: value === null ? null : String(value),
  });
  return {
    id: `gid://shopify/Metaobject/drop-${d.number}`,
    handle: `drop-${d.number}`,
    type: 'drop',
    fields: [
      field('number', 'single_line_text_field', d.number),
      field('state', 'single_line_text_field', d.state),
      field('starts_at', 'date_time', d.startsAt),
      field('ends_at', 'date_time', d.endsAt),
      field('timezone', 'single_line_text_field', d.timezone),
      field('frames', 'json', JSON.stringify(d.frames)),
      field('pairs_per_frame', 'number_integer', d.pairsPerFrame),
      field('limit_per_customer', 'number_integer', d.limitPerCustomer),
      field('early_access_enabled', 'boolean', d.earlyAccess.enabled),
      field('early_access_hours', 'number_integer', d.earlyAccess.hoursBeforePublic),
      field('statement', 'multi_line_text_field', d.statement),
    ],
  };
}
