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
 * Stillness, then one cut: once the small composition is whole on screen and the scroll has settled, the
 * visitor's next scroll, swipe, key or tap inside it cuts to full bleed, never a timer (03-references.md,
 * ref 3). Reduced motion and wire mode show the bleed only.
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
    // Stories and screenshot runs are still: the cut only happens on a visitor's move.
    if ((window as Window & {__dsStatic?: boolean}).__dsStatic) return;
    const el = ref.current;
    if (!el) return;
    let visible = false;
    let armed = false;
    let quiet: number | undefined;
    const arm = () => {
      window.clearTimeout(quiet);
      quiet = window.setTimeout(() => {
        armed = visible;
      }, 300);
    };
    const observer = new IntersectionObserver(
      ([entry]) => {
        visible = entry.intersectionRatio >= 0.9;
        armed = false;
        if (visible) arm();
      },
      {threshold: [0, 0.9, 1]},
    );
    observer.observe(el);
    const onMove = () => {
      if (armed) setState('bleed');
      else if (visible) arm();
    };
    const onKey = (e: KeyboardEvent) => {
      if (armed && ['ArrowDown', 'PageDown', ' ', 'Enter'].includes(e.key)) setState('bleed');
    };
    window.addEventListener('scroll', onMove, {passive: true});
    window.addEventListener('wheel', onMove, {passive: true});
    window.addEventListener('touchmove', onMove, {passive: true});
    window.addEventListener('keydown', onKey);
    return () => {
      observer.disconnect();
      window.clearTimeout(quiet);
      window.removeEventListener('scroll', onMove);
      window.removeEventListener('wheel', onMove);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('keydown', onKey);
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
