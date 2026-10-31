import {useEffect, useRef, useState} from 'react';
import {ShotSlot, type Ratio} from '~/components/base/ShotSlot';
import {cx} from '~/lib/cx';
import type {StorefrontImage} from '~/lib/mock/types';

export interface DetailHoldProps {
  shot: string;
  image: StorefrontImage | null;
  ratio?: Ratio;
  /** One line at most. */
  line?: string | null;
  /** The GCD's 3D render where a frame's pictures show no GCD (F08). */
  renderSrc?: string | null;
  className?: string;
}

/**
 * The long held view of the temple with the GCD, the only warm color on a dim screen, pushing in from
 * 1.00 to 1.06 as the visitor scrolls (03-references.md, ref 2): the section's progress through the
 * viewport drives `--detail-progress`; the scale is 1 + (push − 1) × progress, and the push token is 1
 * under reduced motion, so the picture then holds still. Nothing else moves; one line of copy at most.
 */
export function DetailHold({shot, image, ratio = 'stage', line, renderSrc, className}: DetailHoldProps) {
  const ref = useRef<HTMLElement>(null);
  const [state, setState] = useState<'idle' | 'in-view'>('idle');
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let frameRequest = 0;
    const update = () => {
      frameRequest = 0;
      const r = el.getBoundingClientRect();
      const h = window.innerHeight || 1;
      // 0 when the section's top enters at the bottom of the screen, 1 when its bottom leaves at the top.
      const progress = Math.min(1, Math.max(0, (h - r.top) / (h + r.height)));
      el.style.setProperty('--detail-progress', progress.toFixed(4));
      setState(r.top < h && r.bottom > 0 ? 'in-view' : 'idle');
    };
    const onScroll = () => {
      if (!frameRequest) frameRequest = requestAnimationFrame(update);
    };
    update();
    window.addEventListener('scroll', onScroll, {passive: true});
    window.addEventListener('resize', onScroll);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (frameRequest) cancelAnimationFrame(frameRequest);
    };
  }, []);
  return (
    <section ref={ref} className={cx('grid gap-6 py-16 md:py-24', className)} data-detail-hold={state}>
      <div className={cx('mx-auto w-full overflow-hidden', renderSrc || ratio === 'hero-landscape' ? 'max-w-[min(48rem,105dvh)]' : 'max-w-[min(48rem,56dvh)]')}>
        {renderSrc ? (
          <ShotSlot shot="GCD-3D-YAW35" ratio="hero-landscape" surface="bare" image={null} state="loaded">
            <img src={renderSrc} alt="" className="absolute inset-0 m-auto w-[70%] origin-center [transform:scale(calc(1+(var(--motion-push)-1)*var(--detail-progress,0)))]" loading="lazy" decoding="async" data-detail-image />
          </ShotSlot>
        ) : (
          <ShotSlot shot={shot} ratio={ratio} image={image} sizes="(min-width: 768px) 768px, 100vw" imgClassName="origin-center [transform:scale(calc(1+(var(--motion-push)-1)*var(--detail-progress,0)))] will-change-transform" />
        )}
      </div>
      {line ? <p className="mx-auto max-w-prose px-4 text-center font-text text-card font-regular leading-ui text-ds-text-secondary">{line}</p> : null}
    </section>
  );
}
