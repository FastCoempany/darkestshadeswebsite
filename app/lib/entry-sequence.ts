/**
 * The entry's sequence file (assets/entry/sequence.json), written by tools/photo/entry_stills.py and read
 * by the player and by tools/flashcheck.py. Imported at build time; the files are served from /entry/.
 */
import sequenceJson from '../../assets/entry/sequence.json';

export interface EntryStill {
  ratio: '3:4' | '4:5';
  bright: boolean;
  shot: string;
  sources: {avif: string[]; webp: string[]};
  sizes: {width: number; height: number}[];
}

export interface EntryStep {
  type: 'card' | 'burst' | 'logo' | 'end';
  /** Index into `copy.entry.cards`; `text` is the same words, kept for the flash check. */
  card?: number;
  text?: string;
  seconds?: number;
  layout?: 'framed' | 'bleed';
  fps?: number;
  /** Ids into `stills`. */
  frames?: string[];
  ground?: string;
}

export interface EntrySequence {
  version: 1;
  stills: Record<string, EntryStill>;
  steps: EntryStep[];
}

export const sequence = sequenceJson as unknown as EntrySequence;

/** `assets/entry/x.avif` -> `/entry/x.avif` (vite.config.ts serves the folder there). */
export function entryUrl(path: string): string {
  return path.replace(/^assets\/entry\//, '/entry/');
}

export function stillSources(still: EntryStill): {avif: string; webp: string; fallback: string} {
  const set = (list: string[]) => list.map((p, i) => `${entryUrl(p)} ${still.sizes[i]?.width ?? 0}w`).join(', ');
  return {avif: set(still.sources.avif), webp: set(still.sources.webp), fallback: entryUrl(still.sources.webp[0])};
}

export function stepSeconds(step: EntryStep): number {
  if (step.type === 'burst') return (step.frames?.length ?? 0) / (step.fps ?? 12);
  return step.seconds ?? 1;
}

export function totalSeconds(seq: EntrySequence = sequence): number {
  return seq.steps.reduce((sum, s) => sum + stepSeconds(s), 0);
}
