import type {Meta, StoryObj} from '@storybook/react-vite';
import {emptyCart, lineFor, type Cart} from '~/lib/cart';
import {copy} from '~/lib/copy';
import {store} from '~/lib/mock';
import {BagSummary} from './BagSummary';

const f01 = store.products.byId('F01')!;
const f09 = store.products.byId('F09')!;
const cart: Cart = {...emptyCart, totalQuantity: 3, lines: {nodes: [lineFor(f01, f01.variants.nodes[0], 1), lineFor(f09, f09.variants.nodes[0], 2)]}, cost: {subtotalAmount: {amount: '300.00', currencyCode: 'USD'}, totalAmount: {amount: '300.00', currencyCode: 'USD'}}};
const labels = {subtotal: copy.bag.subtotal, checkout: copy.bag.checkout, checkoutDisabled: copy.bag.checkoutDisabled};

const meta = {
  title: 'Base/BagSummary',
  component: BagSummary,
  parameters: {layout: 'padded'},
  args: {cart, labels, promises: copy.product.promises},
  decorators: [(Story) => <div className="max-w-md"><Story /></div>],
} satisfies Meta<typeof BagSummary>;
export default meta;
type Story = StoryObj<typeof meta>;

/** This phase: "Checkout opens at launch". */
export const CheckoutDisabled: Story = {};
/** Launch: a live checkout. */
export const Default: Story = {name: 'Default (checkout enabled at launch)', args: {checkoutUrl: '/cart'}};
