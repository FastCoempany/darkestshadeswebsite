// The states sheet (DRAWER-WALL.md, The project; Testing): every element in every state, side by side, from
// fixtures: each drawer state, both lights, both mechanics, the view shut, pulling, open, lifted, turned, zoomed,
// the photographs, tier 1, reduced motion, 320 px. The review and screenshot sheet, the wall's stand-in for a
// component catalogue. Each asset's status shows in a corner tag.
import './styles/fonts.css';
import './styles/base.css';
import { LitElement, html, css, nothing } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { WallStore } from './data/store';
import { AssetIndex, isManifest, type Manifest } from './lib/manifest';
import { FRAMES } from './data/frames';
import { resolveBay } from './lib/resolve';
import { enableLog } from './lib/log';
import { t } from './lib/copy';
import type { DrawerBayRecord, ResolvedBay } from './lib/types';
import type { BayRects } from './elements/drawer-bay';
import type { DrawerView } from './elements/drawer-view';
import './elements/drawer-wall';
import './elements/drawer-bay';
import './elements/drawer-view';
import './elements/lifted-frame';
import './elements/photo-zoom';
import './elements/records-panel';

enableLog(new URLSearchParams(location.search).get('debug') === '1');

const BAY_FIXTURES: Array<[string, Partial<DrawerBayRecord>]> = [
  ['available, lit', { frame: 'F09', state: 'available', light: 'auto' }],
  ['sold out, dark', { frame: 'F01', state: 'sold_out', light: 'auto' }],
  ['locked', { frame: 'F03', state: 'locked', light: 'auto' }],
  ['hidden', { frame: 'F06', state: 'hidden', light: 'auto' }],
  ['available, light dark', { frame: 'F02', state: 'available', light: 'dark' }],
  ['sold out, light lit', { frame: 'F08', state: 'sold_out', light: 'lit' }],
  ['no frame (hidden, logged)', { frame: null, state: 'available', light: 'auto' }],
  ['unknown state (hidden, logged)', { frame: 'F04', state: 'soon', light: 'auto' }],
];
const RECT: BayRects = { face: { x: 8, y: 6, w: 84, h: 44 }, knob: { x: 42, y: 20, w: 16, h: 18 }, label: { x: 8, y: 56, w: 84, h: 40 }, crop: { x: 3, y: 1, w: 94, h: 54 } };
const VIEW_STATES = ['shut', 'pulling', 'open', 'lifted', 'turned', 'zoomed', 'photos', 'tier 1 lifted', 'reduced motion'] as const;

@customElement('states-sheet')
export class StatesSheet extends LitElement {
  static override styles = css`
    :host { display: block; padding: var(--space-4); padding-left: max(var(--space-4), env(safe-area-inset-left, 0px)); padding-right: max(var(--space-4), env(safe-area-inset-right, 0px)); }
    h1 { font-size: var(--font-size-h2); font-weight: var(--font-weight-light); margin: 0 0 var(--space-4); }
    h2 { font-size: 11px; font-weight: var(--font-weight-medium); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; color: var(--color-text-secondary); margin: var(--space-8) 0 var(--space-3); }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--space-4); }
    .grid.views { grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
    figure { margin: 0; display: grid; gap: var(--space-2); min-width: 0; }
    figcaption { font-size: 11px; letter-spacing: var(--font-tracking-micro); text-transform: uppercase; color: var(--color-text-tertiary); display: flex; justify-content: space-between; gap: var(--space-2); }
    .tag { color: var(--color-text-editorial); }
    .bay-box { position: relative; aspect-ratio: 220 / 230; background: var(--color-surface-base); overflow: visible; }
    .narrow { width: 320px; max-width: 100%; }
    .view-box { position: relative; width: 100%; aspect-ratio: 390 / 844; overflow: hidden; background: var(--color-surface-base); }
    .view-box drawer-view { position: absolute; }
    .wall-box { max-width: 585px; }
    .panel-box { position: relative; height: 420px; overflow: hidden; }
    .panel-box records-panel { position: absolute; width: 100%; }
    pre { font-size: 11px; color: var(--color-text-tertiary); white-space: pre-wrap; }
  `;

  @state() private store: WallStore | null = null;
  @state() private status: Record<string, string> = {};

  override connectedCallback(): void {
    super.connectedCallback();
    void this.load();
  }

  private async load(): Promise<void> {
    let manifest: Manifest = { renderSet: 'none', assets: [] };
    try { const j: unknown = await (await fetch('./assets/manifest.json')).json(); if (isManifest(j)) manifest = j; } catch { /* no manifest: the sheet still shows the elements */ }
    const idx = new AssetIndex(manifest, './assets/');
    for (const e of manifest.assets) this.status[e.kind] = e.status;
    this.store = new WallStore(idx);
    window.__states = { store: this.store };
  }

  private bay(over: Partial<DrawerBayRecord>): ResolvedBay {
    const rec: DrawerBayRecord = { id: `drawer_bay/${String(over.frame ?? 'x').toLowerCase()}`, handle: 'x', frame: 'F09', state: 'available', light: 'auto', note: null, ...over };
    return resolveBay(rec, FRAMES, this.store!.assets);
  }

  private darkSrc(): { avif: string; webp: string } | null {
    const s = this.store!;
    const d = s.assets.darkCrop('portrait', s.knobStyle, 0);
    return d ? { avif: s.assets.url(s.assets.file(d, 'avif')!), webp: s.assets.url(s.assets.file(d, 'webp')!) } : null;
  }

  protected override async updated(): Promise<void> {
    if (!this.store) return;
    // the views: each put into its state from the fixture (the sheet's own path, not a user's)
    for (const v of this.renderRoot.querySelectorAll<DrawerView & { fixture?: string }>('drawer-view[data-fixture]')) {
      const name = v.getAttribute('data-fixture') ?? '';
      if (v.fixture === name) continue;
      v.fixture = name;
      const bay = this.bay({ frame: 'F09', state: 'available' });
      await v.showFixture(bay, name);
    }
  }

  override render() {
    const s = this.store;
    if (!s) return html`<h1>${t('title')}</h1>`;
    const tag = (kind: string) => this.status[kind] ?? 'none';
    return html`
      <h1>${t('title')} · states</h1>
      <h2>drawer-bay</h2>
      <div class="grid">
        ${BAY_FIXTURES.map(([name, over]) => html`<figure><div class="bay-box"><drawer-bay .bay=${this.bay(over)} .rects=${RECT} .darkSrc=${this.darkSrc()} .plateSize=${{ width: 220, height: 230 }}></drawer-bay></div><figcaption><span>${name}</span><span class="tag">${tag('wall-dark')}</span></figcaption></figure>`)}
        <figure><div class="bay-box"><drawer-bay .bay=${this.bay({ frame: 'F05' })} .rects=${RECT} .darkSrc=${this.darkSrc()} mechanic="pull" .plateSize=${{ width: 220, height: 230 }}></drawer-bay></div><figcaption><span>pull first (the knob's target)</span></figcaption></figure>
        <figure class="narrow"><div class="bay-box"><drawer-bay .bay=${this.bay({ frame: 'F02' })} .rects=${RECT} .darkSrc=${null} .plateSize=${{ width: 320, height: 334 }}></drawer-bay></div><figcaption><span>320 px, the longest name</span></figcaption></figure>
      </div>
      <h2>drawer-wall</h2>
      <div class="wall-box"><drawer-wall .store=${s}></drawer-wall></div>
      <figcaption><span>the portrait wall from the records</span><span class="tag">${tag('wall-plate')}</span></figcaption>
      <h2>drawer-view</h2>
      <div class="grid views">
        ${VIEW_STATES.map((name) => html`<figure><div class="view-box"><drawer-view inline .store=${s} data-fixture=${name}></drawer-view></div><figcaption><span>${name}</span><span class="tag">${name.includes('lifted') || name === 'turned' || name === 'zoomed' ? tag('glb') : tag('sequence-frame')}</span></figcaption></figure>`)}
      </div>
      <h2>records-panel</h2>
      <div class="panel-box"><records-panel .store=${s}></records-panel></div>
      <h2>the resolver's log</h2>
      <pre>${s.resolved.flatMap((b) => b.problems).join('\n') || 'no problems in the committed records'}</pre>
    `;
  }
}

declare global { interface Window { __states?: { store: WallStore } } interface HTMLElementTagNameMap { 'states-sheet': StatesSheet } }
