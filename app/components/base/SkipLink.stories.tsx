import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {SkipLink} from './SkipLink';
import {VisuallyHidden} from './VisuallyHidden';

const meta = {title: 'Base/SkipLink', component: SkipLink, parameters: {layout: 'fullscreen'}, args: {children: copy.nav.skipToContent}} satisfies Meta<typeof SkipLink>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Hidden until it takes focus; first in the tab order on every page. */
export const Hidden: Story = {
  render: () => (
    <div className="p-6">
      <SkipLink>{copy.nav.skipToContent}</SkipLink>
      <p className="font-text text-body text-ds-text-secondary">
        {copy.accessibility.body[0]} <VisuallyHidden>{copy.entry.textEquivalent}</VisuallyHidden>
      </p>
    </div>
  ),
};
export const FocusVisible: Story = {
  render: () => (
    <div className="p-6">
      <SkipLink data-force="focus-visible">{copy.nav.skipToContent}</SkipLink>
      <p className="pt-16 font-text text-body text-ds-text-secondary">{copy.accessibility.body[0]}</p>
    </div>
  ),
};
