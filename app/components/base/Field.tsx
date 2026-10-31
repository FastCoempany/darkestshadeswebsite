import {forwardRef, useId, type InputHTMLAttributes} from 'react';
import {cx} from '~/lib/cx';

/** Dial codes for the phone field; the value the form sends is E.164 (`+14155550123`). Names come from Intl. */
export const DIAL_CODES = [
  {code: 'US', dial: '+1'},
  {code: 'CA', dial: '+1'},
  {code: 'GB', dial: '+44'},
  {code: 'IE', dial: '+353'},
  {code: 'FR', dial: '+33'},
  {code: 'DE', dial: '+49'},
  {code: 'IT', dial: '+39'},
  {code: 'ES', dial: '+34'},
  {code: 'NL', dial: '+31'},
  {code: 'SE', dial: '+46'},
  {code: 'DK', dial: '+45'},
  {code: 'CH', dial: '+41'},
  {code: 'AU', dial: '+61'},
  {code: 'NZ', dial: '+64'},
  {code: 'JP', dial: '+81'},
  {code: 'KR', dial: '+82'},
  {code: 'MX', dial: '+52'},
  {code: 'BR', dial: '+55'},
] as const;

const regionNames = typeof Intl !== 'undefined' && 'DisplayNames' in Intl ? new Intl.DisplayNames(['en'], {type: 'region'}) : null;

export function countryLabelFor(code: string, dial: string): string {
  return `${regionNames?.of(code) ?? code} ${dial}`;
}

export type DialCode = (typeof DIAL_CODES)[number]['code'];

/** `+1 (415) 555-0123` with country US -> `+14155550123`; null when there are no digits. */
export function toE164(national: string, country: DialCode): string | null {
  const digits = national.replace(/\D/g, '');
  if (!digits) return null;
  if (national.trim().startsWith('+')) return `+${digits}`;
  const dial = DIAL_CODES.find((c) => c.code === country)?.dial ?? '+1';
  // A national trunk prefix (0 in most of Europe, 1 in North America) comes off before the dial code.
  const local = dial === '+1' ? digits.replace(/^1(?=\d{10}$)/, '') : country === 'IT' ? digits : digits.replace(/^0/, '');
  return `${dial}${local}`;
}

export interface FieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'id'> {
  label: string;
  kind?: 'email' | 'phone' | 'text';
  /** Shown under the field; with `invalid`, the error. */
  hint?: string | null;
  invalid?: boolean;
  valid?: boolean;
  /** Phone only: the selected country and its change handler. */
  country?: DialCode;
  onCountryChange?: (code: DialCode) => void;
  countryLabel?: string;
  /** Stories: show the focused state. */
  forceFocus?: boolean;
}

/**
 * A 1 px control border, the label always visible above the input, never a placeholder as the label.
 * The phone kind pairs a country select with the number (E.164 goes to the server).
 */
export const Field = forwardRef<HTMLInputElement, FieldProps>(function Field(
  {label, kind = 'text', hint, invalid = false, valid = false, className, disabled, country = 'US', onCountryChange, countryLabel, forceFocus = false, ...rest},
  ref,
) {
  const id = useId();
  const hintId = `${id}-hint`;
  const type = kind === 'email' ? 'email' : kind === 'phone' ? 'tel' : 'text';
  const control = cx(
    'h-12 rounded-none border bg-ds-surface-base px-4 font-text text-body text-ds-text-primary',
    'placeholder:text-ds-text-tertiary disabled:text-ds-text-disabled disabled:border-ds-border-hairline',
    invalid ? 'border-ds-status-error' : valid ? 'border-ds-status-success' : 'border-ds-border-control',
  );
  return (
    <div className={cx('grid gap-2', className)} data-field={kind} data-state={disabled ? 'disabled' : invalid ? 'invalid' : valid ? 'valid' : rest.value || rest.defaultValue ? 'filled' : 'default'}>
      <label htmlFor={id} className="font-text text-small font-medium text-ds-text-secondary">
        {label}
      </label>
      {/* The select takes the width of its longest option, so no country name is ever cut; under 360 px the number goes beneath it. */}
      <div className={cx('grid gap-2', kind === 'phone' ? 'grid-cols-1 min-[360px]:grid-cols-[auto_1fr]' : 'grid-cols-1')}>
        {kind === 'phone' ? (
          <select
            aria-label={countryLabel ?? label}
            value={country}
            onChange={(e) => onCountryChange?.(e.target.value as DialCode)}
            disabled={disabled}
            className={control}
          >
            {DIAL_CODES.map((c) => (
              <option key={c.code} value={c.code}>
                {countryLabelFor(c.code, c.dial)}
              </option>
            ))}
          </select>
        ) : null}
        <input
          ref={ref}
          id={id}
          type={type}
          inputMode={kind === 'phone' ? 'tel' : kind === 'email' ? 'email' : undefined}
          autoComplete={kind === 'phone' ? 'tel-national' : kind === 'email' ? 'email' : rest.autoComplete}
          aria-invalid={invalid || undefined}
          aria-describedby={hint ? hintId : undefined}
          disabled={disabled}
          data-valid={valid || undefined}
          data-force={forceFocus ? 'focus-visible' : undefined}
          className={cx(control, 'w-full')}
          {...rest}
        />
      </div>
      {hint ? (
        <p id={hintId} className={cx('font-text text-small', invalid ? 'text-ds-status-error' : 'text-ds-text-tertiary')}>
          {hint}
        </p>
      ) : null}
    </div>
  );
});
