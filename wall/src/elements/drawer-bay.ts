// <drawer-bay> (DRAWER-WALL.md, The wall; Every drawer is its own thing): one drawer, its resolved state, its
// label, its dark crop, its events. It sits over its rect on the wall plate. The face is a <button> named
// "{name}. Open the drawer." (a locked one: "Not yet."); no price anywhere (00-decisions.md #47); a hidden drawer
// renders no control. Tap first:
// a tap anywhere on the face opens; the wall scrolls natively (touch-action: pan-y). Pull first: the knob's rect
// takes touch-action: none and a pull there opens with the pointer carried; the rest of the face scrolls.
import { LitElement, html, css, nothing, type PropertyValues } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { styleMap } from 'lit/directives/style-map.js';
import type { ResolvedBay } from '../lib/types';
import type { Mechanic } from '../data/store';
import { isTap, KNOB_MIN_PX } from '../lib/gestures';
import { t } from '../lib/copy';
import { log } from '../lib/log';

export interface BayRects {
  face: { x: number; y: number; w: number; h: number };
  knob: { x: number; y: number; w: number; h: number };
  label: { x: number; y: number; w: number; h: number };
  crop: { x: number; y: number; w: number; h: number };
}

export interface BayOpenDetail { id: string; pointer: { x: number; y: number; pointerId: number; target: Element } | null }

@customElement('drawer-bay')
export class DrawerBay extends LitElement {
  static override styles = css`
    :host { display: contents; }
    .face, .label, .dark, .knob { position: absolute; }
    .dark { pointer-events: none; display: block; width: 100%; height: 100%; object-fit: fill; }
    .face {
      appearance: none; margin: 0; padding: 0; border: 0; background: transparent; cursor: pointer;
      touch-action: pan-y; -webkit-tap-highlight-color: transparent; border-radius: 0; color: inherit; font: inherit;
    }
    .face:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); outline-offset: var(--border-focus-offset); }
    .face[aria-disabled="true"] { cursor: default; }
    .knob { touch-action: none; }
    .label {
      display: flex; flex-direction: column; align-items: center; justify-content: flex-start; text-align: center;
      padding: 0 var(--space-1); gap: 0.1em; pointer-events: none; min-width: 0; overflow: visible;
    }
    .look { color: var(--color-text-editorial); font-size: 11px; font-weight: var(--font-weight-medium); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; line-height: 1.2; font-variant-numeric: tabular-nums; }
    .name { color: var(--color-text-secondary); font-size: 11px; font-weight: var(--font-weight-medium); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; line-height: 1.2; overflow-wrap: anywhere; }
    /* when the drawer is sold out, the word under the name; no price on the wall (00-decisions.md #47) */
    .status { color: var(--color-text-secondary); font-size: 11px; font-weight: var(--font-weight-medium); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; line-height: 1.3; margin-top: 0.1em; }
    @media (min-width: 1024px) { .look, .name, .status { font-size: 12px; } }
    /* under 360 px the rail rect is 59 px tall and a two-line name at 11 px overran it by 6 px (the line after it then sat on the
       next drawer's face, under its dark crop): smaller type and tighter lines keep every label inside its rect at 320 px */
    @media (max-width: 359px) { .look, .name, .status { font-size: 10px; line-height: 1.1; margin-top: 0; } .label { gap: 0; } }
  `;

  @property({ attribute: false }) bay: ResolvedBay | null = null;
  @property({ attribute: false }) rects: BayRects | null = null;
  @property({ attribute: false }) darkSrc: { avif: string; webp: string } | null = null;
  @property() mechanic: Mechanic = 'tap';
  /** The plate's size on screen, so the knob's touch target can be grown to 44 px. */
  @property({ attribute: false }) plateSize: { width: number; height: number } = { width: 0, height: 0 };
  @state() private pressed: { x: number; y: number; t: number; id: number } | null = null;

  protected override updated(changed: PropertyValues): void {
    if (changed.has('bay') && this.bay) log('bay.render', { id: this.bay.id, state: this.bay.state, light: this.bay.light });
  }

  private pct(r: { x: number; y: number; w: number; h: number }) {
    return { left: `${r.x}%`, top: `${r.y}%`, width: `${r.w}%`, height: `${r.h}%` };
  }

  /** The knob's rect grown to at least 44 × 44 px on screen (SC 2.5.8 and the doc's 44 px). */
  private knobStyle() {
    const r = this.rects!.knob;
    const pw = this.plateSize.width, ph = this.plateSize.height;
    if (!pw || !ph) return this.pct(r);   // the plate's size on screen is not known yet: the rect as drawn; grown once it is
    const wPct = Math.max(r.w, (KNOB_MIN_PX / pw) * 100), hPct = Math.max(r.h, (KNOB_MIN_PX / ph) * 100);
    return { left: `${r.x + r.w / 2 - wPct / 2}%`, top: `${r.y + r.h / 2 - hPct / 2}%`, width: `${wPct}%`, height: `${hPct}%` };
  }

  private accessibleName(): string {
    const b = this.bay!;
    if (b.state === 'locked') return t('notYet');
    const name = b.label?.name ?? '';
    const sold = b.label?.soldOut ? ` ${t('soldOut')}.` : '';
    return `${name ? `${name}.` : ''}${sold} ${t('openLabel')}`.trim();
  }

  private open(pointer: BayOpenDetail['pointer']): void {
    if (!this.bay?.canOpen) return;
    log('bay.open', { id: this.bay.id, by: pointer ? 'pull' : 'tap' });
    this.dispatchEvent(new CustomEvent<BayOpenDetail>('bay-open', { detail: { id: this.bay.id, pointer }, bubbles: true, composed: true }));
  }

  // tap first: a pointer that moves under 8 px and lifts under 400 ms opens; anything longer is a scroll or nothing
  private onPointerDown(ev: PointerEvent): void {
    if (ev.button !== 0) return;
    this.pressed = { x: ev.clientX, y: ev.clientY, t: performance.now(), id: ev.pointerId };
  }

  private onPointerUp(ev: PointerEvent): void {
    const p = this.pressed;
    this.pressed = null;
    if (!p || p.id !== ev.pointerId) return;
    if (isTap(ev.clientX - p.x, ev.clientY - p.y, performance.now() - p.t)) {
      ev.preventDefault();
      this.open(null);
    }
  }

  private onPointerCancel(): void {
    this.pressed = null;
  }

  // the keyboard: Enter and Space on the button (its click), never a pointer tap (handled above)
  private onClick(ev: MouseEvent): void {
    if (ev.detail === 0) this.open(null);   // a keyboard click has detail 0
  }

  // pull first: a pull on the knob opens with the pointer carried into the view
  private onKnobDown(ev: PointerEvent): void {
    if (ev.button !== 0 || !this.bay?.canOpen) return;
    ev.preventDefault();
    ev.stopPropagation();
    this.open({ x: ev.clientX, y: ev.clientY, pointerId: ev.pointerId, target: ev.target as Element });
  }

  override render() {
    const b = this.bay, r = this.rects;
    if (!b || !r) return nothing;
    const dark = b.light === 'dark' && this.darkSrc;
    const label = b.label;
    return html`
      ${dark ? html`<picture class="dark-wrap" style=${styleMap({ position: 'absolute', ...this.pct(r.crop) })}>
        <source srcset=${this.darkSrc!.avif} type="image/avif">
        <img class="dark" src=${this.darkSrc!.webp} alt="" decoding="async" draggable="false">
      </picture>` : nothing}
      ${b.focusable ? html`<button class="face" type="button" part="face"
          style=${styleMap(this.pct(r.face))}
          aria-label=${this.accessibleName()}
          aria-disabled=${b.canOpen ? 'false' : 'true'}
          data-state=${b.state} data-light=${b.light}
          @pointerdown=${this.mechanic === 'tap' ? this.onPointerDown : undefined}
          @pointerup=${this.mechanic === 'tap' ? this.onPointerUp : undefined}
          @pointercancel=${this.onPointerCancel}
          @click=${this.onClick}></button>` : nothing}
      ${b.focusable && this.mechanic === 'pull' && b.canOpen ? html`<div class="knob" part="knob" style=${styleMap(this.knobStyle())} @pointerdown=${this.onKnobDown}></div>` : nothing}
      ${label ? html`<div class="label" part="label" style=${styleMap(this.pct(r.label))} aria-hidden="true">
        ${label.lookNumber ? html`<span class="look">${label.lookNumber}</span>` : nothing}
        ${label.notYet ? html`<span class="name">${t('notYet')}</span>` : label.name ? html`<span class="name">${label.name}</span>` : nothing}
        ${label.soldOut ? html`<span class="status">${t('soldOut')}</span>` : nothing}
      </div>` : nothing}
    `;
  }
}

declare global { interface HTMLElementTagNameMap { 'drawer-bay': DrawerBay } }
