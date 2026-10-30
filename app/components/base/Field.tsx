import {forwardRef, useId, type InputHTMLAttributes} from 'react';
import {cx} from '~/lib/cx';

export interface FieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'id'> {
  label: string;
  kind?: 'email' | 'phone' | 'text';
  /** Shown under the field; with `invalid`, the error. */
  hint?: string | null;
  invalid?: boolean;
  valid?: boolean;
}

/** A 1 px control border, the label always visible above the input, never a placeholder as the label. */
export const Field = forwardRef<HTMLInputElement, FieldProps>(function Field(
  {label, kind = 'text', hint, invalid = false, valid = false, className, disabled, ...rest},
  ref,
) {
  const id = useId();
  const hintId = `${id}-hint`;
  const type = kind === 'email' ? 'email' : kind === 'phone' ? 'tel' : 'text';
  return (
    <div className={cx('grid gap-2', className)}>
      <label htmlFor={id} className="font-text text-small font-medium text-ds-text-secondary">
        {label}
      </label>
      <input
        ref={ref}
        id={id}
        type={type}
        inputMode={kind === 'phone' ? 'tel' : kind === 'email' ? 'email' : undefined}
        autoComplete={kind === 'phone' ? 'tel' : kind === 'email' ? 'email' : rest.autoComplete}
        aria-invalid={invalid || undefined}
        aria-describedby={hint ? hintId : undefined}
        disabled={disabled}
        data-valid={valid || undefined}
        className={cx(
          'h-12 w-full rounded-none border bg-ds-surface-base px-4 font-text text-body text-ds-text-primary',
          'placeholder:text-ds-text-tertiary disabled:text-ds-text-disabled disabled:border-ds-border-hairline',
          invalid ? 'border-ds-status-error' : valid ? 'border-ds-status-success' : 'border-ds-border-control',
        )}
        {...rest}
      />
      {hint ? (
        <p id={hintId} className={cx('font-text text-small', invalid ? 'text-ds-status-error' : 'text-ds-text-tertiary')}>
          {hint}
        </p>
      ) : null}
    </div>
  );
});
