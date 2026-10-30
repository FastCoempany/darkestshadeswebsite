import type {ReactNode} from 'react';
import {cx} from '~/lib/cx';
import type {StorefrontImage} from '~/lib/mock/types';

export type Ratio = 'stage' | 'hero-landscape' | 'print' | 'mobile-hero' | 'desktop-hero' | 'square';

/** Tailwind needs the class names in full. */
const RATIO_CLASS: Record<Ratio, string> = {
  stage: 'aspect-stage',
  'hero-landscape': 'aspect-hero-landscape',
  print: 'aspect-print',
  'mobile-hero': 'aspect-mobile-hero',
  'desktop-hero': 'aspect-desktop-hero',
  square: 'aspect-square',
};

export const RATIO_LABEL: Record<Ratio, string> = {
  stage: '4:5',
  'hero-landscape': '3:2',
  print: '3:4',
  'mobile-hero': '9:16',
  'desktop-hero': '16:9',
  square: '1:1',
};

export interface ShotSlotProps {
  /** Shot code, e.g. `F01-A2`, `F01-H`, `W2-S06-F09-A2`. Shown in wire mode and while the final is missing. */
  shot: string;
  ratio: Ratio;
  /** The final from the manifest, or null: a labelled slot (CLAUDE.md, Imagery). */
  image?: StorefrontImage | null;
  /** Overrides the manifest's alt text. */
  alt?: string;
  /** The `sizes` attribute for the responsive set. */
  sizes?: string;
  /** Load eagerly and at high priority (the first image on the page). */
  priority?: boolean;
  /** Products sit on the stage color; photographs of people sit on the canvas. */
  surface?: 'stage' | 'canvas';
  className?: string;
  imgClassName?: string;
  children?: ReactNode;
}

/**
 * Every image on the site goes through ShotSlot (docs/brief/05-components.md): a fixed ratio from a
 * token so layouts never jump, the shot code and ratio as a label when the final is missing or in wire
 * mode, and the responsive set (AVIF, then WebP, then JPEG) from the manifest when it exists.
 */
export function ShotSlot({
  shot,
  ratio,
  image = null,
  alt,
  sizes = '100vw',
  priority = false,
  surface = 'stage',
  className,
  imgClassName,
  children,
}: ShotSlotProps) {
  const label = `${shot} · ${RATIO_LABEL[ratio]}`;
  return (
    <div
      className={cx(
        'relative overflow-hidden',
        RATIO_CLASS[ratio],
        surface === 'stage' ? 'bg-ds-surface-stage' : 'bg-ds-surface-base',
        className,
      )}
      data-shot={label}
      data-shot-state={image ? 'loaded' : 'empty'}
    >
      {image ? (
        <picture>
          {image.ds.formats.includes('avif') && <source type="image/avif" srcSet={image.ds.srcset.avif} sizes={sizes} />}
          {image.ds.formats.includes('webp') && <source type="image/webp" srcSet={image.ds.srcset.webp} sizes={sizes} />}
          <img
            className={cx('absolute inset-0 h-full w-full object-cover', imgClassName)}
            src={image.url}
            srcSet={image.ds.srcset.jpg}
            sizes={sizes}
            width={image.width}
            height={image.height}
            alt={alt ?? image.altText}
            loading={priority ? 'eager' : 'lazy'}
            decoding={priority ? 'sync' : 'async'}
            // React 18 knows the attribute only in lowercase.
            {...(priority ? {fetchpriority: 'high'} : {})}
          />
        </picture>
      ) : (
        <span
          className={cx(
            'absolute inset-0 grid place-items-center font-text text-micro font-medium uppercase tracking-micro',
            surface === 'stage' ? 'text-ds-text-inverse' : 'text-ds-text-secondary',
          )}
          aria-hidden="true"
        >
          {label}
        </span>
      )}
      {children}
    </div>
  );
}
