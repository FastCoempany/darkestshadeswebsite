import type {Meta, StoryObj} from '@storybook/react-vite';
import {Seal} from './Seal';

const meta = {
  title: 'House/Seal',
  component: Seal,
  parameters: {layout: 'padded'},
} satisfies Meta<typeof Seal>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Under 48 px: flat gold, no veins. */
export const Small: Story = {args: {width: 32}};
/** 48 to 160 px: the onyx vector with the metallic gradient and veins. */
export const Medium: Story = {args: {width: 96}};
/** Above 160 px: the 3D render. */
export const Large: Story = {args: {width: 320}};
/** On paper: gold with a black stone. */
export const Paper: Story = {args: {width: 96, surface: 'paper'}, globals: {theme: 'paper'}};
