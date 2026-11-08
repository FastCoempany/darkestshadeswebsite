// <photo-zoom> (DRAWER-WALL.md, step 6): the real lightbox photographs (A1, A2, A3 and A6 where they exist) on
// their stage colour, each at full resolution: pinch, drag or double-tap down to one image pixel per screen pixel;
// on desktop drag and the wheel; keys + − 0 and the arrows. The photographs come from wall/public/zoom/ (made by
// npm run assets, never committed) with their manifest alt text. Only here does the pale stage appear.
import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { styleMap } from 'lit/directives/style-map.js';
import type { FrameFacts } from '../lib/types';
import { clamp, doubleTapZoom, isTap, wheelZoom, zoomAbout, TAP_MAX_MS } from '../lib/gestures';
import { t, stageAlt } from '../lib/copy';
import { log } from '../lib/log';

interface ZoomEntry { angle: string; file: string; width: number; height: number; bytes: number; alt: string }
interface ZoomIndex { frames: Record<string, ZoomEntry[]> }

let indexPromise: Promise<ZoomIndex | null> | null = null;
function loadIndex(): Promise<ZoomIndex | null> {
  if (!indexPromise) indexPromise = fetch('./zoom/index.json').then((r) => (r.ok ? (r.json() as Promise<ZoomIndex>) : null)).catch(() => null);
  return indexPromise;
}

@customElement('photo-zoom')
export class PhotoZoom extends LitElement {
  static override styles = css`
    :host { position: absolute; inset: 0; display: block; background: var(--color-surface-stage); color: var(--color-text-inverse); touch-action: none; overflow: hidden; }
    .view { position: absolute; inset: 0; overflow: hidden; outline: none; cursor: grab; }
    .view:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); outline-offset: calc(-1 * var(--border-focus)); }
    img { position: absolute; left: 0; top: 0; transform-origin: 0 0; will-change: transform; user-select: none; -webkit-user-drag: none; max-width: none; }
    .bar { position: absolute; left: 0; right: 0; bottom: 0; display: grid; gap: var(--space-1); padding: var(--space-3); padding-bottom: calc(var(--space-3) + env(safe-area-inset-bottom, 0px)); pointer-events: none; }
    .buttons { display: flex; justify-content: center; gap: var(--space-2) var(--space-3); flex-wrap: wrap; }
    button { appearance: none; background: none; border: 0; border-bottom: var(--border-hairline) solid var(--color-text-inverse); color: var(--color-text-inverse); font: inherit; font-size: 11px; font-weight: var(--font-weight-medium); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; padding: var(--space-3) var(--space-1); min-height: 44px; min-width: 44px; cursor: pointer; pointer-events: auto; }
    button[aria-pressed="true"] { border-bottom-width: 2px; }
    button:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); outline-offset: var(--border-focus-offset); }
    .empty { position: absolute; inset: 0; display: grid; place-items: center; font-size: 11px; letter-spacing: var(--font-tracking-micro); text-transform: uppercase; }
    .count { text-align: center; font-size: 11px; letter-spacing: var(--font-tracking-micro); text-transform: uppercase; pointer-events: none; }
  `;

  @property({ attribute: false }) frame: FrameFacts | null = null;
  @property() name = '';
  @state() private entries: ZoomEntry[] = [];
  @state() private index = 0;
  @state() private zoom = 1;
  @state() private pan = { x: 0, y: 0 };
  @state() private loaded = false;
  private pointers = new Map<number, { x: number; y: number }>();
  private pinch: { d: number; z: number; cx: number; cy: number } | null = null;
  private down: { x: number; y: number; t: number } | null = null;
  private lastTap = 0;
  private ro: ResizeObserver | null = null;
  private box = { w: 1, h: 1 };

  override connectedCallback(): void {
    super.connectedCallback();
    void loadIndex().then((idx) => {
      this.entries = (idx && this.frame ? idx.frames[this.frame.id] : null) ?? [];
      if (!this.entries.length) log('photos.none', { frame: this.frame?.id ?? null });
      this.index = 0;
      this.reset();
    });
  }

  protected override firstUpdated(): void {
    const v = this.renderRoot.querySelector('.view') as HTMLElement | null;
    if (v && 'ResizeObserver' in window) {
      this.ro = new ResizeObserver(([e]) => { if (e) { this.box = { w: e.contentRect.width, h: e.contentRect.height }; this.requestUpdate(); } });
      this.ro.observe(v);
      this.box = { w: v.clientWidth, h: v.clientHeight };
    }
    v?.focus({ preventScroll: true });
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.ro?.disconnect();
  }

  private get entry(): ZoomEntry | null { return this.entries[this.index] ?? null; }

  /** The fit scale: the whole photograph in the view; max zoom: one image pixel per device pixel. */
  private fit(): number {
    const e = this.entry;
    if (!e) return 1;
    return Math.min(this.box.w / e.width, this.box.h / e.height);
  }
  private maxZoom(): number {
    const e = this.entry;
    if (!e) return 1;
    return Math.max(1, (1 / this.fit()) / (window.devicePixelRatio || 1));
  }

  private reset(): void { this.zoom = 1; this.pan = { x: 0, y: 0 }; this.loaded = false; }

  private clampPan(p: { x: number; y: number }, z = this.zoom): { x: number; y: number } {
    const e = this.entry;
    if (!e) return p;
    const s = this.fit() * z;
    const w = e.width * s, h = e.height * s;
    const maxX = Math.max(0, (w - this.box.w) / 2), maxY = Math.max(0, (h - this.box.h) / 2);
    return { x: clamp(p.x, -maxX, maxX), y: clamp(p.y, -maxY, maxY) };
  }

  private setZoom(z: number, aboutX = 0, aboutY = 0): void {
    const z1 = clamp(z, 1, this.maxZoom());
    this.pan = this.clampPan(zoomAbout(this.pan, this.zoom, z1, aboutX, aboutY), z1);
    this.zoom = z1;
    log('photos.zoom', { zoom: Math.round(z1 * 100) / 100 });
  }

  private viewPoint(ev: { clientX: number; clientY: number }): { x: number; y: number } {
    const r = (this.renderRoot.querySelector('.view') as HTMLElement).getBoundingClientRect();
    return { x: ev.clientX - r.left - r.width / 2, y: ev.clientY - r.top - r.height / 2 };
  }

  private onPointerDown(ev: PointerEvent): void {
    (ev.currentTarget as HTMLElement).setPointerCapture(ev.pointerId);
    this.pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      this.pinch = { d: Math.hypot(a!.x - b!.x, a!.y - b!.y), z: this.zoom, cx: (a!.x + b!.x) / 2, cy: (a!.y + b!.y) / 2 };
      this.down = null;
    } else {
      this.down = { x: ev.clientX, y: ev.clientY, t: performance.now() };
    }
  }

  private onPointerMove(ev: PointerEvent): void {
    const prev = this.pointers.get(ev.pointerId);
    if (!prev) return;
    this.pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    if (this.pinch && this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      const d = Math.hypot(a!.x - b!.x, a!.y - b!.y);
      const c = this.viewPoint({ clientX: this.pinch.cx, clientY: this.pinch.cy });
      this.setZoom(this.pinch.z * (d / this.pinch.d), c.x, c.y);
      return;
    }
    if (this.pointers.size === 1) {
      this.pan = this.clampPan({ x: this.pan.x + ev.clientX - prev.x, y: this.pan.y + ev.clientY - prev.y });
    }
  }

  private onPointerUp(ev: PointerEvent): void {
    this.pointers.delete(ev.pointerId);
    if (this.pointers.size < 2) this.pinch = null;
    const d = this.down;
    this.down = null;
    if (d && isTap(ev.clientX - d.x, ev.clientY - d.y, performance.now() - d.t)) {
      const now = performance.now();
      if (now - this.lastTap < TAP_MAX_MS) {
        const p = this.viewPoint(ev);
        this.setZoom(doubleTapZoom(this.zoom), p.x, p.y);
        this.lastTap = 0;
      } else this.lastTap = now;
    }
  }

  private onWheel(ev: WheelEvent): void {
    ev.preventDefault();
    const p = this.viewPoint(ev);
    this.setZoom(wheelZoom(this.zoom, ev.deltaY), p.x, p.y);
  }

  private onKeyDown(ev: KeyboardEvent): void {
    const step = 40;
    switch (ev.key) {
      case '+': case '=': ev.preventDefault(); this.setZoom(this.zoom * 1.2); break;
      case '-': ev.preventDefault(); this.setZoom(this.zoom / 1.2); break;
      case '0': ev.preventDefault(); this.setZoom(1); break;
      case 'ArrowLeft': ev.preventDefault(); if (this.zoom > 1) this.pan = this.clampPan({ x: this.pan.x + step, y: this.pan.y }); else this.go(-1); break;
      case 'ArrowRight': ev.preventDefault(); if (this.zoom > 1) this.pan = this.clampPan({ x: this.pan.x - step, y: this.pan.y }); else this.go(1); break;
      case 'ArrowUp': ev.preventDefault(); this.pan = this.clampPan({ x: this.pan.x, y: this.pan.y + step }); break;
      case 'ArrowDown': ev.preventDefault(); this.pan = this.clampPan({ x: this.pan.x, y: this.pan.y - step }); break;
      default: break;
    }
  }

  private go(delta: number): void {
    if (!this.entries.length) return;
    this.index = (this.index + delta + this.entries.length) % this.entries.length;
    this.reset();
    log('photos.show', { index: this.index, angle: this.entry?.angle });
    this.dispatchEvent(new CustomEvent('announce', { detail: { text: t('announce.photo', { name: this.name, n: this.index + 1, count: this.entries.length, alt: this.entry?.alt ?? '' }) }, bubbles: true, composed: true }));
  }

  override render() {
    const e = this.entry;
    const s = e ? this.fit() * this.zoom : 1;
    const w = e ? e.width * s : 0, h = e ? e.height * s : 0;
    const left = (this.box.w - w) / 2 + this.pan.x, top = (this.box.h - h) / 2 + this.pan.y;
    return html`
      <div class="view" tabindex="0" role="group" aria-label=${t('photos')}
        @pointerdown=${this.onPointerDown} @pointermove=${this.onPointerMove} @pointerup=${this.onPointerUp} @pointercancel=${this.onPointerUp} @wheel=${this.onWheel} @keydown=${this.onKeyDown}>
        ${e ? html`<img src=${'./zoom/' + e.file} alt=${e.alt || stageAlt(this.frame, e.angle)} width=${e.width} height=${e.height} decoding="async" draggable="false"
            style=${styleMap({ transform: `translate(${left}px, ${top}px) scale(${s})`, width: `${e.width}px`, height: `${e.height}px` })} @load=${() => { this.loaded = true; }}>` : html`<p class="empty">${t('photos')}</p>`}
      </div>
      <div class="bar">
        ${e ? html`<div class="count" aria-hidden="true">${this.index + 1} / ${this.entries.length} · ${e.angle}</div>` : nothing}
        <div class="buttons">
        ${this.entries.map((en, i) => html`<button type="button" aria-pressed=${i === this.index ? 'true' : 'false'} @click=${() => { this.index = i; this.reset(); }}>${en.angle}</button>`)}
        <button type="button" @click=${() => this.setZoom(this.zoom * 1.2)}>${t('closer')}</button>
        <button type="button" @click=${() => this.setZoom(this.zoom / 1.2)}>${t('further')}</button>
        <button type="button" @click=${() => this.setZoom(1)}>${t('reset')}</button>
        <button type="button" @click=${() => this.dispatchEvent(new CustomEvent('photos-close', { bubbles: true, composed: true }))}>${t('photosClose')}</button>
        </div>
      </div>
    `;
  }
}

declare global { interface HTMLElementTagNameMap { 'photo-zoom': PhotoZoom } }
