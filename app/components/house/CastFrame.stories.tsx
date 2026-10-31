import type {Meta, StoryObj} from '@storybook/react-vite';
import {store} from '~/lib/mock';
import {CastFrame} from './CastFrame';
import {FilmGrain} from './FilmGrain';
import {ShotSlot} from '~/components/base/ShotSlot';

const w1 = store.cast.member('W1')!;
const w3 = store.cast.member('W3')!;
const meta = {
  title: 'House/CastFrame',
  component: CastFrame,
  parameters: {layout: 'padded'},
  args: {shot: w1.portrait!, product: store.products.byId('F02')},
  decorators: [(Story) => <div className="max-w-md"><Story /></div>],
} satisfies Meta<typeof CastFrame>;
export default meta;
type Story = StoryObj<typeof meta>;

/** A final, with the film grain over the photograph. */
export const Default: Story = {};
/** Full bleed, one per screen on a phone (/cast). */
export const Bleed: Story = {args: {variant: 'bleed'}, parameters: {layout: 'fullscreen'}, decorators: [(Story) => <Story />]};
/** A draft shot: the labelled slot. */
export const Slot: Story = {name: 'Draft shot · labelled slot', args: {shot: w3.portrait!, product: store.products.byId('F09')}};
export const GrainOn: Story = {name: 'FilmGrain · on', render: () => <ShotSlot shot="W1-S07-F02-A1" ratio="stage" image={w1.portrait!.image} surface="canvas" sizes="448px"><FilmGrain /></ShotSlot>};
export const GrainOff: Story = {name: 'FilmGrain · off (reduced transparency, cut-outs)', render: () => <ShotSlot shot="W1-S07-F02-A1" ratio="stage" image={w1.portrait!.image} surface="canvas" sizes="448px"><FilmGrain on={false} /></ShotSlot>};
