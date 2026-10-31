import {Link} from 'react-router';
import {Price} from '~/components/base/Price';
import {ShotSlot} from '~/components/base/ShotSlot';
import {FilmGrain} from '~/components/house/FilmGrain';
import {LookNumber} from '~/components/house/LookNumber';
import {cx} from '~/lib/cx';
import type {CastShot, StorefrontProduct} from '~/lib/mock/types';

export interface CastFrameProps {
  shot: CastShot;
  product: StorefrontProduct | null;
  /** Full bleed, one per screen on a phone (/cast), or a card in a row (home). */
  variant?: 'bleed' | 'card';
  priority?: boolean;
  /** The `sizes` attribute for the picture's responsive set; the variant's default otherwise. */
  sizes?: string;
  className?: string;
}

/** A cast member wearing the frame, linked to it. No names: the codes are internal (RUN.md, Open questions). */
export function CastFrame({shot, product, variant = 'card', priority = false, sizes, className}: CastFrameProps) {
  return (
    <figure className={cx('grid gap-3', variant === 'bleed' && 'min-h-dvh content-center', className)} data-cast-frame={shot.code}>
      <ShotSlot shot={shot.code} ratio="stage" image={shot.image} surface="canvas" priority={priority} sizes={sizes ?? (variant === 'bleed' ? '100vw' : '(min-width: 1024px) 25vw, (min-width: 768px) 50vw, 100vw')}>
        {shot.image ? <FilmGrain /> : null}
      </ShotSlot>
      {product ? (
        <figcaption className="flex items-baseline gap-3 px-4 md:px-0">
          <LookNumber number={product.ds.lookNumber} />
          <Link to={`/frames/${product.handle}`} className="inline-block py-2.5 -my-2.5 font-text text-small text-ds-text-secondary hover:text-ds-text-primary hover:underline underline-offset-3">
            {product.title}
          </Link>
          <Price money={product.priceRange.minVariantPrice} variant="compact" className="text-ds-text-secondary" />
        </figcaption>
      ) : null}
    </figure>
  );
}
