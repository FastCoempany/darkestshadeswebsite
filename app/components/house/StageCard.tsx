import {Link} from 'react-router';
import {Price} from '~/components/base/Price';
import {ShotSlot} from '~/components/base/ShotSlot';
import type {DropView} from '~/lib/drop-view';
import {LookNumber} from '~/components/house/LookNumber';
import {pairsLeftText} from '~/components/house/PairsLeft';
import {copy, fill} from '~/lib/copy';
import {cx} from '~/lib/cx';
import type {StorefrontProduct} from '~/lib/mock/types';

export interface StageCardProps {
  product: StorefrontProduct;
  drop: DropView | null;
  /** Load the image eagerly (above the fold). */
  priority?: boolean;
  sizes?: string;
  /** h2 on pages whose only heading above is the title; h3 inside a titled section. */
  heading?: 'h2' | 'h3';
  className?: string;
}

/** The availability word on a card: "In Drop 001", "Sold out", "Next drop" (04). */
export function availabilityWord(product: StorefrontProduct, drop: DropView | null): string | null {
  if (!drop) return null;
  const inDrop = drop.frames.includes(product.ds.id);
  if (!inDrop) return copy.product.availability.nextDrop;
  const left = drop.inventory?.[product.ds.id];
  if (drop.state === 'sold-out' || (drop.state === 'live' && left === 0)) return copy.product.availability.soldOut;
  if (drop.state === 'ended') return copy.product.availability.nextDrop;
  return fill(copy.product.availability.inDrop, {number: drop.number});
}

/**
 * A frame on the stage color, like a print on a dark wall: look number, the front angle (the
 * three-quarter on hover or focus), name, descriptor, $100, the availability word, pairs left when real.
 */
export function StageCard({product, drop, priority = false, sizes = '(min-width: 1024px) 25vw, (min-width: 768px) 50vw, 100vw', heading: Heading = 'h3', className}: StageCardProps) {
  const a1 = product.images.nodes.find((i) => i.ds.angle === 'A1') ?? null;
  const a2 = product.images.nodes.find((i) => i.ds.angle === 'A2') ?? null;
  const word = availabilityWord(product, drop);
  const pairs = drop?.state === 'live' ? pairsLeftText({left: drop.inventory?.[product.ds.id] ?? null, total: drop.pairsPerFrame, threshold: drop.threshold}) : null;
  const soldOut = word === copy.product.availability.soldOut;
  return (
    <article className={cx('group grid gap-3', className)} data-stage-card={product.ds.id} data-sold-out={soldOut || undefined}>
      <Link to={`/frames/${product.handle}`} className="relative block rounded-none" aria-label={`${product.ds.lookNumber} · ${product.title}`}>
        <ShotSlot shot={`${product.ds.id}-A1`} ratio="stage" image={a1} sizes={sizes} priority={priority} />
        {a2 ? (
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 motion-safe:transition-opacity motion-safe:duration-(--motion-quick)" aria-hidden="true">
            <ShotSlot shot={`${product.ds.id}-A2`} ratio="stage" image={a2} sizes={sizes} />
          </div>
        ) : null}
      </Link>
      <div className="grid gap-1">
        <LookNumber number={product.ds.lookNumber} />
        <Heading className="font-text text-body text-ds-text-primary">
          {/* A 44 px hit area (05 Accessibility) that costs the card no height: the padding is given back by the margins. */}
          <Link to={`/frames/${product.handle}`} className="inline-block py-2.5 -my-2.5 hover:underline underline-offset-3">
            {product.title}
          </Link>
        </Heading>
        <p className="font-text text-small text-ds-text-secondary">{product.ds.descriptor}</p>
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <Price money={product.priceRange.minVariantPrice} />
          {word ? <span className={cx('font-text text-small', soldOut ? 'text-ds-text-tertiary' : 'text-ds-text-secondary')}>{word}</span> : null}
        </div>
        {pairs ? <p className="ds-tabular font-text text-small text-ds-text-secondary">{pairs}</p> : null}
      </div>
    </article>
  );
}
