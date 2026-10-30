import type {Meta, StoryObj} from '@storybook/react-vite';
import {lineFor} from '~/lib/cart';
import {copy} from '~/lib/copy';
import {store} from '~/lib/mock';
import {BagLine} from './BagLine';

const f01 = store.products.byId('F01')!;
const line = lineFor(f01, f01.variants.nodes[0], 2);
const labels = {quantity: copy.bag.quantity, quantityFewer: copy.bag.quantityFewer, quantityMore: copy.bag.quantityMore, remove: copy.bag.remove};

const meta = {
  title: 'Base/BagLine',
  component: BagLine,
  parameters: {layout: 'padded'},
  args: {line, labels, onQuantity: () => undefined, onRemove: () => undefined, limit: 2},
  decorators: [(Story) => <ul className="max-w-md list-none"><Story /></ul>],
} satisfies Meta<typeof BagLine>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Drawer: Story = {args: {variant: 'drawer'}};
export const Page: Story = {args: {variant: 'page'}};
export const Updating: Story = {args: {state: 'updating'}};
export const Removing: Story = {args: {state: 'removing'}};
export const Error: Story = {args: {state: 'error', error: copy.list.error}};
