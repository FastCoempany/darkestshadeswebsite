import type {Meta, StoryObj} from '@storybook/react-vite';
import {drops} from '~/components/pages/stories/fixtures';
import {store} from '~/lib/mock';
import {StageCard} from './StageCard';

const f01 = store.products.byId('F01')!;
const f02 = store.products.byId('F02')!;
const meta = {
  title: 'House/StageCard',
  component: StageCard,
  parameters: {layout: 'padded'},
  args: {product: f01, drop: drops.announcedNoDate},
  decorators: [(Story) => <div className="max-w-xs"><Story /></div>],
} satisfies Meta<typeof StageCard>;
export default meta;
type Story = StoryObj<typeof meta>;

/** A frame on the stage, like a print on a dark wall. */
export const Default: Story = {};
/** Hover or focus: the three-quarter angle (the temple, with the GCD). */
export const Hover: Story = {render: (args) => <div data-force="hover" className="group"><StageCard {...args} /></div>};
export const Live: Story = {name: 'Live, pairs left', args: {drop: drops.live}};
export const SoldOut: Story = {args: {product: f02, drop: drops.live}};
export const Loading: Story = {render: (args) => <StageCard {...args} product={{...f01, images: {nodes: []}, featuredImage: null}} />};
