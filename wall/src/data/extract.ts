// What the wall ships from the repo's content, and nothing more: the eight frames' facts (content/products/, only
// what the wall shows: id, handle, look number, name; never the price, 00-decisions.md #47) and the copy deck's wall
// section with the alt phrases (content/copy/en.json).
// Pure functions over the parsed JSON, used by the Vite plugin that makes `virtual:wall-frames` and
// `virtual:wall-copy` at build time, and by the tests. Nothing is invented: a value the record lacks is null.
import { FRAME_IDS, type FrameFacts, type FrameId } from '../lib/types';

type Json = Record<string, unknown>;

const str = (v: unknown): string | null => (typeof v === 'string' && v.length ? v : null);
const obj = (v: unknown): Json => (v && typeof v === 'object' && !Array.isArray(v) ? (v as Json) : {});

export function frameFacts(product: unknown): FrameFacts | null {
  const p = obj(product);
  const id = str(p.id);
  if (!id || !(FRAME_IDS as readonly string[]).includes(id)) return null;
  return {
    id: id as FrameId,
    handle: str(p.handle),
    lookNumber: str(p.lookNumber),
    name: str(p.name),
  };
}

/** The eight frames by id, from the product records given (any order, any extras ignored). */
export function framesFrom(products: unknown[]): Partial<Record<FrameId, FrameFacts>> {
  const out: Partial<Record<FrameId, FrameFacts>> = {};
  for (const p of products) {
    const f = frameFacts(p);
    if (f) out[f.id] = f;
  }
  return out;
}

export interface WallCopy {
  wall: Json;
  alt: { stage: string | null; subjects: Record<string, string>; angles: Record<string, string> };
  meta: { brand: string | null; instagram: string | null; domain: string | null; hashtag: string | null };
}

/** The copy the wall ships: its own section, the alt phrases, the brand's names. The site's sections stay behind. */
export function copyFrom(deck: unknown): WallCopy {
  const d = obj(deck);
  const alt = obj(d.alt);
  const meta = obj(d.meta);
  const strings = (v: unknown): Record<string, string> => Object.fromEntries(Object.entries(obj(v)).filter(([k, x]) => !k.startsWith('$') && typeof x === 'string')) as Record<string, string>;
  return {
    wall: obj(d.wall),
    alt: { stage: str(alt.stage), subjects: strings(alt.subjects), angles: strings(alt.angles) },
    meta: { brand: str(meta.brand), instagram: str(meta.instagram), domain: str(meta.domain), hashtag: str(meta.hashtag) },
  };
}
