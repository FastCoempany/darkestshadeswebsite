import {useEffect, useRef, useState} from 'react';
import {ShotSlot} from '~/components/base/ShotSlot';
import {Burst} from '~/components/house/Burst';
import {Card} from '~/components/house/Card';
import {Logo} from '~/components/house/Logo';
import {Seal} from '~/components/house/Seal';
import {copy, fill} from '~/lib/copy';
import {cx} from '~/lib/cx';
import {sequence as realSequence, stepSeconds, stillSources, type EntrySequence, type EntryStep} from '~/lib/entry-sequence';

export type {EntrySequence, EntryStep} from '~/lib/entry-sequence';

export interface EntryProps {
  sequence?: EntrySequence;
  /** Cards only, no bursts (prefers-reduced-motion). */
  reducedMotion?: boolean;
  /** Wire mode: the sequence as a static frame list. */
  wire?: boolean;
  /** Stories: hold one step (and frame) instead of running the clock. */
  hold?: {step: number; frame?: number};
  onDone: (how: 'finished' | 'skipped') => void;
}

/** The framed print's rendered width, for `sizes` and the preload. */
export const FRAMED_SIZES = '(min-width: 768px) 720px, 60vw';

const GROUND: Record<string, string> = {
  'surface-overlay': 'bg-ds-surface-overlay',
  'surface-canvas': 'bg-ds-surface-canvas',
  black: 'bg-ds-surface-entry',
};

/**
 * The opening (03-references.md): cards, bursts, the stacked logo, the GCD end card, from graded still
 * images on a frame clock, sound off. Burst 1 runs at 12 a second only because every still is graded
 * under relative luminance 0.09 in the files; burst 2 runs at 3 a second with one bright frame a second.
 * Skip works from the first frame: button, Esc, any scroll or swipe. The pictures are aria-hidden with a
 * text equivalent; the skip control comes first in the tab order.
 */
export function Entry({sequence = realSequence, reducedMotion = false, wire = false, hold, onDone}: EntryProps) {
  const steps = reducedMotion ? sequence.steps.filter((s) => s.type !== 'burst') : sequence.steps;
  const [index, setIndex] = useState(hold?.step ?? 0);
  const [frame, setFrame] = useState(hold?.frame ?? 0);
  const done = useRef(false);
  const skipButton = useRef<HTMLButtonElement>(null);
  const running = !wire && !hold;

  const finish = (how: 'finished' | 'skipped') => {
    if (done.current) return;
    done.current = true;
    onDone(how);
  };

  // Preload every still during the first card, with the same srcset and sizes the bursts render, so the
  // browser fetches the very candidates it will show (2x screens included).
  useEffect(() => {
    if (!running || reducedMotion) return;
    const loaders = Object.values(sequence.stills).map((still) => {
      const src = stillSources(still);
      const img = new Image();
      img.sizes = still.ratio === '3:4' ? FRAMED_SIZES : '100vw';
      img.srcset = src.avif;
      img.src = src.fallback;
      return img;
    });
    return () => loaders.forEach((img) => (img.src = ''));
  }, [sequence, running, reducedMotion]);

  // A modal layer while it plays: the page behind does not scroll, and Tab stays on the one control.
  useEffect(() => {
    if (wire) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const trap = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        skipButton.current?.focus();
      }
    };
    document.addEventListener('keydown', trap);
    return () => {
      document.body.style.overflow = previous;
      document.removeEventListener('keydown', trap);
    };
  }, [wire]);

  // The frame clock.
  useEffect(() => {
    if (!running) return;
    const step = steps[index];
    if (!step) {
      finish('finished');
      return;
    }
    if (step.type === 'burst') {
      const count = step.frames?.length ?? 0;
      if (!count) {
        setIndex((i) => i + 1);
        return;
      }
      let f = 0;
      const id = window.setInterval(() => {
        f += 1;
        if (f >= count) {
          window.clearInterval(id);
          setFrame(0);
          setIndex((i) => i + 1);
        } else {
          setFrame(f);
        }
      }, 1000 / (step.fps ?? 12));
      return () => window.clearInterval(id);
    }
    const id = window.setTimeout(() => setIndex((i) => i + 1), stepSeconds(step) * 1000);
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, running]);

  // Skip: the button has focus from the first frame; Esc, wheel and swipe skip too.
  useEffect(() => {
    if (wire) return;
    skipButton.current?.focus();
    if (!running) return;
    const skip = () => finish('skipped');
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') skip();
    };
    window.addEventListener('keydown', onKey);
    window.addEventListener('wheel', skip, {passive: true});
    window.addEventListener('touchmove', skip, {passive: true});
    return () => {
      window.removeEventListener('keydown', onKey);
      window.removeEventListener('wheel', skip);
      window.removeEventListener('touchmove', skip);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wire, running]);

  if (wire) return <EntryFrameList sequence={sequence} />;

  const step = steps[index];
  if (!step) return null;
  const stillId = step.type === 'burst' ? step.frames?.[frame] : undefined;
  const still = stillId ? sequence.stills[stillId] ?? null : null;
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={copy.entry.textEquivalent}
      className={cx('fixed inset-0 z-(--z-entry) text-ds-text-primary', GROUND[step.ground ?? 'surface-overlay'] ?? 'bg-ds-surface-overlay')}
      data-entry={step.type}
      data-entry-step={index}
      data-entry-frame={frame}
    >
      <button
        ref={skipButton}
        type="button"
        onClick={() => finish('skipped')}
        className="absolute top-3 right-4 z-10 h-11 rounded-none px-3 font-text text-ui font-medium text-ds-text-primary hover:underline underline-offset-3"
      >
        {copy.entry.skip}
      </button>
      <p className="sr-only">{copy.entry.textEquivalent}</p>
      <div className="h-full w-full" aria-hidden="true">
        {step.type === 'card' ? (
          <Card text={cardText(step)} ground={step.ground === 'black' ? 'black' : 'night'} />
        ) : step.type === 'logo' ? (
          <div className="grid h-full place-items-center px-6">
            <Logo variant="stacked" className="!h-auto w-[min(70vw,28rem)]" />
          </div>
        ) : step.type === 'end' ? (
          <div className="grid h-full place-items-center">
            <div className="grid justify-items-center gap-6">
              <Seal width={120} decorative priority />
              <p className="font-text text-card font-regular text-ds-text-primary">{copy.meta.brand}</p>
            </div>
          </div>
        ) : (
          <Burst still={still} code={stillId ?? `E${index}-${String(frame + 1).padStart(2, '0')}`} layout={step.layout ?? 'framed'} />
        )}
      </div>
    </div>
  );
}

/** A card's words come from en.json by index; the sequence file keeps a copy for the flash check only. */
function cardText(step: EntryStep): string {
  return (step.card !== undefined ? copy.entry.cards[step.card] : undefined) ?? step.text ?? '';
}

/** Wire mode: the sequence as a list, every still a labelled slot. */
function EntryFrameList({sequence}: {sequence: EntrySequence}) {
  const listed = sequence.steps.map((step, i) => ({...step, id: `${step.type}-${i}`}));
  return (
    <section className="grid gap-4 border-y border-ds-border-hairline px-4 py-8" aria-label={copy.entry.textEquivalent} data-entry="wire">
      <ol className="grid gap-3">
        {listed.map((step) => (
          <li key={step.id} className="grid grid-cols-[3rem_1fr] items-start gap-4 font-text text-small text-ds-text-secondary">
            <span className="ds-tabular text-ds-text-tertiary">{stepSeconds(step).toFixed(1)}s</span>
            {step.type === 'burst' ? (
              <div className="grid gap-2">
                <span>{fill(copy.entry.burstLine, {count: step.frames?.length ?? 0, fps: step.fps ?? 12, layout: copy.entry.layouts[step.layout ?? 'framed']})}</span>
                <div className={cx('grid gap-2', step.layout === 'framed' ? 'grid-cols-4 md:grid-cols-9' : 'grid-cols-4 md:grid-cols-8')}>
                  {Array.from(new Set(step.frames ?? [])).map((id) => {
                    const still = sequence.stills[id];
                    return <ShotSlot key={id} shot={still?.shot ?? id} ratio={step.layout === 'framed' ? 'print' : 'stage'} surface="canvas" variant="sequence" count={(step.frames ?? []).filter((f) => f === id).length} />;
                  })}
                </div>
              </div>
            ) : step.type === 'card' ? (
              <span className="font-text text-card text-ds-text-primary">{cardText(step)}</span>
            ) : step.type === 'logo' ? (
              <Logo variant="stacked" height={48} />
            ) : (
              <span className="flex items-center gap-3">
                <Seal width={40} decorative /> {copy.meta.brand}
              </span>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
