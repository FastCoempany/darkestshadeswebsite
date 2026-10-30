import type {Meta, StoryObj} from '@storybook/react-vite';
import {Logo} from './Logo';

const meta = {
  title: 'House/Logo',
  component: Logo,
  parameters: {layout: 'padded'},
} satisfies Meta<typeof Logo>;
export default meta;
type Story = StoryObj<typeof meta>;

/** The desktop header and the footer sign-off. */
export const Horizontal: Story = {args: {variant: 'horizontal', height: 24}};
/** Square-ish spaces: the entry's end card. */
export const Stacked: Story = {args: {variant: 'stacked', height: 96}};
/** Edge to edge across the footer's foot. */
export const FooterEdge: Story = {
  args: {variant: 'horizontal', height: 24},
  render: () => (
    <div className="w-full">
      <Logo variant="horizontal" className="!h-auto w-full" />
    </div>
  ),
};
