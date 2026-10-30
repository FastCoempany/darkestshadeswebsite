import {useEffect, useRef, useState} from 'react';
import {ShotSlot, type Ratio} from '~/components/base/ShotSlot';
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
  labels: {previous: string; next: string};
  className?: string;
}

/**
 * On a phone: a horizontal swipe with scroll snapping and a numeric counter (the one allowed motion
 * beyond the cuts). From 1024 px: a two-column stack beside the buy panel (04). Every image sits on the stage.
 */
export function Gallery({items, label, counter, labels, className}: GalleryProps) {
  const track = useRef<HTMLUListElement>(null);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const el = track.current;
    if (!el) return;
    const onScroll = () => {
      const width = el.clientWidth || 1;
      setIndex(Math.min(items.length - 1, Math.max(0, Math.round(el.scrollLeft / width))));
    };
    el.addEventListener('scroll', onScroll, {passive: true});
    return () => el.removeEventListener('scroll', onScroll);
  }, [items.length]);

  const go = (next: number) => {
    const el = track.current;
    if (!el) return;
    const i = Math.min(items.length - 1, Math.max(0, next));
    el.scrollTo({left: i * el.clientWidth, behavior: 'auto'});
    setIndex(i);
  };

  return (
    <section aria-label={label} className={cx('relative', className)} data-gallery>
      {/* A scrollable region must take focus and arrow keys (WCAG 2.1.1; axe scrollable-region-focusable). */}
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex, jsx-a11y/no-noninteractive-element-interactions */}
      <ul ref={track} tabIndex={0} aria-label={label} onKeyDown={(e) => { if (e.key === 'ArrowRight') go(index + 1); if (e.key === 'ArrowLeft') go(index - 1); }}
        className="flex snap-x snap-mandatory overflow-x-auto overscroll-x-contain scroll-smooth motion-reduce:scroll-auto lg:grid lg:grid-cols-2 lg:gap-px lg:snap-none lg:overflow-visible [&::-webkit-scrollbar]:hidden [scrollbar-width:none]"
      >
        {items.map((item) => (
          <li key={item.shot} className="w-full shrink-0 snap-start">
            <ShotSlot shot={item.shot} ratio={item.ratio} image={item.image} sizes="(min-width: 1024px) 50vw, 100vw" />
          </li>
        ))}
      </ul>
      {items.length > 1 ? (
        <div className="mt-2 flex items-center justify-center gap-4 lg:hidden">
          <button type="button" className="size-11 rounded-none font-text text-ui text-ds-text-secondary hover:text-ds-text-primary" onClick={() => go(index - 1)} aria-label={labels.previous} disabled={index === 0}>
            ←
          </button>
          <p className="ds-tabular font-text text-micro font-medium uppercase tracking-micro text-ds-text-tertiary" aria-live="polite">
            {counter(index + 1, items.length)}
          </p>
          <button type="button" className="size-11 rounded-none font-text text-ui text-ds-text-secondary hover:text-ds-text-primary" onClick={() => go(index + 1)} aria-label={labels.next} disabled={index >= items.length - 1}>
            →
          </button>
        </div>
      ) : null}
    </section>
  );
}
