import type {Meta, StoryObj} from '@storybook/react-vite';
import {Burst} from './Burst';
import {Card} from './Card';
import {Entry} from './Entry';
import {sequence} from '~/lib/entry-sequence';

/**
 * The opening, held at each of its steps (the clock is off in stories). The real sequence from
 * assets/entry/sequence.json: every still graded in the files, burst 1 under relative luminance 0.09.
 */
const meta = {
  title: 'House/Entry',
  component: Entry,
  parameters: {layout: 'fullscreen'},
  args: {onDone: () => undefined},
} satisfies Meta<typeof Entry>;
export default meta;
type Story = StoryObj<typeof meta>;

export const CardSeeEverything: Story = {name: 'Card · See everything.', args: {hold: {step: 0}}};
export const Burst1Framed: Story = {name: 'Burst 1 · framed, 12 a second', args: {hold: {step: 1, frame: 0}}};
export const Burst1Pair: Story = {name: 'Burst 1 · a swap pair', args: {hold: {step: 1, frame: 9}}};
export const CardRevealNothing: Story = {name: 'Card · Reveal nothing.', args: {hold: {step: 2}}};
export const LogoHold: Story = {name: 'The stacked logo, held', args: {hold: {step: 3}}};
export const Burst2Bright: Story = {name: 'Burst 2 · full bleed, a bright frame', args: {hold: {step: 4, frame: 0}}};
export const Burst2Dark: Story = {name: 'Burst 2 · full bleed, a dark frame', args: {hold: {step: 4, frame: 1}}};
export const EndCard: Story = {name: 'End card · the GCD in gold', args: {hold: {step: 5}}};
/** Skipped or finished: nothing renders; the cookie ds_entry=seen keeps it away for 30 days. */
export const SkippedOrFinished: Story = {
  name: 'Skipped / finished (nothing renders)',
  render: () => (
    <div className="grid min-h-dvh place-items-center">
      <Entry hold={{step: 99}} onDone={() => undefined} />
    </div>
  ),
};
/** prefers-reduced-motion: the cards only, no bursts. */
export const ReducedMotion: Story = {args: {reducedMotion: true, hold: {step: 1}}};
/** Wire mode: the sequence as a frame list. */
export const Wire: Story = {args: {wire: true}, parameters: {layout: 'padded'}};

const b1 = sequence.steps[1].frames![0];
const b2 = sequence.steps[4].frames![0];
export const BurstFramedStill: Story = {
  name: 'Burst (component) · framed',
  render: () => (
    <div className="h-dvh">
      <Burst still={sequence.stills[b1]} code={b1} layout="framed" />
    </div>
  ),
};
export const BurstBleedStill: Story = {
  name: 'Burst (component) · bleed',
  render: () => (
    <div className="h-dvh">
      <Burst still={sequence.stills[b2]} code={b2} layout="bleed" />
    </div>
  ),
};
export const BurstMissingStill: Story = {
  name: 'Burst (component) · missing still',
  render: () => (
    <div className="h-dvh">
      <Burst still={null} code="E1-01" layout="framed" />
    </div>
  ),
};
export const CardNight: Story = {
  name: 'Card (component) · night',
  render: () => (
    <div className="h-dvh">
      <Card text={sequence.steps[0].text ?? ''} ground="night" />
    </div>
  ),
};
export const CardBlack: Story = {
  name: 'Card (component) · black',
  render: () => (
    <div className="h-dvh">
      <Card text={sequence.steps[2].text ?? ''} ground="black" />
    </div>
  ),
};
