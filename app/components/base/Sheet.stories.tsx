import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Sheet} from './Sheet';

const meta = {
  title: 'Base/Sheet',
  component: Sheet,
  parameters: {layout: 'fullscreen'},
  args: {open: true, onClose: () => undefined, title: copy.bag.title, closeLabel: copy.nav.close, children: <p className="py-6 font-text text-body text-ds-text-secondary">{copy.bag.empty}</p>},
  decorators: [
    (Story) => (
      <div className="min-h-dvh bg-ds-surface-canvas p-6 text-ds-text-primary">
        <p className="font-text text-body text-ds-text-secondary">{copy.frames.statement}</p>
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof Sheet>;
export default meta;
type Story = StoryObj<typeof meta>;

/** The phone menu: a full-screen night surface, hard cut. */
export const Full: Story = {args: {variant: 'full', title: copy.nav.menu, hideTitle: true}};
/** The bag: a side sheet; on desktop it slides 120 ms. */
export const SideOpen: Story = {args: {variant: 'side'}};
export const SideOpening: Story = {args: {variant: 'side', forceState: 'opening'}};
export const SideClosing: Story = {args: {variant: 'side', forceState: 'closing'}};
/** Notices and the list pop-up. */
export const Center: Story = {args: {variant: 'center', title: copy.list.title}};
