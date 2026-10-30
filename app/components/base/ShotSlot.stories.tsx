import type {Meta, StoryObj} from '@storybook/react-vite';
import {store} from '~/lib/mock';
import {ShotSlot} from './ShotSlot';

const meta = {
  title: 'Base/ShotSlot',
  component: ShotSlot,
  parameters: {layout: 'padded'},
  decorators: [(Story) => <div className="max-w-[480px]"><Story /></div>],
} satisfies Meta<typeof ShotSlot>;
export default meta;
type Story = StoryObj<typeof meta>;

/** A final from the manifest on the stage color. */
export const Loaded: Story = {args: {shot: 'F01-A1', ratio: 'stage', image: store.images.forShot('F01', 'A1'), sizes: '480px'}};
/** The landscape hero. */
export const Hero: Story = {args: {shot: 'F09-H', ratio: 'hero-landscape', image: store.images.forShot('F09', 'H'), sizes: '480px'}};
/** No final yet: the labelled slot. */
export const Empty: Story = {args: {shot: 'W3-S02-F09-A1', ratio: 'stage', image: null, surface: 'canvas'}};
/** A cast final on the canvas. */
export const Cast: Story = {args: {shot: 'W1-S07-F02-A1', ratio: 'stage', image: store.images.byId('ds-cast-w1-s07-f02'), surface: 'canvas', sizes: '480px'}};
