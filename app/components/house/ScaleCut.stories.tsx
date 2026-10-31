import type {Meta, StoryObj} from '@storybook/react-vite';
import {ShotSlot} from '~/components/base/ShotSlot';
import {store} from '~/lib/mock';
import {drops} from '~/components/pages/stories/fixtures';
import {DropStatus} from './DropStatus';
import {ScaleCut} from './ScaleCut';
import {StageCard} from './StageCard';

const products = store.products.all();
const small = (
  <div className="grid w-full max-w-sm justify-items-center gap-8">
    <ShotSlot shot="F09-H" ratio="hero-landscape" image={store.images.forShot('F09', 'H')} sizes="384px" className="w-full" />
    <DropStatus drop={drops.announcedNoDate} variant="small" />
  </div>
);
const bleed = (
  <ul className="grid grid-cols-1 gap-x-4 gap-y-10 px-4 py-16 md:grid-cols-2 lg:grid-cols-4">
    {products.map((p) => (
      <li key={p.id}>
        <StageCard product={p} drop={drops.announcedNoDate} />
      </li>
    ))}
  </ul>
);

const meta = {title: 'House/ScaleCut', component: ScaleCut, parameters: {layout: 'fullscreen'}, args: {small, bleed}} satisfies Meta<typeof ScaleCut>;
export default meta;
type Story = StoryObj<typeof meta>;

/** The small, frontal, centered composition: stillness. */
export const Small: Story = {args: {initial: 'small'}};
/** After the visitor's first scroll or tap: the same subject at full bleed. */
export const Bleed: Story = {args: {initial: 'bleed'}};
/** Reduced motion: the bleed only. */
export const ReducedMotion: Story = {args: {initial: 'bleed'}};
