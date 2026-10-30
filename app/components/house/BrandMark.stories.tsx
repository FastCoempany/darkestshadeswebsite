import type {Meta, StoryObj} from '@storybook/react-vite';
import {BrandMark} from './BrandMark';

const meta = {
  title: 'House/BrandMark',
  component: BrandMark,
  parameters: {layout: 'padded'},
} satisfies Meta<typeof BrandMark>;
export default meta;
type Story = StoryObj<typeof meta>;

/** The phone header's mark. */
export const Nav: Story = {args: {height: 24}};
/** The 404 and loading states. */
export const Large: Story = {args: {height: 64}};
