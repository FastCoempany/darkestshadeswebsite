import type {ReactNode} from 'react';
import {cx} from '~/lib/cx';

export type NoticeTone = 'info' | 'success' | 'error';

const TONE: Record<NoticeTone, string> = {
  info: 'border-ds-status-info text-ds-text-primary',
  success: 'border-ds-status-success text-ds-text-primary',
  error: 'border-ds-status-error text-ds-text-primary',
};

/** Inline or toast, polite, with the tone said in words, never only by a color (docs/brief/05-components.md). */
export function Notice({tone = 'info', variant = 'inline', children, className}: {tone?: NoticeTone; variant?: 'inline' | 'toast'; children: ReactNode; className?: string}) {
  return (
    <p
      role="status"
      aria-live="polite"
      className={cx(
        'border-l-2 px-4 py-3 font-text text-small',
        TONE[tone],
        variant === 'toast' && 'fixed bottom-4 left-4 right-4 z-(--z-toast) bg-ds-surface-overlay md:left-auto md:w-96',
        className,
      )}
    >
      {children}
    </p>
  );
}
