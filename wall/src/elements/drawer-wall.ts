// <drawer-wall> (DRAWER-WALL.md, The wall): lays the drawers over the wall plate from the bay_wall record. The
// plate (portrait under 1024 px, landscape from 1024) is the page's LCP element, with a fixed aspect from
// rects.json so nothing shifts; each <drawer-bay> sits over its rect and shows its own dark crop when its record
// says dark; the plate never changes. The page's only heading, wall.title, is visually hidden here; a polite
// live region speaks the announcements.
import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { styleMap } from 'lit/directives/style-map.js';
import type { WallStore } from '../data/store';
import type { Layout } from '../lib/manifest';
import type { BayRects } from './drawer-bay';
import { t } from '../lib/copy';
import { log } from '../lib/log';
import './drawer-bay';

interface RectsFile { layout: Layout; plate: { width: number; height: number }; view: { frontFraction: number; centerY: number; aspect: number[] }; drawers: Array<BayRects & { index: number }> }

@customElement('drawer-wall')
export class DrawerWall extends LitElement {
  static override styles = css`
    :host { display: block; background: var(--color-surface-scene); }
    .plate { position: relative; width: 100%; margin: 0 auto; background: var(--color-surface-scene); }
    .plate > picture > img { display: block; width: 100%; height: 100%; }
    .plate > picture { position: absolute; inset: 0; }
    .visually-hidden { position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0; overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; border: 0; }
    .empty { color: var(--color-text-secondary); font-size: var(--font-size-micro); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; padding: var(--space-8) var(--space-4); text-align: center; }
  `;

  @property({ attribute: false }) store: WallStore | null = null;
  /** The layout: by the viewport (portrait under 1024 px, landscape from it), or forced (the states sheet, the tests). */
  @property() layout: Layout | 'auto' = 'auto';
  @state() private current: Layout = 'portrait';
  @state() private rects: RectsFile | null = null;
  @state() private plateSize = { width: 0, height: 0 };
  @state() private announcement = '';
  private media = window.matchMedia('(min-width: 1024px)');
  private ro: ResizeObserver | null = null;
  private onStoreChange = () => this.requestUpdate();

  override connectedCallback(): void {
    super.connectedCallback();
    this.current = this.pick();
    this.media.addEventListener('change', this.onMedia);
    this.store?.addEventListener('change', this.onStoreChange);
    this.store?.addEventListener('mechanic', this.onStoreChange);
    void this.loadRects();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.media.removeEventListener('change', this.onMedia);
    this.store?.removeEventListener('change', this.onStoreChange);
    this.store?.removeEventListener('mechanic', this.onStoreChange);
    this.ro?.disconnect();
  }

  private pick(): Layout {
    return this.layout === 'auto' ? (this.media.matches ? 'landscape' : 'portrait') : this.layout;
  }

  protected override willUpdate(changed: Map<PropertyKey, unknown>): void {
    if (changed.has('layout')) {
      this.current = this.pick();
      void this.loadRects();
    }
    if (changed.has('store')) {
      const old = changed.get('store') as WallStore | null;
      old?.removeEventListener('change', this.onStoreChange);
      old?.removeEventListener('mechanic', this.onStoreChange);
      this.store?.addEventListener('change', this.onStoreChange);
      this.store?.addEventListener('mechanic', this.onStoreChange);
      void this.loadRects();
    }
  }

  private onMedia = () => {
    const next = this.pick();
    if (next === this.current) return;
    this.current = next;
    log('wall.layout', { layout: this.current });
    void this.loadRects();
  };

  private async loadRects(): Promise<void> {
    const s = this.store;
    if (!s) return;
    const layout = this.current;
    const entry = s.assets.rects(layout, s.knobStyle);
    const file = entry ? s.assets.file(entry) : null;
    if (!file) { this.rects = null; return; }
    try {
      const r = await fetch(s.assets.url(file));
      const j = (await r.json()) as RectsFile;
      if (j.layout === layout && layout === this.current) this.rects = j;
    } catch (e) {
      log('wall.rects-failed', { error: String(e) });
      this.rects = null;
    }
  }

  protected override firstUpdated(): void {
    const plate = this.renderRoot.querySelector('.plate');
    if (plate && 'ResizeObserver' in window) {
      this.ro = new ResizeObserver(([e]) => { if (e) this.plateSize = { width: e.contentRect.width, height: e.contentRect.height }; });
      this.ro.observe(plate);
    }
  }

  /** Say something through the live region (the drawer view calls it). */
  announce(text: string): void {
    this.announcement = '';
    requestAnimationFrame(() => { this.announcement = text; });
  }

  /** The plate's rect for a drawer, for the view's opening transition: the drawer's 4:5 crop in page pixels. */
  viewCropFor(id: string): DOMRect | null {
    const s = this.store;
    const r = this.rects;
    if (!s || !r) return null;
    const i = s.resolved.findIndex((b) => b.id === id);
    const d = r.drawers[i];
    const plate = this.renderRoot.querySelector('.plate');
    if (!d || !plate) return null;
    const p = plate.getBoundingClientRect();
    const faceW = (d.face.w / 100) * p.width;
    const cropW = faceW / r.view.frontFraction;
    const cropH = cropW * (r.view.aspect[1]! / r.view.aspect[0]!);
    const cx = p.left + ((d.face.x + d.face.w / 2) / 100) * p.width;
    const cy = p.top + ((d.face.y + d.face.h / 2) / 100) * p.height;
    return new DOMRect(cx - cropW / 2, cy - r.view.centerY * cropH, cropW, cropH);
  }

  override render() {
    const s = this.store;
    if (!s) return nothing;
    const layout = this.current;
    const plate = s.assets.plate(layout, s.knobStyle);
    const r = this.rects && this.rects.layout === layout ? this.rects : null;
    const aspect = r ? `${r.plate.width} / ${r.plate.height}` : plate?.width && plate.height ? `${plate.width} / ${plate.height}` : '1170 / 2319';
    return html`
      <h1 class="visually-hidden">${t('title')}</h1>
      <div class="plate" part="plate" style=${styleMap({ aspectRatio: aspect })} data-layout=${layout}>
        ${plate ? html`<picture>
          <source srcset=${s.assets.url(s.assets.file(plate, 'avif')!)} type="image/avif">
          <img src=${s.assets.url(s.assets.file(plate, 'webp')!)} alt="" width=${plate.width ?? nothing} height=${plate.height ?? nothing} fetchpriority="high" decoding="async" draggable="false">
        </picture>` : html`<p class="empty">${t('title')}</p>`}
        ${r ? s.resolved.map((bay, i) => {
          const d = r.drawers[i];
          if (!d) return nothing;
          const dark = s.assets.darkCrop(layout, s.knobStyle, i);
          const darkSrc = dark ? { avif: s.assets.url(s.assets.file(dark, 'avif')!), webp: s.assets.url(s.assets.file(dark, 'webp')!) } : null;
          return html`<drawer-bay .bay=${bay} .rects=${d} .darkSrc=${darkSrc} .mechanic=${s.mechanic} .plateSize=${this.plateSize} data-id=${bay.id}></drawer-bay>`;
        }) : nothing}
      </div>
      <div class="visually-hidden" role="status" aria-live="polite" aria-atomic="true">${this.announcement}</div>
    `;
  }
}

declare global { interface HTMLElementTagNameMap { 'drawer-wall': DrawerWall } }
