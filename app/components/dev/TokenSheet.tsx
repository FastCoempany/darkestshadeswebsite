import {ShotSlot} from '~/components/base/ShotSlot';
import {BrandMark} from '~/components/house/BrandMark';
import {Logo} from '~/components/house/Logo';
import {Seal} from '~/components/house/Seal';
import type {FrameId, StorefrontImage} from '~/lib/mock/types';

/**
 * The token sheet: every role token, type role, mark and media ratio on one page, so the foundation
 * can be checked by eye and by the font test. A development view, not a page of the site: it shows
 * several gold elements and several GCDs at once on purpose.
 */

const SURFACES = ['canvas', 'base', 'raised', 'overlay', 'inverse', 'stage'] as const;
const SURFACE_CLASS: Record<(typeof SURFACES)[number], string> = {
  canvas: 'bg-ds-surface-canvas',
  base: 'bg-ds-surface-base',
  raised: 'bg-ds-surface-raised',
  overlay: 'bg-ds-surface-overlay',
  inverse: 'bg-ds-surface-inverse',
  stage: 'bg-ds-surface-stage',
};

const TEXTS = ['primary', 'secondary', 'tertiary', 'disabled', 'accent', 'editorial'] as const;
const TEXT_CLASS: Record<(typeof TEXTS)[number], string> = {
  primary: 'text-ds-text-primary',
  secondary: 'text-ds-text-secondary',
  tertiary: 'text-ds-text-tertiary',
  disabled: 'text-ds-text-disabled',
  accent: 'text-ds-text-accent',
  editorial: 'text-ds-text-editorial',
};

const STATUS = ['success', 'error', 'info', 'live'] as const;
const STATUS_CLASS: Record<(typeof STATUS)[number], string> = {
  success: 'text-ds-status-success',
  error: 'text-ds-status-error',
  info: 'text-ds-status-info',
  live: 'text-ds-status-live',
};

const TYPE_ROLES: {role: string; face: string; className: string; sample: string}[] = [
  {role: 'manifesto', face: 'Owners Wide Medium (stand-in: Mona Sans)', className: 'ds-display text-manifesto leading-manifesto tracking-display', sample: 'See everything.'},
  {role: 'display', face: 'Owners Wide Medium', className: 'ds-display text-display leading-display tracking-display', sample: 'Drop 001'},
  {role: 'h1', face: 'Owners Wide Medium', className: 'ds-display text-h1 leading-heading tracking-heading', sample: 'Lou Went Underground'},
  {role: 'h2', face: 'Owners Wide Medium', className: 'ds-display text-h2 leading-heading tracking-heading', sample: 'Specs'},
  {role: 'label', face: 'Owners Wide Medium', className: 'ds-display text-label leading-ui tracking-label', sample: 'Worn by'},
  {role: 'body-lg', face: 'Stolzl Book (stand-in: Urbanist)', className: 'font-text text-body-lg font-book leading-body', sample: 'Every pair carries one mark worth finding: gold, set with black onyx.'},
  {role: 'body', face: 'Stolzl Book', className: 'font-text text-body font-book leading-body', sample: 'We make sunglasses for people who decide what gets seen.'},
  {role: 'ui', face: 'Stolzl Regular / Medium', className: 'font-text text-ui font-medium leading-ui', sample: 'Add to bag'},
  {role: 'micro', face: 'Stolzl Medium, uppercase', className: 'font-text text-micro font-medium uppercase leading-ui tracking-micro', sample: 'Drop 001 · Announced'},
  {role: 'card', face: 'Stolzl Regular', className: 'font-text text-card font-regular leading-ui', sample: 'Reveal nothing.'},
  {role: 'light', face: 'Stolzl Light, 22 px and up', className: 'font-text text-h2 font-light leading-heading', sample: 'Presence is not a performance.'},
  {role: 'price', face: 'Stolzl Book, tabular figures', className: 'font-text text-body font-book ds-tabular', sample: '$100 · 54□22 145'},
];

function Section({title, children}: {title: string; children: React.ReactNode}) {
  return (
    <section className="grid gap-6 border-t border-ds-border-hairline py-12">
      <h2 className="ds-display text-label leading-ui tracking-label text-ds-text-secondary">{title}</h2>
      {children}
    </section>
  );
}

export function TokenSheet({
  frames,
  hero,
}: {
  frames: {id: FrameId; look: string; name: string; image: StorefrontImage | null}[];
  hero: StorefrontImage | null;
}) {
  return (
    <main id="main" className="mx-auto grid max-w-(--layout-max) gap-8 px-4 py-16 md:px-6 lg:px-10 xl:px-14">
      <header className="grid gap-4">
        <p className="font-text text-micro font-medium uppercase tracking-micro text-ds-text-editorial">Phase 0 · Token sheet</p>
        <h1 className="ds-display text-h1 leading-heading tracking-heading">Darkest Shades foundation</h1>
        <p className="ds-measure text-ds-text-secondary">
          Role tokens, type roles, the marks and the media ratios, as the app renders them. Switch to wire mode with
          <code className="mx-1 font-text text-small text-ds-text-primary">?mode=wire</code>.
        </p>
      </header>

      <Section title="Marks">
        <div className="grid gap-8">
          <Logo variant="horizontal" height={28} />
          <Logo variant="stacked" height={96} />
          <BrandMark height={48} />
        </div>
      </Section>

      <Section title="Seal · three size steps">
        <div className="flex flex-wrap items-end gap-12">
          <Seal width={32} />
          <Seal width={96} />
          <Seal width={240} />
        </div>
      </Section>

      <Section title="Type">
        <dl className="grid gap-8">
          {TYPE_ROLES.map((t) => (
            <div key={t.role} className="grid gap-2">
              <dt className="font-text text-micro font-medium uppercase tracking-micro text-ds-text-tertiary">
                {t.role} · {t.face}
              </dt>
              <dd className={t.className} data-font-role={t.role}>
                {t.sample}
              </dd>
            </div>
          ))}
        </dl>
      </Section>

      <Section title="Surfaces and text">
        <div className="grid grid-cols-2 gap-px bg-ds-border-hairline md:grid-cols-3 xl:grid-cols-6">
          {SURFACES.map((s) => (
            <div key={s} className={`${SURFACE_CLASS[s]} aspect-square p-3`}>
              <span className={`font-text text-micro font-medium uppercase tracking-micro ${s === 'inverse' || s === 'stage' ? 'text-ds-text-inverse' : 'text-ds-text-primary'}`}>
                surface-{s}
              </span>
            </div>
          ))}
        </div>
        <ul className="grid gap-2">
          {TEXTS.filter((t) => t !== 'disabled').map((t) => (
            <li key={t} className={`${TEXT_CLASS[t]} font-text text-body`}>
              text-{t}: Forty-five days to exchange. Six months of warranty.
            </li>
          ))}
          <li>
            {/* Disabled text only ever sits on an inactive control, which WCAG exempts from contrast (RUN.md, Edge cases). */}
            <button type="button" disabled className={`${TEXT_CLASS.disabled} font-text text-ui font-medium`}>
              text-disabled: Sold out
            </button>
          </li>
          {STATUS.map((s) => (
            <li key={s} className={`${STATUS_CLASS[s]} font-text text-ui font-medium`}>
              status-{s}
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Paper theme">
        <div data-theme="paper" className="grid gap-4 bg-ds-surface-canvas p-6 text-ds-text-primary">
          <p className="ds-display text-h2 leading-heading tracking-heading">Manifesto</p>
          <p className="ds-measure text-ds-text-secondary">Real power doesn&apos;t ask for attention. It controls it.</p>
          <p className="font-text text-micro font-medium uppercase tracking-micro text-ds-text-editorial">01 · Look number in camel ink</p>
          <Seal width={96} surface="paper" />
        </div>
      </Section>

      <Section title="Media ratios · ShotSlot">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {frames.slice(0, 4).map((f) => (
            <ShotSlot key={f.id} shot={`${f.id}-A1`} ratio="stage" image={f.image} sizes="(min-width: 768px) 25vw, 50vw" />
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <ShotSlot shot="F09-H" ratio="hero-landscape" image={hero} sizes="(min-width: 768px) 50vw, 100vw" />
          <ShotSlot shot="W3-S02-F09-A1" ratio="stage" image={null} surface="canvas" />
        </div>
      </Section>

      <Section title="Spacing">
        <div className="flex flex-wrap items-end gap-2">
          {['1', '2', '3', '4', '6', '8', '12', '16', '24'].map((s) => (
            <div key={s} className="grid gap-1">
              <div className="bg-ds-text-accent" style={{width: `var(--space-${s})`, height: `var(--space-${s})`}} />
              <span className="font-text text-micro text-ds-text-tertiary">{s}</span>
            </div>
          ))}
        </div>
      </Section>
    </main>
  );
}
