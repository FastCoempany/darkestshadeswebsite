import {useEffect, useRef} from 'react';
import {Button} from '~/components/base/Button';
import {copy} from '~/lib/copy';

export interface SensoryNoticeProps {
  onContinue: () => void;
  onSkip: () => void;
  /** The choice was made before (the cookie): nothing shows. */
  remembered?: boolean;
}

/**
 * The photosensitivity notice before the entry: one line, Continue, Skip intro. Shown once; the choice
 * is remembered. A modal layer: focus starts on Skip intro, Tab moves between the two controls, Esc skips.
 */
export function SensoryNotice({onContinue, onSkip, remembered = false}: SensoryNoticeProps) {
  const skip = useRef<HTMLButtonElement>(null);
  const cont = useRef<HTMLButtonElement>(null);
  const skipRef = useRef(onSkip);
  skipRef.current = onSkip;

  useEffect(() => {
    if (remembered) return;
    skip.current?.focus();
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') skipRef.current();
      if (e.key === 'Tab') {
        e.preventDefault();
        (document.activeElement === skip.current ? cont.current : skip.current)?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener('keydown', onKey);
    };
  }, [remembered]);

  if (remembered) return null;
  return (
    <div className="fixed inset-0 z-(--z-entry) grid place-items-center bg-ds-surface-overlay px-4 text-ds-text-primary" role="dialog" aria-modal="true" aria-labelledby="sensory-notice" data-sensory-notice>
      <div className="grid max-w-md gap-8 text-center">
        <p id="sensory-notice" className="font-text text-card font-regular leading-ui">
          {copy.entry.notice.text}
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <Button ref={cont} variant="solid" size={48} onClick={onContinue}>
            {copy.entry.notice.continue}
          </Button>
          <Button ref={skip} variant="outline" size={48} onClick={onSkip}>
            {copy.entry.notice.skip}
          </Button>
        </div>
        <p className="font-text text-small text-ds-text-tertiary">{copy.entry.notice.note}</p>
      </div>
    </div>
  );
}
