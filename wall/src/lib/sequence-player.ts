// The sequence player (DRAWER-WALL.md, In the browser): the drawer view's frames fetched as encoded blobs (about
// 1 MB a drawer at 720 px), decoded ImageBitmaps kept only for the current frame ± 2 and closed otherwise, the
// next ones decoded ahead in the direction of travel, a cross-fade between neighbours on a 2D canvas sized to the
// view at the device pixel ratio; AVIF where createImageBitmap takes it, WebP otherwise. The first and the last
// frames load first. Pure enough to test: the decoding and the canvas are injectable.
import { DECODE_WINDOW } from './gestures';

export interface FrameSource { avif?: string; webp?: string }
export interface Decoder { (blob: Blob): Promise<ImageBitmap> }
export interface Fetcher { (url: string): Promise<Blob> }

export interface PlayerOptions {
  fetcher?: Fetcher;
  decoder?: Decoder;
  /** Whether AVIF decodes here; probed once by default. */
  avif?: boolean;
  window?: number;
  onLog?: (type: string, data?: Record<string, unknown>) => void;
}

let avifProbe: Promise<boolean> | null = null;
/** Whether createImageBitmap takes AVIF here: a 1 × 1 AVIF decoded once per visit. */
export function canDecodeAvif(): Promise<boolean> {
  if (!avifProbe) {
    avifProbe = (async () => {
      try {
        const b64 = 'AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAABcAAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAEAAAABAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAAB9tZGF0EgAKCBgANogQEAwgMg8f8D///8WfhwB8+ErK42A=';
        const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
        const bmp = await createImageBitmap(new Blob([bytes], { type: 'image/avif' }));
        bmp.close();
        return true;
      } catch {
        return false;
      }
    })();
  }
  return avifProbe;
}

export class SequencePlayer {
  readonly count: number;
  private blobs: (Blob | null)[];
  private bitmaps = new Map<number, ImageBitmap>();
  private decoding = new Map<number, Promise<ImageBitmap | null>>();
  private fetches: (Promise<void> | null)[];
  private current = 0;
  private direction = 1;
  private disposed = false;
  private readonly fetcher: Fetcher;
  private readonly decoder: Decoder;
  private readonly window: number;
  private readonly onLog: (type: string, data?: Record<string, unknown>) => void;
  private avif: boolean | null;

  constructor(readonly frames: FrameSource[], opts: PlayerOptions = {}) {
    this.count = frames.length;
    this.blobs = frames.map(() => null);
    this.fetches = frames.map(() => null);
    this.fetcher = opts.fetcher ?? (async (u) => { const r = await fetch(u); if (!r.ok) throw new Error(`${r.status} ${u}`); return r.blob(); });
    this.decoder = opts.decoder ?? ((b) => createImageBitmap(b));
    this.window = opts.window ?? DECODE_WINDOW;
    this.onLog = opts.onLog ?? (() => {});
    this.avif = opts.avif ?? null;
  }

  private async format(): Promise<'avif' | 'webp'> {
    if (this.avif === null) this.avif = await canDecodeAvif();
    return this.avif ? 'avif' : 'webp';
  }

  private urlOf(i: number, fmt: 'avif' | 'webp'): string | null {
    const f = this.frames[i];
    if (!f) return null;
    return (fmt === 'avif' ? f.avif ?? f.webp : f.webp ?? f.avif) ?? null;
  }

  /** Fetch every frame's bytes: the first and the last first, then outward from the current frame. */
  async prefetch(): Promise<void> {
    const order = [0, this.count - 1, ...Array.from({ length: this.count }, (_, i) => i)].filter((v, i, a) => a.indexOf(v) === i);
    await Promise.all(order.map((i) => this.ensureBlob(i)));
  }

  private ensureBlob(i: number): Promise<void> {
    if (this.blobs[i]) return Promise.resolve();
    if (this.fetches[i]) return this.fetches[i]!;
    const p = (async () => {
      const fmt = await this.format();
      const url = this.urlOf(i, fmt);
      if (!url) return;
      try {
        this.blobs[i] = await this.fetcher(url);
      } catch (e) {
        this.onLog('sequence.fetch-failed', { i, url, error: String(e) });
      }
    })();
    this.fetches[i] = p;
    return p;
  }

  /** The bitmap for frame i, decoded on demand; null while its bytes are not here yet or after dispose. */
  async bitmap(i: number): Promise<ImageBitmap | null> {
    if (this.disposed) return null;
    const have = this.bitmaps.get(i);
    if (have) return have;
    const pending = this.decoding.get(i);
    if (pending) return pending;
    const p = (async () => {
      await this.ensureBlob(i);
      const blob = this.blobs[i];
      if (!blob || this.disposed) return null;
      try {
        const bmp = await this.decoder(blob);
        if (this.disposed || Math.abs(i - this.current) > this.window + 1) { bmp.close(); return null; }
        this.bitmaps.set(i, bmp);
        this.onLog('sequence.decoded', { i, held: this.bitmaps.size });
        return bmp;
      } catch (e) {
        this.onLog('sequence.decode-failed', { i, error: String(e) });
        return null;
      } finally {
        this.decoding.delete(i);
      }
    })();
    this.decoding.set(i, p);
    return p;
  }

  /** Move to position p (0..1): keeps the window of decoded frames round it, decodes ahead in the direction of
   * travel, closes the rest. Returns the two neighbouring frame indices and the blend between them. */
  seek(p: number): { a: number; b: number; mix: number } {
    const f = Math.min(1, Math.max(0, p)) * (this.count - 1);
    const a = Math.floor(f);
    const b = Math.min(this.count - 1, a + 1);
    const mix = f - a;
    const next = Math.round(f);
    if (next !== this.current) this.direction = next > this.current ? 1 : -1;
    this.current = next;
    for (const [i, bmp] of this.bitmaps) {
      if (Math.abs(i - this.current) > this.window) { bmp.close(); this.bitmaps.delete(i); }
    }
    for (let d = 0; d <= this.window; d++) {
      const i = this.current + d * this.direction;
      if (i >= 0 && i < this.count) void this.bitmap(i);
    }
    const back = this.current - this.direction;
    if (back >= 0 && back < this.count) void this.bitmap(back);
    return { a, b, mix };
  }

  /** Draw position p on the canvas: a cross-fade between the two neighbouring frames (what is decoded of them). */
  async draw(ctx: CanvasRenderingContext2D, p: number, width: number, height: number): Promise<boolean> {
    const { a, b, mix } = this.seek(p);
    const [ba, bb] = await Promise.all([this.bitmap(a), mix > 0 ? this.bitmap(b) : null]);
    if (this.disposed) return false;
    const fit = (bmp: ImageBitmap) => {
      const k = Math.max(width / bmp.width, height / bmp.height);
      const w = bmp.width * k, h = bmp.height * k;
      return [(width - w) / 2, (height - h) / 2, w, h] as const;
    };
    ctx.clearRect(0, 0, width, height);
    if (!ba && !bb) return false;
    ctx.globalAlpha = 1;
    if (ba) ctx.drawImage(ba, ...fit(ba));
    if (bb && mix > 0) { ctx.globalAlpha = mix; ctx.drawImage(bb, ...fit(bb)); ctx.globalAlpha = 1; }
    return true;
  }

  /** How many decoded frames are held (the budget: at most 5). */
  held(): number {
    return this.bitmaps.size;
  }

  dispose(): void {
    this.disposed = true;
    for (const bmp of this.bitmaps.values()) bmp.close();
    this.bitmaps.clear();
    this.blobs.fill(null);
  }
}
