import {Link} from 'react-router';
import {ShotSlot} from '~/components/base/ShotSlot';
import {LookNumber} from '~/components/house/LookNumber';
import {cx} from '~/lib/cx';
import type {CastShot, StorefrontProduct} from '~/lib/mock/types';

export interface CastFrameProps {
  shot: CastShot;
  product: StorefrontProduct | null;
  /** Full bleed, one per screen on a phone (/cast), or a card in a row (home). */
  variant?: 'bleed' | 'card';
  priority?: boolean;
  className?: string;
}

/** A cast member wearing the frame, linked to it. No names: the codes are internal (RUN.md, Open questions). */
export function CastFrame({shot, product, variant = 'card', priority = false, className}: CastFrameProps) {
  return (
    <figure className={cx('grid gap-3', variant === 'bleed' && 'min-h-dvh content-center', className)} data-cast-frame={shot.code}>
      <ShotSlot shot={shot.code} ratio="stage" image={shot.image} surface="canvas" priority={priority} sizes={variant === 'bleed' ? '100vw' : '(min-width: 1024px) 25vw, (min-width: 768px) 50vw, 100vw'} />
      {product ? (
        <figcaption className="flex items-baseline gap-3 px-4 md:px-0">
          <LookNumber number={product.ds.lookNumber} />
          <Link to={`/frames/${product.handle}`} className="font-text text-small text-ds-text-secondary hover:text-ds-text-primary hover:underline underline-offset-3">
            {product.title}
          </Link>
        </figcaption>
      ) : null}
    </figure>
  );
}
