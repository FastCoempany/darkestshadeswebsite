import type {Meta, StoryObj} from '@storybook/react-vite';
import {ListForm} from './ListForm';
import {ListOffer} from './ListOffer';

const never = () => new Promise<'success' | 'already'>(() => undefined);
const meta = {
  title: 'House/ListForm',
  component: ListForm,
  parameters: {layout: 'padded'},
  decorators: [(Story) => <div className="max-w-md"><Story /></div>],
} satisfies Meta<typeof ListForm>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Email first; the mobile number optional with the consent box, never pre-checked. */
export const Idle: Story = {};
export const Submitting: Story = {args: {initialState: 'submitting', submit: never}};
export const Success: Story = {args: {initialState: 'success'}};
export const Error: Story = {args: {initialState: 'error'}};
export const AlreadyOnList: Story = {args: {initialState: 'already'}};
export const OfferOpen: Story = {
  name: 'ListOffer · open',
  parameters: {layout: 'fullscreen'},
  decorators: [(Story) => <div className="min-h-dvh"><Story /></div>],
  render: () => <ListOffer open onClose={() => undefined} />,
};
export const OfferEarlyAccess: Story = {
  name: 'ListOffer · open, early access gated',
  parameters: {layout: 'fullscreen'},
  decorators: [(Story) => <div className="min-h-dvh"><Story /></div>],
  render: () => <ListOffer open onClose={() => undefined} earlyAccess={{enabled: true, hours: 24}} />,
};
export const OfferSignedUp: Story = {
  name: 'ListOffer · open, signed up',
  parameters: {layout: 'fullscreen'},
  decorators: [(Story) => <div className="min-h-dvh"><Story /></div>],
  render: () => <ListOffer open onClose={() => undefined} formState="success" />,
};
export const OfferHidden: Story = {
  name: 'ListOffer · hidden, dismissed, signed up (nothing renders)',
  render: () => <ListOffer open={false} onClose={() => undefined} />,
};
