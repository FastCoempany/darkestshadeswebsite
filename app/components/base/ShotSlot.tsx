import {useEffect, useRef, useState, type ReactNode} from 'react';
import {cx} from '~/lib/cx';
import type {StorefrontImage} from '~/lib/mock/types';

export type Ratio = 'stage' | 'hero-landscape' | 'print' | 'mobile-hero' | 'desktop-hero' | 'square';
export type ShotState = 'loading' | 'loaded' | 'error' | 'empty';

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

export function slotLabel(shot: string, ratio: Ratio, count?: number): string {
  return count ? `${shot} · ${count} · ${RATIO_LABEL[ratio]}` : `${shot} · ${RATIO_LABEL[ratio]}`;
}

export interface ShotSlotProps {
  /** Shot code, e.g. `F01-A2`, `F01-H`, `W2-S06-F09-A2`. Shown in wire mode and while the final is missing. */
  shot: string;
  ratio: Ratio;
  /** The final from the manifest, or null: a labelled slot (CLAUDE.md, Imagery). */
  image?: StorefrontImage | null;
  /** `image`: one picture. `sequence`: a run of stills (the entry's bursts); the label carries the count. */
  variant?: 'image' | 'sequence';
  /** Frames in a sequence, for the label. */
  count?: number;
  /** Overrides the manifest's alt text. */
  alt?: string;
  /** The `sizes` attribute for the responsive set. */
  sizes?: string;
  /** Load eagerly and at high priority (the first image on the page). */
  priority?: boolean;
  /** Products sit on the stage color; photographs of people on the base surface; `bare` paints nothing (a render set straight on the canvas). */
  surface?: 'stage' | 'canvas' | 'bare';
  /** Forces a state: `loading` before the picture arrives, `error` when it fails (stories); `loaded` when the children are the picture. */
  state?: ShotState;
  /** 1 (default) or 2: the picture at twice its size inside the frame, panned by scrolling (the gallery's zoom). */
  zoom?: 1 | 2;
  /** The zoomed frame's accessible name (it becomes a focusable scroll region). */
  zoomLabel?: string;
  className?: string;
  imgClassName?: string;
  children?: ReactNode;
}

/**
 * Every image on the site goes through ShotSlot (docs/brief/05-components.md): a fixed ratio from a
 * token so layouts never jump, the shot code and ratio as a label when the final is missing or in wire
 * mode, and the responsive set (AVIF, then WebP, then JPEG) from the manifest when it exists.
 * States: loading (the stage color), loaded, error (the label, in the error tone), empty (the label).
 */
export function ShotSlot({
  shot,
  ratio,
  image = null,
  variant = 'image',
  count,
  alt,
  sizes = '100vw',
  priority = false,
  surface = 'stage',
  state: forced,
  zoom = 1,
  zoomLabel,
  className,
  imgClassName,
  children,
}: ShotSlotProps) {
  const img = useRef<HTMLImageElement>(null);
  const frame = useRef<HTMLDivElement>(null);
  const [own, setOwn] = useState<ShotState>(image ? 'loading' : 'empty');

  // The load event can fire before React attaches onLoad (cached or fast files): read the element's state.
  useEffect(() => {
    if (!image) {
      setOwn('empty');
      return;
    }
    const el = img.current;
    if (el?.complete) setOwn(el.naturalWidth > 0 ? 'loaded' : 'error');
    else setOwn('loading');
  }, [image?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Zoom opens on the picture's centre.
  useEffect(() => {
    const el = frame.current;
    if (!el || zoom === 1) return;
    el.scrollTo({left: (el.scrollWidth - el.clientWidth) / 2, top: (el.scrollHeight - el.clientHeight) / 2});
  }, [zoom]);

  const state: ShotState = forced ?? (image ? own : 'empty');
  const label = slotLabel(shot, ratio, variant === 'sequence' ? count : undefined);
  const showLabel = state === 'empty' || state === 'error';
  return (
    <div
      ref={frame}
      className={cx(
        'relative',
        zoom > 1 ? 'overflow-auto overscroll-contain' : 'overflow-hidden',
        RATIO_CLASS[ratio],
        surface === 'stage' ? 'bg-ds-surface-stage' : surface === 'canvas' ? 'bg-ds-surface-base' : null,
        className,
      )}
      data-shot={label}
      data-shot-state={state}
      data-shot-variant={variant}
      data-zoom={zoom > 1 ? zoom : undefined}
      // A zoomed frame is a scrollable region: focusable and named (WCAG 2.1.1).
      tabIndex={zoom > 1 ? 0 : undefined}
      role={zoom > 1 ? 'region' : undefined}
      aria-label={zoom > 1 ? zoomLabel : undefined}
    >
      {image && state !== 'error' ? (
        <picture key={image.id} className={cx('block', zoom > 1 ? 'h-[200%] w-[200%]' : 'absolute inset-0')}>
          {image.ds.formats.includes('avif') && <source type="image/avif" srcSet={image.ds.srcset.avif} sizes={sizes} />}
          {image.ds.formats.includes('webp') && <source type="image/webp" srcSet={image.ds.srcset.webp} sizes={sizes} />}
          <img
            ref={img}
            className={cx('h-full w-full object-cover', imgClassName)}
            src={image.url}
            srcSet={image.ds.srcset.jpg}
            sizes={sizes}
            width={image.width}
            height={image.height}
            alt={alt ?? image.altText}
            loading={priority ? 'eager' : 'lazy'}
            decoding={priority ? 'sync' : 'async'}
            onLoad={() => setOwn('loaded')}
            onError={() => setOwn('error')}
            // React 18 knows the attribute only in lowercase.
            {...(priority ? {fetchpriority: 'high'} : {})}
          />
        </picture>
      ) : null}
      {showLabel ? (
        <span
          className={cx(
            'absolute inset-0 grid place-items-center px-2 text-center font-text text-micro font-medium uppercase tracking-micro',
            state === 'error' ? (surface === 'stage' ? 'text-ds-status-error-stage' : 'text-ds-status-error') : surface === 'stage' ? 'text-ds-text-on-stage' : 'text-ds-text-secondary',
          )}
          aria-hidden="true"
        >
          {label}
        </span>
      ) : null}
      {children}
    </div>
  );
}
