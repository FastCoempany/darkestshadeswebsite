import {useEffect, useId, useRef, type ReactNode} from 'react';
import {cx} from '~/lib/cx';

export type SheetVariant = 'full' | 'side' | 'center';

const PANEL: Record<SheetVariant, string> = {
  full: 'inset-0',
  side: 'inset-y-0 right-0 w-full max-w-md md:transition-transform md:duration-(--motion-quick) motion-reduce:transition-none',
  center: 'left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2',
};

export interface SheetProps {
  open: boolean;
  onClose: () => void;
  variant?: SheetVariant;
  /** The accessible name; shown as a heading unless `hideTitle`. */
  title: string;
  hideTitle?: boolean;
  closeLabel: string;
  children: ReactNode;
  className?: string;
}

/**
 * A modal layer that opens with a hard cut (the bag on desktop slides 120 ms, the one exception).
 * Focus moves inside on open and returns on close; Esc and a click outside close it.
 */
export function Sheet({open, onClose, variant = 'center', title, hideTitle = false, closeLabel, children, className}: SheetProps) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  const opener = useRef<Element | null>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    if (!open) return;
    const onClose = () => closeRef.current();
    opener.current = document.activeElement;
    const first = panel.current?.querySelector<HTMLElement>('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    (first ?? panel.current)?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'Tab' && panel.current) {
        const focusables = Array.from(panel.current.querySelectorAll<HTMLElement>('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')).filter((el) => !el.hasAttribute('disabled'));
        if (!focusables.length) return;
        const firstEl = focusables[0];
        const lastEl = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === firstEl) {
          e.preventDefault();
          lastEl.focus();
        } else if (!e.shiftKey && document.activeElement === lastEl) {
          e.preventDefault();
          firstEl.focus();
        }
      }
    };
    document.addEventListener('keydown', onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = previousOverflow;
      (opener.current as HTMLElement | null)?.focus?.();
    };
  }, [open]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-(--z-sheet)" data-sheet={variant}>
      <button type="button" className="absolute inset-0 h-full w-full cursor-default bg-ds-surface-canvas/80" aria-label={closeLabel} onClick={onClose} tabIndex={-1} />
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${id}-title`}
        tabIndex={-1}
        className={cx('absolute flex flex-col overflow-y-auto bg-ds-surface-canvas text-ds-text-primary outline-none', PANEL[variant], className)}
      >
        <div className="flex items-center justify-between gap-4 px-4 py-3 md:px-6">
          <h2 id={`${id}-title`} className={cx('ds-display text-label leading-ui tracking-label', hideTitle && 'sr-only')}>
            {title}
          </h2>
          <button type="button" onClick={onClose} className="ml-auto h-11 min-w-11 rounded-none px-2 font-text text-ui font-medium text-ds-action-quiet-text hover:text-ds-action-quiet-text-hover hover:underline underline-offset-3">
            {closeLabel}
          </button>
        </div>
        <div className="flex-1 px-4 pb-6 md:px-6">{children}</div>
      </div>
    </div>
  );
}
