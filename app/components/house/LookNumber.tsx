import {cx} from '~/lib/cx';

/** The runway-style index, `01` to `09`, in camel micro type (docs/brief/01-brand-system.md, patina). */
export function LookNumber({number, className}: {number: string; className?: string}) {
  return <span className={cx('ds-tabular font-text text-micro font-medium uppercase tracking-micro text-ds-text-editorial', className)}>{number}</span>;
}
