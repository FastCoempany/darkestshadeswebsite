import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Quantity} from './Quantity';

const labels = {fewer: copy.bag.quantityFewer, more: copy.bag.quantityMore};
const meta = {
  title: 'Base/Quantity',
  component: Quantity,
  parameters: {layout: 'padded'},
  args: {label: copy.bag.quantity, labels, onChange: () => undefined},
} satisfies Meta<typeof Quantity>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {args: {value: 1}};
/** The drop sets a per-customer limit of 2: the plus is inert. */
export const AtLimit: Story = {args: {value: 2, limit: 2}};
export const Disabled: Story = {args: {value: 1, disabled: true}};
export const Updating: Story = {args: {value: 2, updating: true}};
