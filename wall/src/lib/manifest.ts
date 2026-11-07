// The asset manifest's loader (DRAWER-WALL.md, "Assets"): wall/assets/manifest.json validated by npm run check,
// read here into lookups the elements use. Every path is relative to the assets folder; `base` makes it a URL.
import type { FrameId } from './types';

export type AssetKind = 'wall-plate' | 'wall-dark' | 'sequence-frame' | 'glb' | 'still' | 'env' | 'camera' | 'rects' | 'tints';
export type AssetStatus = 'prototype' | 'mockup' | 'final';
export type Layout = 'portrait' | 'landscape';

export interface AssetEntry {
  id: string;
  kind: AssetKind;
  files: string[];
  status: AssetStatus;
  tool: string;
  command: string;
  sourceCommit: string;
  frame?: FrameId;
  layout?: Layout;
  knob?: 'black-relief' | 'gold' | 'plain';
  width?: number;
  height?: number;
  checks?: Record<string, string | number | boolean>;
  alt?: string;
  note?: string;
}

export interface Manifest {
  renderSet: string;
  assets: AssetEntry[];
}

/** A sequence frame's entry id: `seq/<frame or base>/<width>/<NNN>`. */
export const sequenceId = (frame: FrameId | 'base', width: number, index: number): string => `seq/${frame}/${width}/${String(index).padStart(3, '0')}`;

export class AssetIndex {
  readonly byId = new Map<string, AssetEntry>();
  readonly byKind = new Map<AssetKind, AssetEntry[]>();
  readonly problems: string[] = [];

  constructor(readonly manifest: Manifest, readonly base = './assets/') {
    for (const e of manifest.assets ?? []) {
      if (this.byId.has(e.id)) this.problems.push(`${e.id}: listed twice`);
      this.byId.set(e.id, e);
      const list = this.byKind.get(e.kind) ?? [];
      list.push(e);
      this.byKind.set(e.kind, list);
    }
  }

  url(file: string): string {
    return this.base + file;
  }

  /** The file of an entry in a format the browser takes: the first file with that extension, or the first file. */
  file(entry: AssetEntry, preferExt?: string): string | null {
    if (!entry.files.length) return null;
    if (preferExt) {
      const f = entry.files.find((x) => x.endsWith('.' + preferExt));
      if (f) return f;
    }
    return entry.files[0] ?? null;
  }

  plate(layout: Layout, knob: AssetEntry['knob']): AssetEntry | null {
    return (this.byKind.get('wall-plate') ?? []).find((e) => e.layout === layout && e.knob === knob) ?? null;
  }

  rects(layout: Layout, knob: AssetEntry['knob']): AssetEntry | null {
    return (this.byKind.get('rects') ?? []).find((e) => e.layout === layout && e.knob === knob) ?? null;
  }

  darkCrop(layout: Layout, knob: AssetEntry['knob'], bayIndex: number): AssetEntry | null {
    return this.byId.get(`wall/${layout}/${knob}/bay-${String(bayIndex).padStart(2, '0')}-dark`) ?? null;
  }

  /** The drawer-view frames for a frame (or the base sequence), at a width, in order; empty when none. */
  sequence(frame: FrameId | 'base', width: number): AssetEntry[] {
    const prefix = `seq/${frame}/${width}/`;
    return (this.byKind.get('sequence-frame') ?? []).filter((e) => e.id.startsWith(prefix)).sort((a, b) => a.id.localeCompare(b.id));
  }

  /** The widths a sequence exists at, smallest first. */
  sequenceWidths(frame: FrameId | 'base'): number[] {
    const widths = new Set<number>();
    for (const e of this.byKind.get('sequence-frame') ?? []) {
      const m = e.id.match(new RegExp(`^seq/${frame}/(\\d+)/`));
      if (m) widths.add(Number(m[1]));
    }
    return [...widths].sort((a, b) => a - b);
  }

  glb(frame: FrameId): AssetEntry | null {
    return this.byId.get(`glb/${frame}`) ?? null;
  }

  still(frame: FrameId): AssetEntry | null {
    return this.byId.get(`stills/${frame}-lifted`) ?? null;
  }

  env(): AssetEntry | null {
    return this.byId.get('env/drawer') ?? null;
  }

  camera(name: 'open' | 'inspect'): AssetEntry | null {
    return this.byId.get(`camera/${name}`) ?? null;
  }

  tints(): AssetEntry | null {
    return this.byId.get('lens-tints') ?? null;
  }

  /** The resolver's questions: a drawer can be seen when its frame sequence exists at some width; it can be lifted
   * when its GLB or its lifted still exists too. */
  hasSequence(frame: FrameId): boolean {
    return this.sequenceWidths(frame).length > 0;
  }

  hasLift(frame: FrameId): boolean {
    return !!(this.glb(frame) || this.still(frame));
  }
}

export function isManifest(x: unknown): x is Manifest {
  return !!x && typeof x === 'object' && Array.isArray((x as Manifest).assets) && typeof (x as Manifest).renderSet === 'string';
}
