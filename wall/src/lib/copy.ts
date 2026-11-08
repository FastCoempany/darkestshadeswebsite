// The wall's copy (DRAWER-WALL.md, Copy): every string from the copy deck's wall section, read through one function
// with its placeholders filled; no string is hard-coded in wall/src. A key the deck lacks returns an empty string
// and is reported once, so a missing string renders nothing rather than a made-up one.
import copyData from 'virtual:wall-copy';
import type { FrameFacts } from './types';

type Dict = Record<string, unknown>;
const reported = new Set<string>();

function lookup(path: string): string | null {
  let node: unknown = copyData.wall;
  for (const part of path.split('.')) {
    if (!node || typeof node !== 'object') return null;
    node = (node as Dict)[part];
  }
  return typeof node === 'string' ? node : null;
}

/** The string at `key` (dots for nesting: `announce.open`) with `{name}`-style placeholders filled. */
export function t(key: string, values: Record<string, string | number> = {}): string {
  const s = lookup(key);
  if (s === null) {
    if (!reported.has(key)) {
      reported.add(key);
      console.warn(`copy: no wall.${key} in the copy deck`);
    }
    return '';
  }
  return s.replace(/\{(\w+)\}/g, (m, k: string) => (k in values ? String(values[k]) : m));
}

/** The keys the deck lacks so far, for the debug log. */
export function missingKeys(): string[] {
  return [...reported];
}

/** A frame's alt phrase (the copy deck's alt.subjects), capitalised where it starts a sentence. */
export function subjectOf(frame: Pick<FrameFacts, 'id'> | null, capitalise = false): string {
  if (!frame) return '';
  const s = copyData.alt.subjects[frame.id] ?? '';
  return capitalise && s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

/** A photograph's alt text as the manifest gives it, or the deck's stage phrase as a fallback. */
export function stageAlt(frame: Pick<FrameFacts, 'id'> | null, angle: string): string {
  const subject = subjectOf(frame, true);
  const a = copyData.alt.angles[angle] ?? angle;
  return (copyData.alt.stage ?? '{subject}, {angle}.').replace('{subject}', subject).replace('{angle}', a);
}

export const brand = copyData.meta;
