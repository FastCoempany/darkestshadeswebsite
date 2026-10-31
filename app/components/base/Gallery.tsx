import {useEffect, useRef, useState} from 'react';
import {ShotSlot, slotLabel, type Ratio, type ShotState} from '~/components/base/ShotSlot';
import {cx} from '~/lib/cx';
import type {StorefrontImage} from '~/lib/mock/types';

export interface GalleryItem {
  shot: string;
  ratio: Ratio;
  image: StorefrontImage | null;
}

export interface GalleryProps {
  items: GalleryItem[];
  label: string;
  /** "{index} / {total}" already filled by the caller for each index: pass a formatter. */
  counter: (index: number, total: number) => string;
  labels: {previous: string; next: string; zoomIn: string; zoomOut: string};
  /** Stories: hold every slot in a state, or start zoomed. */
  slotState?: ShotState;
  initialZoom?: number | null;
  className?: string;
}

/**
 * On a phone: a horizontal swipe with scroll snapping and a numeric counter (the one allowed motion
 * beyond the cuts). From 1024 px: a two-column stack beside the buy panel (04). Every image sits on the
 * stage. The zoom control in a picture's corner shows it at twice the size inside its frame, panned by
 * scrolling; pinch zoom is the browser's. States: loading, ready, zoomed, single image.
 */
export function Gallery({items, label, counter, labels, slotState, initialZoom = null, className}: GalleryProps) {
  const track = useRef<HTMLUListElement>(null);
  const [index, setIndex] = useState(0);
  const [zoomed, setZoomed] = useState<number | null>(initialZoom);
  const [swipes, setSwipes] = useState(true);

  useEffect(() => {
    const el = track.current;
    if (!el) return;
    const onScroll = () => {
      const width = el.clientWidth || 1;
      setIndex(Math.min(items.length - 1, Math.max(0, Math.round(el.scrollLeft / width))));
    };
    el.addEventListener('scroll', onScroll, {passive: true});
    const mq = window.matchMedia('(min-width: 1024px)');
    const onChange = () => setSwipes(!mq.matches);
    onChange();
    mq.addEventListener('change', onChange);
    return () => {
      el.removeEventListener('scroll', onScroll);
      mq.removeEventListener('change', onChange);
    };
  }, [items.length]);

  const go = (next: number) => {
    const el = track.current;
    if (!el || !swipes) return;
    const i = Math.min(items.length - 1, Math.max(0, next));
    el.scrollTo({left: i * el.clientWidth, behavior: 'auto'});
    setIndex(i);
  };

  const single = items.length <= 1;
  return (
    <section aria-label={label} className={cx('relative', className)} data-gallery data-gallery-state={zoomed !== null ? 'zoomed' : slotState === 'loading' ? 'loading' : single ? 'single' : 'ready'}>
      {/* The swipe track is a scrollable region: it takes focus and arrow keys on a phone (WCAG 2.1.1; axe scrollable-region-focusable). */}
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <ul ref={track} tabIndex={swipes && !single ? 0 : -1} aria-label={label} onKeyDown={(e) => { if (e.key === 'ArrowRight') go(index + 1); if (e.key === 'ArrowLeft') go(index - 1); }}
        className={cx(
          'flex snap-x snap-mandatory overflow-x-auto overscroll-x-contain scroll-smooth motion-reduce:scroll-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden',
          single ? 'lg:block' : 'lg:grid lg:grid-cols-2 lg:gap-px lg:snap-none lg:overflow-visible',
        )}
      >
        {items.map((item, i) => {
          const isZoomed = zoomed === i;
          // The control's name carries what the picture shows (WCAG 2.5.3: the visible slot label is part of it).
          const name = item.image ? item.image.altText : slotLabel(item.shot, item.ratio);
          return (
            <li key={item.shot} className="relative w-full shrink-0 snap-start">
              <ShotSlot shot={item.shot} ratio={item.ratio} image={item.image} state={slotState} priority={i === 0} sizes="(min-width: 1024px) 50vw, 100vw" zoom={isZoomed ? 2 : 1} zoomLabel={name} />
              {/* A labelled slot has nothing to zoom. */}
              {item.image ? <button
                type="button"
                className="absolute right-2 bottom-2 grid size-11 place-items-center rounded-none bg-ds-surface-canvas/80 font-text text-ui text-ds-text-primary hover:bg-ds-surface-canvas"
                data-zoomed={isZoomed}
                aria-label={`${isZoomed ? labels.zoomOut : labels.zoomIn}: ${name}`}
                aria-pressed={isZoomed}
                onClick={() => setZoomed(isZoomed ? null : i)}
              >
                {isZoomed ? '−' : '+'}
              </button> : null}
            </li>
          );
        })}
      </ul>
      {!single ? (
        <div className="mt-2 flex items-center justify-center gap-4 lg:hidden">
          <button type="button" className="size-11 rounded-none font-text text-ui text-ds-text-secondary hover:text-ds-text-primary disabled:text-ds-text-disabled" onClick={() => go(index - 1)} aria-label={labels.previous} disabled={index === 0}>
            ←
          </button>
          <p className="ds-tabular font-text text-micro font-medium uppercase tracking-micro text-ds-text-tertiary" aria-live="polite">
            {counter(index + 1, items.length)}
          </p>
          <button type="button" className="size-11 rounded-none font-text text-ui text-ds-text-secondary hover:text-ds-text-primary disabled:text-ds-text-disabled" onClick={() => go(index + 1)} aria-label={labels.next} disabled={index >= items.length - 1}>
            →
          </button>
        </div>
      ) : null}
    </section>
  );
}
