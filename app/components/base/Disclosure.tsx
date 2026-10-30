import type {ReactNode} from 'react';
import {cx} from '~/lib/cx';

/** A native details/summary pair: the Questions page and the specs on a phone. */
export function Disclosure({summary, children, open = false, className, id}: {summary: ReactNode; children: ReactNode; open?: boolean; className?: string; id?: string}) {
  return (
    <details id={id} open={open} className={cx('group border-t border-ds-border-hairline', className)}>
      <summary className="flex cursor-pointer list-none items-start justify-between gap-6 py-4 font-text text-body font-medium text-ds-text-primary marker:content-none [&::-webkit-details-marker]:hidden">
        <span>{summary}</span>
        <span aria-hidden="true" className="ds-tabular shrink-0 font-text text-body text-ds-text-tertiary group-open:hidden">
          +
        </span>
        <span aria-hidden="true" className="ds-tabular hidden shrink-0 font-text text-body text-ds-text-tertiary group-open:inline">
          −
        </span>
      </summary>
      <div className="ds-measure pb-6 font-text text-body text-ds-text-secondary">{children}</div>
    </details>
  );
}
