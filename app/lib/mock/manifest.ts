/**
 * The image library: assets/photography/MANIFEST.csv read at build time (MiniOxygen has no file system).
 * Files are served from /photography/ by the static-assets plugin in vite.config.ts, so a new or replaced
 * final needs no code change: tools/photo/export_web.py writes the files and the manifest (RUN.md, phase 5).
 */
import manifestCsv from '../../../assets/photography/MANIFEST.csv?raw';
import {parseCsv} from './csv';
import type {FrameId, ImageFormat, StorefrontImage} from './types';

export const PHOTOGRAPHY_BASE = '/photography';

const FRAME_IDS: FrameId[] = ['F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F08', 'F09'];

function isFrameId(v: string): v is FrameId {
  return (FRAME_IDS as string[]).includes(v);
}

function shotCode(row: Record<string, string>): string {
  if (row.id.startsWith('ds-cast-')) {
    // ds-cast-w1-s07-f02 -> W1-S07-F02-A1; ds-cast-w2-s06-f03-a2 -> W2-S06-F03-A2
    const parts = row.id.replace('ds-cast-', '').toUpperCase().split('-');
    const [cast, scene, frame, angle] = parts;
    return `${cast}-${scene}-${frame}-${angle ?? 'A1'}`;
  }
  return `${row.frame}-${row.angle}`;
}

function toImage(row: Record<string, string>): StorefrontImage | null {
  if (!isFrameId(row.frame)) return null;
  const widths = row.widths.split(/\s+/).filter(Boolean).map(Number).sort((a, b) => a - b);
  const formats = row.formats.split(/\s+/).filter(Boolean) as ImageFormat[];
  const width = Number(row.width);
  const height = Number(row.height);
  const largest = widths[widths.length - 1];
  const srcset = Object.fromEntries(
    formats.map((f) => [f, widths.map((w) => `${PHOTOGRAPHY_BASE}/${row.id}-${w}.${f} ${w}w`).join(', ')]),
  ) as Record<ImageFormat, string>;
  const kind = row.id.startsWith('ds-cast-') ? 'cast' : 'product';
  const landscape = width > height;
  return {
    id: `gid://shopify/MediaImage/${row.id}`,
    url: `${PHOTOGRAPHY_BASE}/${row.id}-${largest}.jpg`,
    altText: row.alt,
    width,
    height,
    ds: {
      manifestId: row.id,
      shot: shotCode(row),
      frame: row.frame,
      angle: row.angle,
      ratio: landscape ? 'hero-landscape' : 'stage',
      ratioLabel: landscape ? '3:2' : '4:5',
      widths,
      formats,
      srcset,
      status: row.status,
      kind,
    },
  };
}

/** The one reader: the manifest's CSV text in, the image library out (a row for a frame the site does not sell stays out). */
export function imagesFromManifest(csv: string): StorefrontImage[] {
  return parseCsv(csv)
    .map(toImage)
    .filter((i): i is StorefrontImage => i !== null);
}

export const images: StorefrontImage[] = imagesFromManifest(manifestCsv);
const byId = new Map(images.map((i) => [i.ds.manifestId, i]));

export function imageById(manifestId: string): StorefrontImage | null {
  return byId.get(manifestId) ?? null;
}

const ANGLE_ORDER = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'H'];

/** A frame's product finals in gallery order: A1 to A6, then the hero. */
export function productImagesFor(frame: FrameId): StorefrontImage[] {
  return images
    .filter((i) => i.ds.kind === 'product' && i.ds.frame === frame && i.ds.status === 'final')
    .sort((a, b) => ANGLE_ORDER.indexOf(a.ds.angle) - ANGLE_ORDER.indexOf(b.ds.angle));
}

/** A frame's on-model finals. */
export function castImagesFor(frame: FrameId): StorefrontImage[] {
  return images.filter((i) => i.ds.kind === 'cast' && i.ds.frame === frame && i.ds.status === 'final');
}

export function imageForShot(frame: FrameId, angle: string): StorefrontImage | null {
  return images.find((i) => i.ds.kind === 'product' && i.ds.frame === frame && i.ds.angle === angle) ?? null;
}
