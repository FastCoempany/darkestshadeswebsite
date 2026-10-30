import {Link} from 'react-router';
import {Button} from '~/components/base/Button';
import {Gallery} from '~/components/base/Gallery';
import {Price} from '~/components/base/Price';
import {ShotSlot} from '~/components/base/ShotSlot';
import {DetailHold} from '~/components/house/DetailHold';
import {dropSentence, type DropView} from '~/components/house/DropStatus';
import {LineDrawing} from '~/components/house/LineDrawing';
import {LookNumber} from '~/components/house/LookNumber';
import {PairsLeft} from '~/components/house/PairsLeft';
import {SpecSheet} from '~/components/house/SpecSheet';
import {lineFor, useCart} from '~/lib/cart';
import {copy, fill} from '~/lib/copy';
import type {CastShot, StorefrontProduct} from '~/lib/mock/types';

export interface FramePageProps {
  product: StorefrontProduct;
  drop: DropView | null;
  castShots: CastShot[];
  next: StorefrontProduct | null;
  /** The GCD's 3D render for F08, whose pictures show no GCD (00-decisions.md #34). */
  detailRender?: string | null;
}

/** Gallery beside a sticky buy panel, then the detail hold, specs, the drawings, worn by, next look (04). */
export function FramePage({product, drop, castShots, next, detailRender = null}: FramePageProps) {
  const {add} = useCart();
  const angles = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6'];
  const gallery = [
    ...angles.map((a) => ({shot: `${product.ds.id}-${a}`, ratio: 'stage' as const, image: product.images.nodes.find((i) => i.ds.kind === 'product' && i.ds.angle === a) ?? null})),
    ...castShots.map((s) => ({shot: s.code, ratio: 'stage' as const, image: s.image})),
  ];
  const inDrop = drop?.frames.includes(product.ds.id) ?? false;
  const left = drop?.inventory?.[product.ds.id] ?? null;
  const soldOut = drop?.state === 'sold-out' || (drop?.state === 'live' && left === 0);
  const a6 = product.images.nodes.find((i) => i.ds.angle === 'A6') ?? null;
  const subject = copy.alt.subjects[product.ds.id];

  return (
    <main id="main" data-page="frame" data-frame={product.ds.id}>
      <div className="grid gap-8 lg:grid-cols-[3fr_2fr] lg:gap-12 lg:px-10 xl:px-14">
        <Gallery items={gallery} label={fill(copy.product.galleryLabel, {name: product.title}) ?? product.title} counter={(i, t) => fill(copy.product.galleryCounter, {index: i, total: t}) ?? `${i} / ${t}`} labels={{previous: copy.product.galleryPrevious, next: copy.product.galleryNext}} />
        <aside className="grid content-start gap-6 px-4 md:px-6 lg:sticky lg:top-(--layout-header-lg) lg:self-start lg:px-0 lg:py-8" aria-label={product.title} data-buy-panel>
          <LookNumber number={product.ds.lookNumber} />
          <h1 className="ds-display text-h1 leading-heading tracking-heading">{product.title}</h1>
          <p className="font-text text-body text-ds-text-secondary">{product.ds.descriptor}</p>
          <Price money={product.priceRange.minVariantPrice} className="text-body-lg" />
          {drop && inDrop ? (
            <div className="grid gap-2">
              <p className="font-text text-small text-ds-text-secondary">{dropSentence(drop)}</p>
              <PairsLeft left={left} total={drop.pairsPerFrame} threshold={drop.threshold} />
            </div>
          ) : null}
          {drop?.state === 'live' && inDrop ? (
            <Button variant="solid" size={56} disabled={soldOut} onClick={() => add(lineFor(product, product.variants.nodes[0]), drop.limitPerCustomer)}>
              {soldOut ? copy.product.soldOut : copy.product.addToBag}
            </Button>
          ) : drop?.state === 'sold-out' && inDrop ? (
            <Button variant="solid" size={56} disabled>
              {copy.product.soldOut}
            </Button>
          ) : drop?.state === 'announced' && inDrop ? (
            <Button variant="solid" size={56} to={`/drops/${drop.number}`}>
              {copy.product.notify}
            </Button>
          ) : (
            <p className="font-text text-small text-ds-text-secondary">{copy.product.availability.nextDrop}</p>
          )}
          <ul className="grid gap-1 font-text text-small text-ds-text-secondary">
            {product.ds.promises.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </aside>
      </div>

      <DetailHold shot={`${product.ds.id}-A6`} image={detailRender ? null : a6} renderSrc={detailRender} line={copy.product.gcdLine} />

      <section aria-labelledby="frame-specs" className="grid gap-6 px-4 py-12 md:px-6 lg:grid-cols-[1fr_2fr] lg:px-10 xl:px-14">
        <h2 id="frame-specs" className="ds-display text-h2 leading-heading tracking-heading">
          {copy.product.specsTitle}
        </h2>
        <SpecSheet product={product} />
      </section>

      <section aria-labelledby="frame-drawn" className="grid gap-6 px-4 py-12 md:px-6 lg:px-10 xl:px-14">
        <h2 id="frame-drawn" className="ds-display text-h2 leading-heading tracking-heading">
          {copy.product.drawnTitle}
        </h2>
        <LineDrawing product={product} />
      </section>

      <section aria-labelledby="frame-worn" className="grid gap-6 px-4 py-12 md:px-6 lg:px-10 xl:px-14">
        <h2 id="frame-worn" className="ds-display text-h2 leading-heading tracking-heading">
          {copy.product.wornByTitle}
        </h2>
        <ul className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {castShots.map((s) => (
            <li key={s.code}>
              <ShotSlot shot={s.code} ratio="stage" image={s.image} surface="canvas" sizes="(min-width: 1024px) 25vw, 50vw" />
            </li>
          ))}
        </ul>
        <p className="font-text text-small text-ds-text-tertiary">{copy.product.imageDisclosure}</p>
      </section>

      {next ? (
        <section aria-labelledby="frame-next" className="grid gap-6 border-t border-ds-border-hairline px-4 py-12 md:px-6 lg:px-10 xl:px-14">
          <h2 id="frame-next" className="ds-display text-h2 leading-heading tracking-heading">
            {copy.product.nextLook}
          </h2>
          <Link to={`/frames/${next.handle}`} className="grid max-w-sm gap-3 rounded-none">
            <ShotSlot shot={`${next.ds.id}-A1`} ratio="stage" image={next.featuredImage} sizes="384px" />
            <span className="flex items-baseline gap-3">
              <LookNumber number={next.ds.lookNumber} />
              <span className="font-text text-body text-ds-text-primary">{next.title}</span>
            </span>
            <span className="sr-only">{subject}</span>
          </Link>
        </section>
      ) : null}
    </main>
  );
}
