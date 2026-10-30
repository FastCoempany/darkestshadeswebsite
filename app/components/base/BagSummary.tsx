import {useId} from 'react';
import {Button} from '~/components/base/Button';
import {Price} from '~/components/base/Price';
import type {Cart} from '~/lib/cart';

export interface BagSummaryProps {
  cart: Cart;
  labels: {subtotal: string; checkout: string; checkoutDisabled: string};
  /** The exchange and warranty lines. */
  promises: string[];
  /** Launch: a live checkout URL. This phase: null, and the button stays disabled. */
  checkoutUrl?: string | null;
}

/** Subtotal, the two promises, and Checkout, which reads "Checkout opens at launch" in this phase. */
export function BagSummary({cart, labels, promises, checkoutUrl = null}: BagSummaryProps) {
  const noteId = useId();
  const enabled = Boolean(checkoutUrl);
  return (
    <div className="grid gap-4 border-t border-ds-border-rule pt-4" data-checkout={enabled ? 'enabled' : 'disabled'}>
      <div className="flex items-baseline justify-between font-text text-body">
        <span className="text-ds-text-secondary">{labels.subtotal}</span>
        <Price money={cart.cost.subtotalAmount} />
      </div>
      <ul className="grid gap-1 font-text text-small text-ds-text-secondary">
        {promises.map((p) => (
          <li key={p}>{p}</li>
        ))}
      </ul>
      {enabled ? (
        <Button variant="solid" size={56} full to={checkoutUrl ?? undefined}>
          {labels.checkout}
        </Button>
      ) : (
        <>
          <Button variant="solid" size={56} full disabled aria-describedby={noteId}>
            {labels.checkout}
          </Button>
          <p id={noteId} className="text-center font-text text-small text-ds-text-tertiary">
            {labels.checkoutDisabled}
          </p>
        </>
      )}
    </div>
  );
}
