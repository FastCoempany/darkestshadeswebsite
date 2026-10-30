import {BagContents} from '~/components/house/BagDrawer';
import {useCart} from '~/lib/cart';
import {copy} from '~/lib/copy';

/** The bag as a page (/cart): the same lines and summary as the drawer. */
export function BagPage({limit = null}: {limit?: number | null}) {
  const {cart, setQuantity, remove} = useCart();
  return (
    <main id="main" className="mx-auto grid w-full max-w-3xl gap-8 px-4 py-12 md:px-6" data-page="bag">
      <h1 className="ds-display text-h1 leading-heading tracking-heading">{copy.bag.title}</h1>
      <BagContents cart={cart} limit={limit} onQuantity={setQuantity} onRemove={remove} variant="page" />
    </main>
  );
}
