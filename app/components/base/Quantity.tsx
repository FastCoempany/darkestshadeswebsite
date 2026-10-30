import {cx} from '~/lib/cx';

export interface QuantityProps {
  value: number;
  onChange: (next: number) => void;
  /** A per-customer limit the drop sets; null means none. */
  limit?: number | null;
  disabled?: boolean;
  updating?: boolean;
  label: string;
  labels: {fewer: string; more: string};
  className?: string;
}

/** A stepper that honors the drop's limit. At the limit the plus is inert; at one the minus removes nothing: the line's Remove does. */
export function Quantity({value, onChange, limit = null, disabled = false, updating = false, label, labels, className}: QuantityProps) {
  const atLimit = limit !== null && value >= limit;
  const btn = 'size-11 rounded-none border border-ds-border-control font-text text-ui text-ds-text-primary hover:bg-ds-surface-raised disabled:text-ds-text-disabled disabled:border-ds-border-hairline';
  return (
    <div className={cx('inline-flex items-center', className)} role="group" aria-label={label} aria-busy={updating || undefined} data-at-limit={atLimit || undefined}>
      <button type="button" className={btn} onClick={() => onChange(value - 1)} disabled={disabled || updating || value <= 1} aria-label={labels.fewer}>
        −
      </button>
      <output className="ds-tabular inline-grid h-11 min-w-11 place-items-center border-y border-ds-border-control font-text text-ui" aria-live="polite">
        {value}
      </output>
      <button type="button" className={btn} onClick={() => onChange(value + 1)} disabled={disabled || updating || atLimit} aria-label={labels.more}>
        +
      </button>
    </div>
  );
}
