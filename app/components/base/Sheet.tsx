import {useEffect, useId, useRef, useState, type ReactNode} from 'react';
import {cx} from '~/lib/cx';

export type SheetVariant = 'full' | 'side' | 'center';
export type SheetState = 'opening' | 'open' | 'closing';

const PANEL: Record<SheetVariant, string> = {
  full: 'inset-0',
  side: 'inset-y-0 right-0 w-full max-w-md',
  center: 'left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2',
};

/** The bag on desktop is the one sheet that moves: 120 ms in and out. Everything else is a hard cut. */
const MOTION: Record<SheetVariant, string> = {
  full: '',
  side: 'md:transition-transform md:duration-(--motion-quick) md:ease-ds motion-reduce:transition-none md:data-[state=opening]:translate-x-full md:data-[state=closing]:translate-x-full',
  center: '',
};

/** Only the side sheet on a desktop with motion allowed holds its closing state. */
const SLIDES = '(min-width: 768px) and (prefers-reduced-motion: no-preference)';

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
  /** Stories: hold the sheet in a transitional state. */
  forceState?: SheetState;
}

const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function focusables(root: HTMLElement): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((el) => el.offsetParent !== null || el === document.activeElement);
}

/**
 * A modal layer. Opens with a hard cut (the bag on desktop slides 120 ms, the one exception). Focus moves
 * inside on open, stays inside (Tab wraps) and returns to the opener on close; Esc and a click outside close it.
 */
export function Sheet({open, onClose, variant = 'center', title, hideTitle = false, closeLabel, children, className, forceState}: SheetProps) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  const opener = useRef<Element | null>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const [closing, setClosing] = useState(false);
  const [entered, setEntered] = useState(false);
  const wasOpen = useRef(open);

  // The side sheet slides in from `opening`; on close, on a desktop with motion, it holds `closing` for the transition.
  useEffect(() => {
    if (open) {
      setClosing(false);
      setEntered(false);
      const frame = requestAnimationFrame(() => setEntered(true));
      wasOpen.current = true;
      return () => cancelAnimationFrame(frame);
    }
    if (!wasOpen.current) return;
    wasOpen.current = false;
    if (variant !== 'side' || !window.matchMedia(SLIDES).matches) return;
    setClosing(true);
    const ms = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--motion-quick')) || 120;
    const t = window.setTimeout(() => setClosing(false), ms);
    return () => window.clearTimeout(t);
  }, [open, variant]);

  const visible = open || closing;

  // Focus moves in when the panel exists; Esc closes; Tab wraps; focus returns to the opener on close.
  useEffect(() => {
    if (!open || !visible) return;
    opener.current = document.activeElement;
    const root = panel.current;
    if (!root) return;
    const first = focusables(root)[0];
    (first ?? root).focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeRef.current();
      if (e.key === 'Tab') {
        const list = focusables(root);
        if (!list.length) return;
        const firstEl = list[0];
        const lastEl = list[list.length - 1];
        if (e.shiftKey && document.activeElement === firstEl) {
          e.preventDefault();
          lastEl.focus();
        } else if (!e.shiftKey && (document.activeElement === lastEl || !root.contains(document.activeElement))) {
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
  }, [open, visible]);

  if (!visible && !forceState) return null;
  const shown: SheetState = forceState ?? (closing ? 'closing' : entered ? 'open' : 'opening');
  return (
    <div className="fixed inset-0 z-(--z-sheet)" data-sheet={variant} data-state={shown}>
      <button type="button" className="absolute inset-0 h-full w-full cursor-default bg-ds-surface-canvas/80" aria-label={closeLabel} onClick={() => closeRef.current()} tabIndex={-1} aria-hidden="true" />
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${id}-title`}
        tabIndex={-1}
        data-state={shown}
        className={cx('absolute flex flex-col overflow-y-auto bg-ds-surface-canvas text-ds-text-primary outline-none', PANEL[variant], MOTION[variant], className)}
      >
        <div className="flex items-center justify-between gap-4 px-4 py-3 md:px-6">
          <h2 id={`${id}-title`} className={cx('ds-display text-label leading-ui tracking-label', hideTitle && 'sr-only')}>
            {title}
          </h2>
          <button type="button" onClick={() => closeRef.current()} className="ml-auto h-11 min-w-11 rounded-none px-2 font-text text-ui font-medium text-ds-action-quiet-text hover:text-ds-action-quiet-text-hover hover:underline underline-offset-3">
            {closeLabel}
          </button>
        </div>
        <div className="flex-1 px-4 pb-6 md:px-6">{children}</div>
      </div>
    </div>
  );
}
