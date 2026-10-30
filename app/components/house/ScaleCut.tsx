import {useEffect, useRef, useState, type ReactNode} from 'react';
import {cx} from '~/lib/cx';

export interface ScaleCutProps {
  /** The small, frontal, centered composition. */
  small: ReactNode;
  /** The same subject at full bleed. */
  bleed: ReactNode;
  /** Start in the bleed state (reduced motion, wire mode, stories). */
  initial?: 'small' | 'bleed';
  className?: string;
}

/**
 * Stillness, then one cut: a small composition cuts to full bleed on the visitor's first scroll or tap
 * inside it, never on a timer (03-references.md, ref 3). Reduced motion shows the bleed only.
 */
export function ScaleCut({small, bleed, initial = 'small', className}: ScaleCutProps) {
  const [state, setState] = useState<'small' | 'bleed'>(initial);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (state === 'bleed') return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || document.documentElement.dataset.mode === 'wire') {
      setState('bleed');
      return;
    }
    const el = ref.current;
    if (!el) return;
    let armed = false;
    const observer = new IntersectionObserver(([entry]) => {
      armed = entry.intersectionRatio > 0.6;
    }, {threshold: [0, 0.6, 1]});
    observer.observe(el);
    const onScroll = () => {
      if (armed) setState('bleed');
    };
    window.addEventListener('scroll', onScroll, {passive: true});
    window.addEventListener('wheel', onScroll, {passive: true});
    window.addEventListener('touchmove', onScroll, {passive: true});
    return () => {
      observer.disconnect();
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('wheel', onScroll);
      window.removeEventListener('touchmove', onScroll);
    };
  }, [state]);

  return (
    <section ref={ref} className={cx('relative', className)} data-scale-cut={state}>
      {state === 'small' ? (
        <div
          role="button"
          tabIndex={0}
          onClick={() => setState('bleed')}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') setState('bleed');
          }}
          className="grid min-h-dvh w-full cursor-default place-items-center rounded-none px-4 text-left"
        >
          {small}
        </div>
      ) : (
        bleed
      )}
    </section>
  );
}
