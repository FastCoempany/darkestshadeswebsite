import {forwardRef, useId, type InputHTMLAttributes, type ReactNode} from 'react';
import {cx} from '~/lib/cx';

export interface CheckProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'id'> {
  /** The full label; the consent variant holds the whole consent text (docs/brief/08-copy.md). */
  label: ReactNode;
  variant?: 'consent' | 'plain';
  invalid?: boolean;
  error?: string | null;
}

/** A square checkbox with its label; never pre-checked (the caller never passes `defaultChecked` for consent). */
export const Check = forwardRef<HTMLInputElement, CheckProps>(function Check({label, variant = 'plain', invalid = false, error, className, ...rest}, ref) {
  const id = useId();
  const errorId = `${id}-error`;
  return (
    <div className={cx('grid gap-2', className)}>
      <label htmlFor={id} className="grid grid-cols-[1.25rem_1fr] items-start gap-3">
        <input
          ref={ref}
          id={id}
          type="checkbox"
          aria-invalid={invalid || undefined}
          aria-describedby={error ? errorId : undefined}
          className={cx(
            'mt-0.5 size-5 appearance-none rounded-none border bg-ds-surface-base',
            'checked:bg-ds-action-primary-bg checked:border-ds-action-primary-bg',
            invalid ? 'border-ds-status-error' : 'border-ds-border-control',
          )}
          {...rest}
        />
        <span className={cx('font-text', variant === 'consent' ? 'text-small text-ds-text-secondary' : 'text-body text-ds-text-primary')}>{label}</span>
      </label>
      {error ? (
        <p id={errorId} className="font-text text-small text-ds-status-error">
          {error}
        </p>
      ) : null}
    </div>
  );
});
