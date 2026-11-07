// <records-panel> (DRAWER-WALL.md, Every drawer is its own thing): the simulated backend behind ?panel=1, labelled
// "Records (example data)". The founder changes any drawer's record (its frame, state and light) and sees that
// drawer, and only that drawer, change; the ?mech= choice sits here too. Nothing here ships to a store: it edits
// the in-memory records through the store's update(), the same path a store's answer would take.
import { LitElement, html, css, nothing } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import type { Mechanic, WallStore } from '../data/store';
import { BAY_LIGHTS, BAY_STATES, FRAME_IDS, type Metaobject } from '../lib/types';
import { t } from '../lib/copy';

@customElement('records-panel')
export class RecordsPanel extends LitElement {
  static override styles = css`
    :host { position: fixed; right: 0; top: 0; bottom: 0; width: min(100vw, 22rem); z-index: 20; background: var(--color-surface-raised); color: var(--color-text-primary); overflow: auto; border-left: var(--border-hairline) solid var(--color-border-hairline);
      padding: var(--space-4); padding-top: calc(var(--space-4) + env(safe-area-inset-top, 0px)); padding-right: max(var(--space-4), env(safe-area-inset-right, 0px)); font-size: var(--font-size-small); }
    h2 { font-size: 11px; font-weight: var(--font-weight-medium); letter-spacing: var(--font-tracking-micro); text-transform: uppercase; color: var(--color-text-secondary); margin: 0 0 var(--space-3); }
    fieldset { border: 0; padding: 0; margin: 0 0 var(--space-4); display: grid; gap: var(--space-2); }
    legend { font-size: var(--font-size-small); padding: 0; margin-bottom: var(--space-1); color: var(--color-text-primary); }
    label { display: grid; grid-template-columns: 4.5rem 1fr; align-items: center; gap: var(--space-2); color: var(--color-text-secondary); }
    select { font: inherit; color: var(--color-text-primary); background: var(--color-surface-base); border: var(--border-hairline) solid var(--color-border-control); padding: var(--space-1) var(--space-2); min-height: 44px; }
    select:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); outline-offset: var(--border-focus-offset); }
    button { appearance: none; background: none; border: 0; border-bottom: var(--border-hairline) solid var(--color-border-rule); color: var(--color-text-secondary); font: inherit; font-size: 11px; letter-spacing: var(--font-tracking-micro); text-transform: uppercase; min-height: 44px; cursor: pointer; }
    button:focus-visible { outline: var(--border-focus) solid var(--color-focus-ring); outline-offset: var(--border-focus-offset); }
    .head { display: flex; justify-content: space-between; align-items: baseline; }
  `;

  @property({ attribute: false }) store: WallStore | null = null;
  @state() private tick = 0;
  private onChange = () => { this.tick++; };

  override connectedCallback(): void {
    super.connectedCallback();
    this.store?.addEventListener('change', this.onChange);
    this.store?.addEventListener('mechanic', this.onChange);
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.store?.removeEventListener('change', this.onChange);
    this.store?.removeEventListener('mechanic', this.onChange);
  }

  private set(id: string, key: 'frame' | 'state' | 'light', value: string): void {
    const s = this.store;
    const r = s?.record(id);
    if (!s || !r) return;
    const fields = r.fields.map((f) => (f.key === key ? { ...f, value: value === '' ? null : value } : f));
    const changed: Metaobject = { ...r, fields };
    s.update(changed);
  }

  override render() {
    const s = this.store;
    if (!s) return nothing;
    return html`
      <div class="head"><h2 id="panel-title">${t('panel.title')}</h2><button type="button" @click=${() => this.dispatchEvent(new CustomEvent('panel-close', { bubbles: true, composed: true }))}>${t('panel.close')}</button></div>
      <fieldset>
        <legend>${t('panel.mechanic')}</legend>
        <label><span>${t('panel.mechanic')}</span>
          <select @change=${(ev: Event) => s.setMechanic((ev.target as HTMLSelectElement).value as Mechanic)}>
            <option value="tap" ?selected=${s.mechanic === 'tap'}>${t('panel.tapFirst')}</option>
            <option value="pull" ?selected=${s.mechanic === 'pull'}>${t('panel.pullFirst')}</option>
          </select></label>
      </fieldset>
      ${s.records.order.map((b) => html`<fieldset data-id=${b.id}>
        <legend>${b.id}</legend>
        <label><span>${t('panel.frame')}</span>
          <select @change=${(ev: Event) => this.set(b.id, 'frame', (ev.target as HTMLSelectElement).value)}>
            <option value="" ?selected=${b.frame === null}>—</option>
            ${FRAME_IDS.map((f) => html`<option value=${f} ?selected=${b.frame === f}>${f}</option>`)}
          </select></label>
        <label><span>${t('panel.state')}</span>
          <select @change=${(ev: Event) => this.set(b.id, 'state', (ev.target as HTMLSelectElement).value)}>
            <option value="" ?selected=${b.state === null}>—</option>
            ${BAY_STATES.map((v) => html`<option value=${v} ?selected=${b.state === v}>${v}</option>`)}
          </select></label>
        <label><span>${t('panel.light')}</span>
          <select @change=${(ev: Event) => this.set(b.id, 'light', (ev.target as HTMLSelectElement).value)}>
            <option value="" ?selected=${b.light === null}>—</option>
            ${BAY_LIGHTS.map((v) => html`<option value=${v} ?selected=${b.light === v}>${v}</option>`)}
          </select></label>
      </fieldset>`)}
    `;
  }
}

declare global { interface HTMLElementTagNameMap { 'records-panel': RecordsPanel } }
