import {BagLine} from '~/components/base/BagLine';
import {BagSummary} from '~/components/base/BagSummary';
import {Sheet} from '~/components/base/Sheet';
import {TextLink} from '~/components/base/TextLink';
import {useCart} from '~/lib/cart';
import {copy, fill} from '~/lib/copy';

/** The bag as a side sheet on every page. Lines, $100, the exchange and warranty lines, Checkout disabled. */
export function BagDrawer({limit = null}: {limit?: number | null}) {
  const {cart, isOpen, close, setQuantity, remove} = useCart();
  return (
    <Sheet open={isOpen} onClose={close} variant="side" title={copy.bag.title} closeLabel={copy.nav.close}>
      <BagContents cart={cart} limit={limit} onQuantity={setQuantity} onRemove={remove} />
    </Sheet>
  );
}

export function BagContents({
  cart,
  limit,
  onQuantity,
  onRemove,
  variant = 'drawer',
}: {
  cart: ReturnType<typeof useCart>['cart'];
  limit: number | null;
  onQuantity: (id: string, q: number) => void;
  onRemove: (id: string) => void;
  variant?: 'drawer' | 'page';
}) {
  if (cart.lines.nodes.length === 0) {
    return (
      <div className="grid justify-items-start gap-4 py-8">
        <p className="font-text text-body text-ds-text-secondary">{copy.bag.empty}</p>
        <TextLink to="/frames" variant="nav">
          {copy.nav.frames}
        </TextLink>
      </div>
    );
  }
  return (
    <div className="grid gap-6">
      <ul className="grid">
        {cart.lines.nodes.map((line) => (
          <BagLine
            key={line.id}
            line={line}
            variant={variant}
            limit={limit}
            labels={{quantity: copy.bag.quantity, quantityFewer: copy.bag.quantityFewer, quantityMore: copy.bag.quantityMore, remove: copy.bag.remove}}
            onQuantity={onQuantity}
            onRemove={onRemove}
          />
        ))}
      </ul>
      {limit ? <p className="font-text text-small text-ds-text-tertiary">{fill(copy.bag.limit, {n: limit})}</p> : null}
      <BagSummary cart={cart} labels={{subtotal: copy.bag.subtotal, checkout: copy.bag.checkout, checkoutDisabled: copy.bag.checkoutDisabled}} promises={copy.product.promises} />
    </div>
  );
}
