import {ShotSlot, slotLabel} from '~/components/base/ShotSlot';
import {cx} from '~/lib/cx';
import type {EntryStill} from '~/lib/entry-sequence';
import {stillSources} from '~/lib/entry-sequence';
import {FRAMED_SIZES} from '~/components/house/Entry';

export interface BurstProps {
  /** The still on screen now. */
  still: EntryStill | null;
  /** The still's code, for the slot label when the file is missing. */
  code: string;
  /** `framed`: a small 3:4 print with dark margins. `bleed`: full screen. */
  layout: 'framed' | 'bleed';
  className?: string;
}

/**
 * One frame of a burst (03, reference 1): a graded black-and-white still, either a small print on the
 * dark wall or full bleed. Rate and order come from the sequence file; the luminance cap is in the files.
 */
export function Burst({still, code, layout, className}: BurstProps) {
  const src = still ? stillSources(still) : null;
  return (
    <div className={cx('grid h-full w-full place-items-center', layout === 'framed' ? 'bg-ds-surface-canvas' : 'bg-ds-surface-entry', className)} data-burst={layout}>
      {src ? (
        <picture
          className={cx('relative block', layout === 'framed' ? 'aspect-print w-[min(60vw,34dvh)]' : 'h-full w-full')}
          data-shot={slotLabel(still!.shot, layout === 'framed' ? 'print' : 'stage')}
        >
          <source type="image/avif" srcSet={src.avif} sizes={layout === 'framed' ? FRAMED_SIZES : '100vw'} />
          <source type="image/webp" srcSet={src.webp} sizes={layout === 'framed' ? FRAMED_SIZES : '100vw'} />
          <img src={src.fallback} alt="" width={still!.sizes[0].width} height={still!.sizes[0].height} className="h-full w-full object-cover" decoding="sync" />
        </picture>
      ) : (
        <div className={cx(layout === 'framed' ? 'w-[min(60vw,34dvh)]' : 'h-full w-full')}>
          <ShotSlot shot={code} ratio={layout === 'framed' ? 'print' : 'mobile-hero'} surface="canvas" className={layout === 'bleed' ? 'h-full !aspect-auto' : undefined} />
        </div>
      )}
    </div>
  );
}
