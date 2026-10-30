import {useEffect, useRef, useState} from 'react';
import {Logo} from '~/components/house/Logo';
import {Seal} from '~/components/house/Seal';
import {ShotSlot} from '~/components/base/ShotSlot';
import {copy, fill} from '~/lib/copy';
import {cx} from '~/lib/cx';

/** The sequence file both the player and tools/flashcheck.py read (assets/entry/sequence.json). */
export interface EntryStep {
  type: 'card' | 'burst' | 'logo' | 'end';
  text?: string;
  seconds?: number;
  layout?: 'framed' | 'bleed';
  fps?: number;
  frames?: string[];
  ground?: string;
}

export interface EntrySequence {
  version: 1;
  steps: EntryStep[];
}

/** The sequence as 03-references.md lays it out, before the stills exist: bursts with no frames render labelled slots. */
export const defaultSequence: EntrySequence = {
  version: 1,
  steps: [
    {type: 'card', text: copy.entry.cards[0], seconds: 1.2, ground: 'surface-overlay'},
    {type: 'burst', layout: 'framed', fps: 12, frames: [], ground: 'surface-canvas'},
    {type: 'card', text: copy.entry.cards[1], seconds: 2.0, ground: 'surface-overlay'},
    {type: 'logo', seconds: 2.4, ground: 'surface-overlay'},
    {type: 'burst', layout: 'bleed', fps: 3, frames: [], ground: 'black'},
    {type: 'end', seconds: 1.6, ground: 'black'},
  ],
};

const BURST_FRAMES = {framed: 28, bleed: 7};

function stepSeconds(step: EntryStep): number {
  if (step.type === 'burst') return (step.frames?.length || BURST_FRAMES[step.layout ?? 'framed']) / (step.fps ?? 12);
  return step.seconds ?? 1;
}

const GROUND: Record<string, string> = {
  'surface-overlay': 'bg-ds-surface-overlay',
  'surface-canvas': 'bg-ds-surface-canvas',
  black: 'bg-ds-surface-canvas',
};

export interface EntryProps {
  sequence?: EntrySequence;
  /** Cards only, no bursts (prefers-reduced-motion). */
  reducedMotion?: boolean;
  /** Wire mode: the sequence as a static frame list. */
  wire?: boolean;
  onDone: (how: 'finished' | 'skipped') => void;
}

/**
 * The opening (03-references.md): cards, bursts, the stacked logo, the GCD end card, from still images on
 * a frame clock, sound off. Skip works from the first frame: button, Esc, any scroll or swipe. The
 * visual sequence is aria-hidden with a text equivalent; the skip control comes first in the tab order.
 */
export function Entry({sequence = defaultSequence, reducedMotion = false, wire = false, onDone}: EntryProps) {
  const steps = reducedMotion ? sequence.steps.filter((s) => s.type !== 'burst') : sequence.steps;
  const listed = sequence.steps.map((step, i) => ({...step, id: `${step.type}-${i}`}));
  const [index, setIndex] = useState(0);
  const [frame, setFrame] = useState(0);
  const done = useRef(false);
  const skipButton = useRef<HTMLButtonElement>(null);

  const finish = (how: 'finished' | 'skipped') => {
    if (done.current) return;
    done.current = true;
    onDone(how);
  };

  useEffect(() => {
    if (wire) return;
    const step = steps[index];
    if (!step) {
      finish('finished');
      return;
    }
    if (step.type === 'burst') {
      const count = step.frames?.length || BURST_FRAMES[step.layout ?? 'framed'];
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
  }, [index, wire]);

  useEffect(() => {
    if (wire) return;
    skipButton.current?.focus();
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
  }, [wire]);

  if (wire) {
    return (
      <section className="grid gap-4 border-y border-ds-border-hairline px-4 py-8" aria-label={copy.entry.textEquivalent} data-entry="wire">
        <ol className="grid gap-3">
          {listed.map((step, i) => (
            <li key={step.id} className="grid grid-cols-[3rem_1fr] items-start gap-4 font-text text-small text-ds-text-secondary">
              <span className="ds-tabular text-ds-text-tertiary">{stepSeconds(step).toFixed(1)}s</span>
              {step.type === 'burst' ? (
                <div className="grid gap-2">
                  <span>
                    {fill(copy.entry.burstLine, {count: step.frames?.length || BURST_FRAMES[step.layout ?? 'framed'], fps: step.fps ?? 12, layout: copy.entry.layouts[step.layout ?? 'framed']})}
                  </span>
                  <div className={cx('grid gap-2', step.layout === 'framed' ? 'grid-cols-4 md:grid-cols-7' : 'grid-cols-2 md:grid-cols-4')}>
                    {Array.from({length: Math.min(step.frames?.length || BURST_FRAMES[step.layout ?? 'framed'], 7)}, (_, f) => `E${i}-${String(f + 1).padStart(2, '0')}`).map((code) => (
                      <ShotSlot key={code} shot={code} ratio={step.layout === 'framed' ? 'print' : 'desktop-hero'} surface="canvas" />
                    ))}
                  </div>
                </div>
              ) : step.type === 'card' ? (
                <span className="font-text text-card text-ds-text-primary">{step.text}</span>
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

  const step = steps[index];
  if (!step) return null;
  return (
    <div className={cx('fixed inset-0 z-(--z-entry) text-ds-text-primary', GROUND[step.ground ?? 'surface-overlay'] ?? 'bg-ds-surface-overlay')} data-entry={step.type} data-entry-step={index}>
      <button
        ref={skipButton}
        type="button"
        onClick={() => finish('skipped')}
        className="absolute top-3 right-4 z-10 h-11 rounded-none px-3 font-text text-ui font-medium text-ds-text-primary hover:underline underline-offset-3"
      >
        {copy.entry.skip}
      </button>
      <p className="sr-only">{copy.entry.textEquivalent}</p>
      <div className="grid h-full place-items-center" aria-hidden="true">
        {step.type === 'card' ? (
          <p className="font-text text-card font-regular leading-ui">{step.text}</p>
        ) : step.type === 'logo' ? (
          <Logo variant="stacked" height={96} />
        ) : step.type === 'end' ? (
          <div className="grid justify-items-center gap-6">
            <Seal width={120} decorative />
            <p className="font-text text-card font-regular">{copy.meta.brand}</p>
          </div>
        ) : step.layout === 'framed' ? (
          <div className="w-[min(60vw,45vh)]">
            <ShotSlot shot={`E${index}-${String(frame + 1).padStart(2, '0')}`} ratio="print" surface="canvas" image={null} />
          </div>
        ) : (
          <div className="h-full w-full">
            <ShotSlot shot={`E${index}-${String(frame + 1).padStart(2, '0')}`} ratio="mobile-hero" surface="canvas" image={null} className="h-full !aspect-auto" />
          </div>
        )}
      </div>
    </div>
  );
}
