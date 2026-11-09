// The wall, alone (DRAWER-WALL.md). index.html runs the whole experience from the records: the tiers, ?open=,
// ?mech=, ?panel=1, ?debug=1 (D6 completes the flows; D5 lays the drawers over the plate).
import './styles/fonts.css';
import './styles/base.css';
import { WallStore } from './data/store';
import { enableLog, log } from './lib/log';
import { readSignals, tierFor, tierReasons, probeWebGL2, type Tier } from './lib/tier';
import type { ResolvedBay } from './lib/types';
import type { DrawerView, OpenRequest } from './elements/drawer-view';
import type { DrawerWall } from './elements/drawer-wall';
import type { BayOpenDetail } from './elements/drawer-bay';
import './elements/drawer-wall';

declare global {
  interface Window { __wall?: { store: WallStore; tier: Tier } }
}

const params = new URLSearchParams(location.search);
enableLog(params.get('debug') === '1');

let tier: Tier = 2;
let view: DrawerView | null = null;
let viewReady: Promise<DrawerView> | null = null;

/** The drawer view and what it needs load on the first open, never in the initial bundle; <lifted-frame> at every tier
 * (tier 1 shows the lifted still through it), three.js only inside its tier-2 setup. */
function loadView(store: WallStore, wall: DrawerWall): Promise<DrawerView> {
  if (!viewReady) {
    viewReady = (async () => {
      await Promise.all([import('./elements/drawer-view'), import('./elements/photo-zoom'), import('./elements/lifted-frame')]);
      const v = document.createElement('drawer-view');
      v.store = store;
      v.tier = tier;
      v.addEventListener('announce', ((ev: CustomEvent<{ text: string }>) => wall.announce(ev.detail.text)) as EventListener);
      v.addEventListener('tier-fallback', () => { tier = 1; v.tier = 1; if (window.__wall) window.__wall.tier = 1; log('tier', { tier, reason: 'context lost' }); });
      v.addEventListener('view-closed', ((ev: CustomEvent<{ id: string }>) => {
        const bay = wall.renderRoot.querySelector(`drawer-bay[data-id="${ev.detail.id}"]`)?.shadowRoot?.querySelector('button.face') as HTMLElement | null;
        bay?.focus({ preventScroll: true });
      }) as EventListener);
      document.body.append(v);
      view = v;
      return v;
    })();
  }
  return viewReady;
}

async function openBay(store: WallStore, wall: DrawerWall, bay: ResolvedBay, pointer: OpenRequest['pointer']): Promise<void> {
  const v = await loadView(store, wall);
  await v.show({ bay, pointer, from: wall.viewCropFor(bay.id) });
}

async function start(): Promise<void> {
  const store = await WallStore.load('./assets/');
  if (params.get('mech') === 'pull') store.setMechanic('pull');
  const signals = readSignals(navigator, () => probeWebGL2(document));
  tier = tierFor(signals);
  window.__wall = { store, tier };   // for the tests and the usability sessions' console
  const wall = document.querySelector('drawer-wall');
  if (!wall) return;
  wall.removeAttribute('data-placeholder');
  wall.store = store;
  wall.addEventListener('bay-open', ((ev: CustomEvent<BayOpenDetail>) => {
    const bay = store.bay(ev.detail.id);
    if (bay) void openBay(store, wall, bay, ev.detail.pointer);
  }) as EventListener);
  store.addEventListener('change', ((ev: CustomEvent<{ changed: string[] }>) => {
    for (const id of ev.detail.changed) { const b = store.bay(id); if (b && view) view.recordChanged(b); }
  }) as EventListener);
  log('start', { drawers: store.resolved.length, renderSet: store.assets.manifest.renderSet, mechanic: store.mechanic, tier, reasons: tierReasons(signals) });
  // the records panel (?panel=1): the simulated backend
  if (params.get('panel') === '1') {
    await import('./elements/records-panel');
    const panel = document.createElement('records-panel');
    panel.store = store;
    panel.addEventListener('panel-close', () => panel.remove());
    document.body.append(panel);
  }
  // a deep link (?open=F09, an id or a handle) opens that drawer's view on its last frame, not lifted; unknown opens nothing
  const open = params.get('open');
  if (open) {
    const bay = store.resolved.find((b) => b.frame && (b.frame.id.toLowerCase() === open.toLowerCase() || b.frame.handle === open));
    if (bay?.canOpen) {
      const v = await loadView(store, wall);
      await v.show({ bay, pointer: null, from: wall.viewCropFor(bay.id) });
      v.jumpOpen();
    } else log('open.unknown', { open });
  }
  wall.setAttribute('data-tier', String(tier));
  // ?debug=1: the event log's copy button, for the tests and the usability sessions
  if (params.get('debug') === '1') {
    const { logText, log: logEvent } = await import('./lib/log');
    const { t } = await import('./lib/copy');
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'debug-copy';
    b.textContent = t('debug.copy');
    b.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(logText()); b.textContent = t('debug.copied'); } catch { const ta = document.createElement('textarea'); ta.value = logText(); document.body.append(ta); ta.select(); }
      logEvent('debug.copied');
      setTimeout(() => { b.textContent = t('debug.copy'); }, 1500);
    });
    document.body.append(b);
  }
}

void start();
