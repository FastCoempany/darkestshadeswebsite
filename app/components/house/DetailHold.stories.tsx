import type {Meta, StoryObj} from '@storybook/react-vite';
import gcdRender from '../../../brand/emblems/gcd/render/gcd-3d-yaw35-1024.png?url';
import {copy} from '~/lib/copy';
import {store} from '~/lib/mock';
import {DetailHold} from './DetailHold';

const meta = {
  title: 'House/DetailHold',
  component: DetailHold,
  parameters: {layout: 'fullscreen'},
  args: {shot: 'F09-A6', image: store.images.forShot('F09', 'A6'), line: copy.home.detail},
} satisfies Meta<typeof DetailHold>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Idle: the hold before it enters the viewport (push at 1.00). */
export const Idle: Story = {};
/** In view: pushed in as the visitor scrolls (1.00 to 1.06), the only movement on the page. */
export const InView: Story = {
  render: (args) => (
    <div>
      <div className="h-[60dvh]" />
      <DetailHold {...args} />
      <div className="h-[60dvh]" />
    </div>
  ),
};
/** Reduced motion: the push token is 1, the picture holds still. */
export const ReducedMotion: Story = {
  render: (args) => (
    <div style={{['--motion-push' as string]: '1'}}>
      <DetailHold {...args} />
    </div>
  ),
};
/** F08 shows no GCD in its pictures: its hold uses the emblem's render. */
export const F08Render: Story = {name: 'F08 · the GCD render', args: {shot: 'F08-A6', image: null, renderSrc: gcdRender, line: copy.product.gcdLine}};
