import {useEffect, useState} from 'react';
import {CastFrame} from '~/components/house/CastFrame';
import {DetailHold} from '~/components/house/DetailHold';
import {DropStatus, type DropView} from '~/components/house/DropStatus';
import {Entry} from '~/components/house/Entry';
import {ListForm} from '~/components/house/ListForm';
import {Manifesto} from '~/components/house/Manifesto';
import {ScaleCut} from '~/components/house/ScaleCut';
import {SensoryNotice} from '~/components/house/SensoryNotice';
import {ShotSlot} from '~/components/base/ShotSlot';
import {StageCard} from '~/components/house/StageCard';
import {copy} from '~/lib/copy';
import {cx} from '~/lib/cx';
import {listBody} from '~/lib/list-offer';
import {entryCookie} from '~/lib/entry';
import type {CastMember, StorefrontImage, StorefrontProduct} from '~/lib/mock/types';

export interface HomePageProps {
  products: StorefrontProduct[];
  drop: DropView | null;
  cast: CastMember[];
  /** F09's A6: the temple where the gold reads clearest (RUN.md, Edge cases). */
  detail: StorefrontImage | null;
  /** The small frontal composition's picture: F09's landscape hero. */
  dropHero: StorefrontImage | null;
  /** First visit to `/`: the notice, then the opening. */
  showEntry?: boolean;
  /** Wire mode shows the opening as a frame list at the top of the page. */
  wire?: boolean;
  /** Stories: the drop section after its cut. */
  cut?: boolean;
}

/** Home, in order (03-references.md): manifesto, the detail, the drop, the cast, the promises, the list. */
export function HomePage({products, drop, cast, detail, dropHero, showEntry = false, wire = false, cut = false}: HomePageProps) {
  const [entry, setEntry] = useState<'notice' | 'playing' | 'done'>(showEntry && !wire ? 'notice' : 'done');
  const [reducedMotion, setReducedMotion] = useState(false);
  useEffect(() => {
    setReducedMotion(window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }, []);
  useEffect(() => {
    if (entry === 'done') delete document.documentElement.dataset.opening;
    else document.documentElement.dataset.opening = 'playing';
    return () => {
      delete document.documentElement.dataset.opening;
    };
  }, [entry]);
  const finish = () => {
    document.cookie = entryCookie('seen');
    setEntry('done');
  };
  const byId = new Map(products.map((p) => [p.ds.id, p]));

  return (
    <main id="main" data-page="home">
      {entry === 'notice' ? <SensoryNotice onContinue={() => setEntry('playing')} onSkip={finish} /> : null}
      {entry === 'playing' ? <Entry reducedMotion={reducedMotion} onDone={finish} /> : null}
      {wire && showEntry ? <Entry wire onDone={() => undefined} /> : null}

      <Manifesto lines={copy.home.manifesto} variant="home" heading />

      <DetailHold shot="F09-A6" image={detail} line={copy.home.detail} />

      <ScaleCut
        initial={wire || cut ? 'bleed' : 'small'}
        small={
          <div className="grid w-full max-w-sm justify-items-center gap-8">
            <ShotSlot shot="F09-H" ratio="hero-landscape" image={dropHero} sizes="384px" className="w-full" />
            <DropStatus drop={drop} variant="small" />
          </div>
        }
        bleed={
          <div className="grid gap-10 px-4 py-16 md:px-6 lg:px-10 xl:px-14">
            <DropStatus drop={drop} variant="small" className="mx-auto max-w-md" />
            <ul className="grid grid-cols-1 gap-x-4 gap-y-10 md:grid-cols-2 lg:grid-cols-4" aria-label={copy.nav.frames}>
              {products.map((p, i) => (
                <li key={p.id}>
                  <StageCard product={p} drop={drop} priority={i < 2} />
                </li>
              ))}
            </ul>
          </div>
        }
      />

      <section aria-labelledby="home-cast" className="grid gap-8 py-16 md:px-6 lg:px-10 xl:px-14">
        <h2 id="home-cast" className="ds-display px-4 text-h2 leading-heading tracking-heading md:px-0">
          {copy.home.castTitle}
        </h2>
        {/* Seven portraits: two across with the seventh centred, four across with the last three centred (no empty cell). */}
        <ul className="grid gap-12 md:grid-cols-4 md:gap-6 lg:grid-cols-8">
          {cast.map((m, i) =>
            m.portrait ? (
              <li key={m.id} className={cx('md:col-span-2', i === 4 && 'lg:col-start-2', i === 6 && 'md:col-start-2 lg:col-start-auto')}>
                <CastFrame shot={m.portrait} product={byId.get(m.portrait.frame) ?? null} variant="card" />
              </li>
            ) : null,
          )}
        </ul>
        <p className="px-4 font-text text-small text-ds-text-tertiary md:px-0">{copy.product.imageDisclosure}</p>
      </section>

      <section aria-labelledby="home-promises" className="grid gap-8 px-4 py-16 md:px-6 lg:grid-cols-2 lg:px-10 xl:px-14">
        <h2 id="home-promises" className="ds-display text-h2 leading-heading tracking-heading">
          {copy.home.promisesTitle}
        </h2>
        <ul className="grid gap-3">
          {copy.home.promises.map((p) => (
            <li key={p} className="ds-tabular border-t border-ds-border-hairline py-3 font-text text-body-lg font-book text-ds-text-primary">
              {p}
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="home-list" className="grid gap-8 px-4 py-16 md:px-6 lg:grid-cols-2 lg:px-10 xl:px-14">
        <h2 id="home-list" className="ds-display text-h2 leading-heading tracking-heading">
          {copy.list.title}
        </h2>
        <div className="grid gap-4">
          <p className="font-text text-body text-ds-text-secondary">{listBody(drop ? {enabled: drop.earlyAccess.enabled, hours: drop.earlyAccess.hoursBeforePublic} : undefined)}</p>
          <ListForm scope="footer" />
        </div>
      </section>
    </main>
  );
}
