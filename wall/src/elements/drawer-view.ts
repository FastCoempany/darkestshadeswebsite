// <drawer-view> (DRAWER-WALL.md, One drawer, step by step): the full-screen drawer view. One layer over the wall
// (role="dialog", aria-modal, labelled by the frame's name); nothing behind it scrolls. The drawer, shut, barely
// lit; the hint wall.hintPull with a thin falling line; pull down to slide the drawer out through the scrubbed
// sequence; let go and it settles open or shut (velocity first, then position); quiet buttons do the same. Tap the
// frame (or wall.lift) to lift it into <lifted-frame>; wall.photos opens <photo-zoom>; put back, shut, close with
// focus back on the drawer. The name and $100 stay on screen. Reduced motion: cross-fades of about 160 ms, the
// drawer still follows the finger but snaps. Haptics: a 10 ms tick at the stops where navigator.vibrate exists.
import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { classMap } from 'lit/directives/class-map.js';
import type { WallStore } from '../data/store';
import type { ResolvedBay } from '../lib/types';
import { initialContext, reduce, type ViewContext, type ViewEvent, VIEW_OPEN_STATES } from '../lib/machine';
import { FULL_PULL, HAPTIC_MS, HINT_IDLE_MS, LIFT_MS, LIFT_REDUCED_MS, REDUCED_FADE_MS, SETTLE_SPRING, isTap, pullPosition, rubberBand } from '../lib/gestures';
import { springSettled, springStep, type SpringState } from '../lib/spring';
import { SequencePlayer, type FrameSource } from '../lib/sequence-player';
import { lockScroll, unlockScroll } from '../lib/scroll-lock';
import { trapFocus, type FocusTrap } from '../lib/focus-trap';
import { t, subjectOf } from '../lib/copy';
import { log } from '../lib/log';
import type { Tier } from '../lib/tier';

export interface OpenRequest { bay: ResolvedBay; pointer: { x: number; y: number; pointerId: number; target: Element } | null; from: DOMRect | null }

const HINT_GESTURES = ['pull', 'lift', 'turn'] as const;
type Hint = (typeof HINT_GESTURES)[number];
const done = new Set<Hint>();   // hints gone after the first success of that gesture, for the session

@customElement('drawer-view')
export class DrawerView extends LitElement {
  static override styles = css`
    :host { display: none; position: fixed; inset: 0; z-index: 10; background: var(--color-surface-scene); color: var(--color-text-primary);
      touch-action: none; overscroll-behavior: contain; user-select: none; -webkit-user-select: none; container-type: size; }
    :host([open]) { display: block; }
    :host([inline]) { position: absolute; z-index: auto; display: block; }
    .view { position: absolute; inset: 0; outline: none; }
    .dim { position: absolute; inset: 0; background: var(--color-surface-scene); }
    /* the stage: 4:5 like the renders, as large as the view allows (container units, so the states sheet's boxes work too) */
    .stage { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: min(100cqw, calc(100cqh * 1200 / 1500)); aspect-ratio: 1200 / 1500; max-width: 100%; overflow: hidden; outline: none; }
    .stage:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); outline-offset: calc(-1 * var(--border-focus)); }
    canvas, .poster { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
    .poster { object-fit: cover; }
    .fade { transition: opacity 160ms var(--motion-ease); }
    .lift-layer { position: absolute; inset: 0; }
    .dimmed { opacity: 0.35; filter: blur(6px); transition: opacity 600ms var(--motion-ease), filter 600ms var(--motion-ease); }
    .top, .bottom { position: absolute; left: 0; right: 0; display: flex; align-items: center; justify-content: space-between; gap: var(--space-3);
      padding-left: max(var(--space-4), env(safe-area-inset-left, 0px)); padding-right: max(var(--space-4), env(safe-area-inset-right, 0px)); pointer-events: none; }
    .top { top: 0; padding-top: calc(var(--space-4) + env(safe-area-inset-top, 0px)); z-index: 2; }
    .top.on-stage .micro, .top.on-stage .price { color: var(--color-text-inverse); }
    photo-zoom { position: absolute; inset: 0; z-index: 1; }
    .bottom { bottom: 0; padding-bottom: calc(var(--space-6) + env(safe-area-inset-bottom, 0px)); flex-direction: column; align-items: stretch; gap: var(--space-3); }
    .bottom[hidden] { display: none; }
    .micro { font-size: 11px; font-weight: var(--font-weight-medium); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; color: var(--color-text-secondary); }
    .price { font-size: var(--font-size-body); font-variant-numeric: tabular-nums; color: var(--color-text-primary); }
    .name { font-size: 22px; font-weight: var(--font-weight-light); color: var(--color-text-primary); margin: 0; text-align: center; }
    .hint { display: flex; flex-direction: column; align-items: center; gap: var(--space-2); color: var(--color-text-secondary); opacity: 0; transition: opacity 900ms var(--motion-ease); min-height: 3.5em; justify-content: flex-end; }
    .hint.on { opacity: 1; }
    .hint i { display: block; width: 1px; height: 34px; background: linear-gradient(var(--color-text-secondary), transparent); animation: drip 2.4s ease-in-out infinite; }
    @keyframes drip { 0%, 100% { transform: scaleY(0.4); transform-origin: top; } 50% { transform: scaleY(1); transform-origin: top; } }
    .controls { display: flex; flex-wrap: wrap; justify-content: center; gap: var(--space-2) var(--space-4); pointer-events: auto; }
    button.quiet { appearance: none; background: none; border: 0; border-bottom: var(--border-hairline) solid var(--color-border-rule); color: var(--color-text-secondary); font: inherit; font-size: 11px; font-weight: var(--font-weight-medium); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; padding: var(--space-3) var(--space-1); min-height: 44px; min-width: 44px; cursor: pointer; }
    button.quiet:hover { color: var(--color-text-primary); }
    button.quiet:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); outline-offset: var(--border-focus-offset); }
    button.quiet[hidden] { display: none; }
    .tap-frame { position: absolute; left: 50%; top: 42%; width: 56%; height: 24%; transform: translate(-50%, -50%); background: transparent; border: 0; cursor: pointer; pointer-events: none; }
    .tap-frame:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); }
    :host([data-state="open"]) .tap-frame { pointer-events: auto; }
    .close { pointer-events: auto; }
    @media (prefers-reduced-motion: reduce) { .hint i { animation: none; } .dimmed, .fade { transition-duration: 160ms; } }
  `;

  @property({ attribute: false }) store: WallStore | null = null;
  @property({ type: Number }) tier: Tier = 2;
  @property({ type: Boolean, reflect: true }) open = false;
  @state() private ctx: ViewContext = initialContext(false, false);
  @state() private bay: ResolvedBay | null = null;
  @state() private hint: Hint | null = null;
  @state() private posterUrl: string | null = null;
  @state() private drawn = false;

  private player: SequencePlayer | null = null;
  private canvas: HTMLCanvasElement | null = null;
  private trap: FocusTrap | null = null;
  private drag: { id: number; y0: number; p0: number; lastY: number; lastT: number; v: number } | null = null;
  private spring: SpringState | null = null;
  private raf = 0;
  private hintTimer = 0;
  private reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  private pendingPointer: OpenRequest['pointer'] = null;
  private lastDrawn = -1;

  get state() { return this.ctx.state; }
  get position() { return this.ctx.p; }
  /** The states sheet's fixture name, once shown. */
  fixture: string | undefined;

  /** The states sheet's way in (never a user's): the view in a named state, inline, no scroll lock or focus trap. */
  async showFixture(bay: ResolvedBay, name: string): Promise<void> {
    const s = this.store;
    if (!s) return;
    this.bay = bay;
    this.setAttribute('inline', '');
    this.open = true;
    if (name === 'tier 1 lifted') this.tier = 1;
    const base = initialContext(true, true);
    const states: Record<string, Partial<ViewContext>> = {
      'shut': { state: 'shut', p: 0 }, 'pulling': { state: 'pulling', p: 0.45 }, 'open': { state: 'open', p: 1 },
      'lifted': { state: 'lifted', p: 1 }, 'turned': { state: 'lifted', p: 1, yaw: 40, pitch: -10 }, 'zoomed': { state: 'lifted', p: 1, zoom: 2.2 },
      'photos': { state: 'photos', p: 1 }, 'tier 1 lifted': { state: 'lifted', p: 1 }, 'reduced motion': { state: 'open', p: 1 },
    };
    this.ctx = { ...base, ...(states[name] ?? states['shut']) };
    this.setAttribute('data-state', this.ctx.state);
    const frame = bay.frame?.id ?? null;
    const seqName = frame && s.assets.sequenceWidths(frame).length ? frame : 'base';
    const widths = s.assets.sequenceWidths(seqName);
    const width = widths[0] ?? 0;
    const frames: FrameSource[] = s.assets.sequence(seqName, width).map((e) => ({ avif: s.assets.file(e, 'avif') ? s.assets.url(s.assets.file(e, 'avif')!) : undefined, webp: s.assets.file(e, 'webp') ? s.assets.url(s.assets.file(e, 'webp')!) : undefined }));
    this.player?.dispose();
    this.player = frames.length ? new SequencePlayer(frames, { onLog: log }) : null;
    this.posterUrl = frames[0]?.webp ?? frames[0]?.avif ?? null;
    await this.updateComplete;
    await this.player?.prefetch();
    await this.draw();
    if (this.ctx.state === 'shut') this.hint = 'pull';
    if (this.ctx.state === 'open') this.hint = 'lift';
    if (this.ctx.state === 'lifted' && this.tier === 2) this.hint = 'turn';
    const lifted = this.renderRoot.querySelector('lifted-frame') as (HTMLElement & { lift?: () => Promise<void> }) | null;
    if (lifted?.lift) { await lifted.lift(); this.syncLifted(); }
  }

  /** Open the view for a drawer (the wall's bay-open). */
  async show(req: OpenRequest): Promise<void> {
    const s = this.store;
    if (!s || !req.bay.canOpen) return;
    this.bay = req.bay;
    this.ctx = reduce(initialContext(req.bay.canOpen, req.bay.canLift && this.tier === 2 ? true : req.bay.canLift), { type: 'OPEN', ...(req.pointer ? { pointer: { x: req.pointer.x, y: req.pointer.y } } : {}) });
    if (this.ctx.state !== 'entering') return;
    this.open = true;
    this.setAttribute('data-state', this.ctx.state);
    lockScroll();
    this.pendingPointer = req.pointer;
    log('view.enter', { id: req.bay.id, by: req.pointer ? 'pull' : 'tap' });
    // the sequence: the frame's own where it exists, else the base (the empty drawer); first and last frames first
    const frame = req.bay.frame?.id ?? null;
    const widths = frame && s.assets.sequenceWidths(frame).length ? s.assets.sequenceWidths(frame) : s.assets.sequenceWidths('base');
    const name = frame && s.assets.sequenceWidths(frame).length ? frame : 'base';
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const want = Math.min(window.innerWidth, window.innerHeight * 0.8) * dpr;
    const width = widths.find((w) => w >= want) ?? widths[widths.length - 1] ?? 0;
    const frames: FrameSource[] = s.assets.sequence(name, width).map((e) => ({ avif: s.assets.file(e, 'avif') ? s.assets.url(s.assets.file(e, 'avif')!) : undefined, webp: s.assets.file(e, 'webp') ? s.assets.url(s.assets.file(e, 'webp')!) : undefined }));
    this.player?.dispose();
    this.player = frames.length ? new SequencePlayer(frames, { onLog: log }) : null;
    this.posterUrl = frames[0]?.webp ?? frames[0]?.avif ?? null;
    await this.updateComplete;
    this.trap = trapFocus(this.renderRoot.querySelector('.view') as HTMLElement, this.renderRoot.querySelector('.stage') as HTMLElement);
    void this.player?.prefetch();
    this.dispatch({ type: 'ENTERED' });
    this.announce(t('announce.open', { name: req.bay.label?.name ?? '' }).replace(/^\.\s*/, ''));
    void this.draw();
    this.armHint('pull');
    if (req.pointer) this.carryPointer(req.pointer);
  }

  /** The deep link: the view on its last frame, the drawer open, not lifted. */
  jumpOpen(): void {
    if (this.ctx.state !== 'shut') return;
    this.dispatch({ type: 'OPEN_DRAWER' });
    this.spring = null;
    cancelAnimationFrame(this.raf);
    this.ctx = { ...this.ctx, p: 1 };
    void this.draw().then(() => this.dispatch({ type: 'SETTLED' }));
  }

  private carryPointer(p: NonNullable<OpenRequest['pointer']>): void {
    // pull first: the same drag goes on in the view without a second touch
    const stage = this.renderRoot.querySelector('.stage') as HTMLElement | null;
    if (!stage) return;
    try { stage.setPointerCapture(p.pointerId); } catch { /* the pointer may be gone */ }
    this.drag = { id: p.pointerId, y0: p.y, p0: 0, lastY: p.y, lastT: performance.now(), v: 0 };
  }

  private dispatch(ev: ViewEvent): void {
    const before = this.ctx;
    const after = reduce(before, ev);
    if (after === before) return;
    this.ctx = after;
    this.setAttribute('data-state', after.state);
    log('view.state', { from: before.state, to: after.state, event: ev.type });
    this.onEnter(after, before);
  }

  private onEnter(c: ViewContext, prev: ViewContext): void {
    switch (c.state) {
      case 'opening': case 'shutting': this.settle(c.state === 'opening' ? 1 : 0); break;
      case 'open': this.haptic(); this.announce(t('announce.open', { name: this.bay?.label?.name ?? '' })); if (prev.state !== 'returning') this.armHint('lift'); break;
      case 'shut': if (prev.state === 'shutting') { this.haptic(); this.announce(t('announce.shut')); } this.armHint('pull'); break;
      case 'lifting': this.lift(); break;
      case 'lifted': this.announce(t('announce.lifted', { name: this.bay?.label?.name ?? '' })); if (prev.state !== 'photos') this.armHint('turn'); break;
      case 'returning': this.putBack(); break;
      case 'leaving': this.leave(); break;
      case 'photos': this.clearHint(); break;
      default: break;
    }
  }

  // --- the pull ------------------------------------------------------------------------------------------------
  private onPointerDown(ev: PointerEvent): void {
    if (ev.button !== 0) return;
    const st = this.ctx.state;
    if (st === 'lifted' || st === 'photos' || st === 'lifting' || st === 'returning' || st === 'entering' || st === 'leaving') return;
    (ev.currentTarget as HTMLElement).setPointerCapture(ev.pointerId);
    this.spring = null;
    this.drag = { id: ev.pointerId, y0: ev.clientY, p0: this.ctx.p, lastY: ev.clientY, lastT: performance.now(), v: 0 };
  }

  private onPointerMove(ev: PointerEvent): void {
    const d = this.drag;
    if (!d || d.id !== ev.pointerId) return;
    const now = performance.now();
    const dt = Math.max(1, now - d.lastT);
    d.v = 0.6 * d.v + 0.4 * ((ev.clientY - d.lastY) / dt);
    d.lastY = ev.clientY;
    d.lastT = now;
    const h = (this.renderRoot.querySelector('.stage') as HTMLElement | null)?.clientHeight || window.innerHeight;
    const p = pullPosition(d.p0, ev.clientY - d.y0, h);
    this.dispatch({ type: 'DRAG', p });
    void this.draw();
  }

  private onPointerUp(ev: PointerEvent): void {
    const d = this.drag;
    if (!d || d.id !== ev.pointerId) return;
    this.drag = null;
    const moved = Math.abs(ev.clientY - d.y0);
    if (this.ctx.state === 'pulling') {
      // a tap on the open drawer's frame is the tap-frame button's; a tap elsewhere while shut does nothing
      if (moved < 2 && isTap(0, moved, performance.now() - d.lastT + 1)) {
        this.dispatch({ type: 'RELEASE', v: 0, p: this.ctx.p });
        return;
      }
      if (this.ctx.p >= 0.98 && d.p0 >= 0.98) done.add('pull');
      this.dispatch({ type: 'RELEASE', v: d.v, p: this.ctx.p });
    }
  }

  private settle(target: 0 | 1): void {
    cancelAnimationFrame(this.raf);
    if (this.reduced.matches) {
      this.ctx = { ...this.ctx, p: target };
      void this.draw().then(() => this.dispatch({ type: 'SETTLED' }));
      return;
    }
    this.spring = { x: this.ctx.p, v: 0 };
    let last = performance.now();
    const step = (now: number) => {
      if (!this.spring || (this.ctx.state !== 'opening' && this.ctx.state !== 'shutting')) return;
      const dt = Math.min(64, now - last);
      last = now;
      this.spring = springStep(this.spring, target, dt, SETTLE_SPRING);
      this.ctx = { ...this.ctx, p: Math.min(1 + rubberBand(0), Math.max(0, this.spring.x)) };
      void this.draw();
      if (springSettled(this.spring, target, 0.002, 0.02)) {
        this.spring = null;
        this.ctx = { ...this.ctx, p: target };
        if (target === 1) done.add('pull');
        void this.draw();
        this.dispatch({ type: 'SETTLED' });
        return;
      }
      this.raf = requestAnimationFrame(step);
    };
    this.raf = requestAnimationFrame(step);
  }

  private async draw(): Promise<void> {
    const c = this.canvas ?? (this.renderRoot.querySelector('canvas') as HTMLCanvasElement | null);
    if (!c || !this.player) return;
    this.canvas = c;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = Math.round(c.clientWidth * dpr), h = Math.round(c.clientHeight * dpr);
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    const ctx = c.getContext('2d');
    if (!ctx) return;
    const p = Math.min(1, Math.max(0, this.ctx.p));
    const ok = await this.player.draw(ctx, p, w, h);
    if (ok && !this.drawn) this.drawn = true;
    this.lastDrawn = p;
    log('view.draw', { p: Math.round(p * 1000) / 1000, held: this.player.held() });
  }

  // --- the lift, the photographs, the way back ------------------------------------------------------------------
  private lift(): void {
    done.add('lift');
    this.clearHint();
    const el = this.renderRoot.querySelector('lifted-frame') as (HTMLElement & { lift?: () => Promise<void> }) | null;
    const ms = this.reduced.matches ? LIFT_REDUCED_MS : LIFT_MS;
    const go = el?.lift ? el.lift() : new Promise<void>((r) => setTimeout(r, ms));
    void go.then(() => this.dispatch({ type: 'LIFTED' }));
  }

  private putBack(): void {
    const el = this.renderRoot.querySelector('lifted-frame') as (HTMLElement & { putBack?: () => Promise<void> }) | null;
    const ms = this.reduced.matches ? LIFT_REDUCED_MS : LIFT_MS;
    const go = el?.putBack ? el.putBack() : new Promise<void>((r) => setTimeout(r, ms));
    void go.then(() => { this.dispatch({ type: 'RETURNED' }); this.announce(t('announce.back', { name: this.bay?.label?.name ?? '' })); });
  }

  private leave(): void {
    this.clearHint();
    const ms = this.reduced.matches ? REDUCED_FADE_MS : 300;
    setTimeout(() => {
      this.dispatch({ type: 'LEFT' });
      this.open = false;
      unlockScroll();
      this.player?.dispose();
      this.player = null;
      this.drawn = false;
      this.trap?.release();
      this.trap = null;
      log('view.left', { id: this.bay?.id });
      this.dispatchEvent(new CustomEvent('view-closed', { detail: { id: this.bay?.id }, bubbles: true, composed: true }));
    }, ms);
  }

  /** A record changed (the panel): the view closes only if the drawer can no longer open. */
  recordChanged(bay: ResolvedBay): void {
    if (!this.bay || bay.id !== this.bay.id) return;
    this.bay = bay;
    this.dispatch({ type: 'RECORD', canOpen: bay.canOpen, canLift: bay.canLift });
  }

  // --- hints, haptics, announcements ----------------------------------------------------------------------------
  private armHint(h: Hint): void {
    this.clearHint();
    if (done.has(h)) return;
    if (h === 'turn' && this.tier !== 2) return;
    this.hintTimer = window.setTimeout(() => { this.hint = h; log('hint', { hint: h }); }, HINT_IDLE_MS);
  }

  private clearHint(): void {
    clearTimeout(this.hintTimer);
    this.hint = null;
  }

  private haptic(): void {
    try { navigator.vibrate?.(HAPTIC_MS); } catch { /* never the only signal */ }
  }

  private announce(text: string): void {
    this.dispatchEvent(new CustomEvent('announce', { detail: { text }, bubbles: true, composed: true }));
  }

  // --- keys -------------------------------------------------------------------------------------------------------
  private onKeyDown(ev: KeyboardEvent): void {
    const st = this.ctx.state;
    const lifted = st === 'lifted';
    const step = (dp: number) => { this.dispatch({ type: 'DRAG', p: Math.min(1, Math.max(0, this.ctx.p + dp)) }); void this.draw(); clearTimeout(this.keyTimer); this.keyTimer = window.setTimeout(() => this.dispatch({ type: 'RELEASE', v: 0, p: this.ctx.p }), 320); };
    switch (ev.key) {
      case 'Escape': ev.preventDefault(); this.dispatch({ type: 'ESC' }); break;
      case 'ArrowDown': case 'PageDown': if (lifted) { ev.preventDefault(); this.turnBy(0, 8); } else if (st === 'shut' || st === 'pulling' || st === 'open') { ev.preventDefault(); step(0.12); } break;
      case 'ArrowUp': case 'PageUp': if (lifted) { ev.preventDefault(); this.turnBy(0, -8); } else if (st === 'shut' || st === 'pulling' || st === 'open') { ev.preventDefault(); step(-0.12); } break;
      case 'ArrowLeft': if (lifted) { ev.preventDefault(); this.turnBy(-24, 0); } break;
      case 'ArrowRight': if (lifted) { ev.preventDefault(); this.turnBy(24, 0); } break;
      case '+': case '=': if (lifted) { ev.preventDefault(); this.zoomBy(1.2); } break;
      case '-': if (lifted) { ev.preventDefault(); this.zoomBy(1 / 1.2); } break;
      case '0': if (lifted) { ev.preventDefault(); this.dispatch({ type: 'RESET' }); this.syncLifted(); } break;
      default: break;
    }
  }
  private keyTimer = 0;

  private turnBy(dx: number, dy: number): void { done.add('turn'); this.clearHint(); this.dispatch({ type: 'TURN', dx, dy }); this.syncLifted(); }
  private zoomBy(f: number): void { this.dispatch({ type: 'ZOOM', zoom: this.ctx.zoom * f }); this.syncLifted(); }
  private syncLifted(): void {
    const el = this.renderRoot.querySelector('lifted-frame') as (HTMLElement & { pose?: unknown }) | null;
    if (el) el.pose = { yaw: this.ctx.yaw, pitch: this.ctx.pitch, zoom: this.ctx.zoom };
  }

  /** The lifted frame reports its turn and zoom (pointer gestures) so the machine holds the pose. */
  private onLiftedTurn(ev: CustomEvent<{ dx: number; dy: number }>): void { done.add('turn'); this.clearHint(); this.dispatch({ type: 'TURN', dx: ev.detail.dx, dy: ev.detail.dy }); }
  private onLiftedZoom(ev: CustomEvent<{ zoom: number }>): void { this.dispatch({ type: 'ZOOM', zoom: ev.detail.zoom }); }

  override render() {
    const s = this.store, b = this.bay, c = this.ctx;
    if (!s || !b) return nothing;
    const name = b.label?.name ?? '';
    const st = c.state;
    const drawerOpen = st === 'open';
    const liftedish = st === 'lifting' || st === 'lifted' || st === 'photos' || st === 'returning';
    const showPhotos = st === 'photos';
    const frame = b.frame;
    const subject = subjectOf(frame);
    return html`
      <div class="view" role="dialog" aria-modal="true" aria-label=${name} tabindex="-1" @keydown=${this.onKeyDown}>
      <div class="dim" @click=${(ev: Event) => { if (ev.target === ev.currentTarget && window.innerWidth >= 1024 && (st === 'shut' || st === 'open')) this.dispatch({ type: 'CLOSE' }); }}></div>
      <div class="stage" tabindex="-1"
        @pointerdown=${this.onPointerDown} @pointermove=${this.onPointerMove} @pointerup=${this.onPointerUp} @pointercancel=${this.onPointerUp}>
        ${this.posterUrl && !this.drawn ? html`<img class="poster" src=${this.posterUrl} alt="" draggable="false">` : nothing}
        <canvas class=${classMap({ dimmed: liftedish })} aria-hidden="true"></canvas>
        <button class="tap-frame" type="button" aria-label=${t('lift')} ?hidden=${!drawerOpen || !c.canLift} @click=${() => this.dispatch({ type: 'LIFT' })}></button>
        ${liftedish ? html`<lifted-frame class="lift-layer" .store=${s} .frame=${frame} .tier=${this.tier} .active=${st === 'lifted'} .label=${t('model3dLabel', { subject })}
            @lifted-turn=${this.onLiftedTurn} @lifted-zoom=${this.onLiftedZoom} @lifted-tap=${() => this.dispatch({ type: 'PUT_BACK' })}></lifted-frame>` : nothing}
      </div>
      ${showPhotos ? html`<photo-zoom .frame=${frame} .name=${name} @photos-close=${() => this.dispatch({ type: 'BACK' })}></photo-zoom>` : nothing}
      <div class=${classMap({ top: true, 'on-stage': showPhotos })}><span class="micro">${name}</span><span class="price">${b.label?.price ?? ''}</span></div>
      <div class="bottom" ?hidden=${showPhotos}>
        ${liftedish ? html`<p class="name">${name}</p>` : nothing}
        <div class=${classMap({ hint: true, on: !!this.hint })} aria-hidden="true">
          ${this.hint === 'pull' ? html`<span class="micro">${t('hintPull')}</span><i></i>` : this.hint === 'lift' ? html`<span class="micro">${t('hintLift')}</span>` : this.hint === 'turn' ? html`<span class="micro">${t('hintTurn')}</span>` : nothing}
        </div>
        <div class="controls">
          ${st === 'shut' || st === 'pulling' || st === 'shutting' ? html`<button class="quiet" type="button" @click=${() => this.dispatch({ type: 'OPEN_DRAWER' })}>${t('open')}</button>` : nothing}
          ${drawerOpen || st === 'opening' ? html`<button class="quiet" type="button" @click=${() => this.dispatch({ type: 'SHUT_DRAWER' })}>${t('shut')}</button>` : nothing}
          ${drawerOpen && c.canLift ? html`<button class="quiet" type="button" @click=${() => this.dispatch({ type: 'LIFT' })}>${t('lift')}</button>` : nothing}
          ${st === 'lifted' && this.tier === 2 ? html`
            <button class="quiet" type="button" @click=${() => this.turnBy(-24, 0)}>${t('turnLeft')}</button>
            <button class="quiet" type="button" @click=${() => this.turnBy(24, 0)}>${t('turnRight')}</button>
            <button class="quiet" type="button" @click=${() => this.zoomBy(1.2)}>${t('closer')}</button>
            <button class="quiet" type="button" @click=${() => this.zoomBy(1 / 1.2)}>${t('further')}</button>
            <button class="quiet" type="button" @click=${() => { this.dispatch({ type: 'RESET' }); this.syncLifted(); }}>${t('reset')}</button>` : nothing}
          ${st === 'lifted' ? html`<button class="quiet" type="button" @click=${() => this.dispatch({ type: 'PHOTOS' })}>${t('photos')}</button>
            <button class="quiet" type="button" @click=${() => this.dispatch({ type: 'PUT_BACK' })}>${t('putBack')}</button>` : nothing}
          ${st === 'shut' || st === 'open' || st === 'pulling' ? html`<button class="quiet close" type="button" @click=${() => this.dispatch({ type: 'CLOSE' })}>${t('close')}</button>` : nothing}
        </div>
      </div>
      </div>
    `;
  }
}

declare global { interface HTMLElementTagNameMap { 'drawer-view': DrawerView } }
