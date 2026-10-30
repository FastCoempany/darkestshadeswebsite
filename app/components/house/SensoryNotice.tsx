import {useEffect, useRef} from 'react';
import {Button} from '~/components/base/Button';
import {copy} from '~/lib/copy';

/** The photosensitivity notice before the entry: one line, Continue, Skip intro. Shown once; the choice is remembered. */
export function SensoryNotice({onContinue, onSkip}: {onContinue: () => void; onSkip: () => void}) {
  const skip = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    skip.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onSkip();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onSkip]);
  return (
    <div className="fixed inset-0 z-(--z-entry) grid place-items-center bg-ds-surface-overlay px-4 text-ds-text-primary" role="dialog" aria-modal="true" aria-labelledby="sensory-notice" data-sensory-notice>
      <div className="grid max-w-md gap-8 text-center">
        <p id="sensory-notice" className="font-text text-card font-regular leading-ui">
          {copy.entry.notice.text}
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <Button variant="solid" size={48} onClick={onContinue}>
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
