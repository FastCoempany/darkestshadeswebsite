import type {Meta, StoryObj} from '@storybook/react-vite';
import {Price} from './Price';

const meta = {title: 'Base/Price', component: Price, parameters: {layout: 'padded'}} satisfies Meta<typeof Price>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Always $100, tabular figures, never struck through: there are no sales. */
export const Default: Story = {args: {money: {amount: '100.00', currencyCode: 'USD'}}};
export const Compact: Story = {args: {money: {amount: '100.00', currencyCode: 'USD'}, variant: 'compact'}};
export const LineTotal: Story = {name: 'Line total (two pairs)', args: {money: {amount: '200.00', currencyCode: 'USD'}}};
