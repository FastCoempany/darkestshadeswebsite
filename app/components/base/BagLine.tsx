import {Price} from '~/components/base/Price';
import {Quantity} from '~/components/base/Quantity';
import {ShotSlot} from '~/components/base/ShotSlot';
import type {CartLine} from '~/lib/cart';
import {cx} from '~/lib/cx';

export interface BagLineProps {
  line: CartLine;
  variant?: 'drawer' | 'page';
  state?: 'default' | 'updating' | 'removing' | 'error';
  limit?: number | null;
  labels: {quantity: string; quantityFewer: string; quantityMore: string; remove: string};
  onQuantity: (lineId: string, quantity: number) => void;
  onRemove: (lineId: string) => void;
  error?: string | null;
}

/** A line in the bag: stage thumbnail, look number, descriptor, price, quantity, remove. */
export function BagLine({line, variant = 'drawer', state = 'default', limit = null, labels, onQuantity, onRemove, error}: BagLineProps) {
  const {product} = line.merchandise;
  return (
    <li className={cx('grid grid-cols-[5rem_1fr] gap-4 border-t border-ds-border-hairline py-4', variant === 'page' && 'md:grid-cols-[7rem_1fr]')} data-state={state} aria-busy={state === 'updating' || state === 'removing' || undefined}>
      <ShotSlot shot={line.merchandise.image?.ds.shot ?? `${line.merchandise.sku.split('-')[1] ?? ''}-A1`} ratio="stage" image={line.merchandise.image} sizes="112px" className={cx(state === 'removing' && 'opacity-50')} />
      <div className="grid content-start gap-2">
        <p className="font-text text-micro font-medium uppercase tracking-micro text-ds-text-editorial">{product.lookNumber}</p>
        <p className="font-text text-body text-ds-text-primary">{product.title}</p>
        <p className="font-text text-small text-ds-text-secondary">{product.descriptor}</p>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="flex items-baseline gap-2">
            <Price money={line.merchandise.price} />
            {line.quantity > 1 ? <Price money={line.cost.totalAmount} variant="compact" className="text-ds-text-secondary" /> : null}
          </span>
          <Quantity value={line.quantity} onChange={(q) => onQuantity(line.id, q)} limit={limit} label={labels.quantity} labels={{fewer: labels.quantityFewer, more: labels.quantityMore}} updating={state === 'updating' || state === 'removing'} />
        </div>
        <button type="button" onClick={() => onRemove(line.id)} disabled={state === 'removing'} className="inline-flex min-h-11 items-center justify-self-start rounded-none font-text text-small text-ds-action-quiet-text underline underline-offset-3 hover:text-ds-action-quiet-text-hover disabled:text-ds-text-disabled">
          {labels.remove}
        </button>
        {state === 'error' && error ? <p className="font-text text-small text-ds-status-error">{error}</p> : null}
      </div>
    </li>
  );
}
