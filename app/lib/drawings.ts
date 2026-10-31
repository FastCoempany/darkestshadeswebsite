/**
 * The technical drawings (content/products/drawings, from tools/drawings.py) are read on the server for the
 * one frame a page shows, so the client never carries all thirty-two (the frame page's chunk was 433 KiB
 * with them inlined; Lighthouse's LCP on that page swung with it).
 */
const files = import.meta.glob('../../content/products/drawings/*.svg', {query: '?raw', import: 'default'}) as Record<string, () => Promise<string>>;

export type DrawingView = 'front' | 'side' | 'top' | 'iso';
export type Drawings = Partial<Record<DrawingView, string>>;

export async function drawingsFor(frame: string, views: DrawingView[] = ['front', 'side', 'top']): Promise<Drawings> {
  const out: Drawings = {};
  for (const view of views) {
    const key = Object.keys(files).find((k) => k.endsWith(`/${frame}-${view}.svg`));
    if (key) out[view] = await files[key]();
  }
  return out;
}
