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
 * 1.00 to 1.06 as the visitor scrolls (03-references.md, ref 2). Static under reduced motion. The push
 * itself is wired in phase 3; the layout and the one line are here.
 */
export function DetailHold({shot, image, ratio = 'stage', line, renderSrc, className}: DetailHoldProps) {
  return (
    <section className={cx('grid gap-6 py-16 md:py-24', className)} data-detail-hold>
      <div className={cx('mx-auto w-full overflow-hidden', renderSrc || ratio === 'hero-landscape' ? 'max-w-[min(48rem,105dvh)]' : 'max-w-[min(48rem,56dvh)]')}>
        {renderSrc ? (
          <ShotSlot shot="GCD-3D-YAW35" ratio="hero-landscape" surface="canvas" image={null}>
            <img src={renderSrc} alt="" className="absolute inset-0 m-auto w-1/2" loading="lazy" decoding="async" data-detail-image />
          </ShotSlot>
        ) : (
          <ShotSlot shot={shot} ratio={ratio} image={image} sizes="(min-width: 768px) 768px, 100vw" imgClassName="origin-center scale-(--detail-scale,1)" />
        )}
      </div>
      {line ? <p className="mx-auto max-w-prose px-4 text-center font-text text-card font-regular leading-ui text-ds-text-secondary">{line}</p> : null}
    </section>
  );
}
