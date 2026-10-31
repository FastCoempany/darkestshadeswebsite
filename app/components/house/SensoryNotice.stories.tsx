import type {Meta, StoryObj} from '@storybook/react-vite';
import {SensoryNotice} from './SensoryNotice';

const meta = {
  title: 'House/SensoryNotice',
  component: SensoryNotice,
  parameters: {layout: 'fullscreen'},
  args: {onContinue: () => undefined, onSkip: () => undefined},
} satisfies Meta<typeof SensoryNotice>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Shown once before the opening; Continue · Skip intro; Esc skips. */
export const Shown: Story = {};
/** Remembered: the choice set the cookie; nothing renders. */
export const Remembered: Story = {args: {remembered: true}};
