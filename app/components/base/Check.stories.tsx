import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Check} from './Check';

const meta = {
  title: 'Base/Check',
  component: Check,
  parameters: {layout: 'padded'},
  args: {label: copy.accessibility.introToggle.label},
  decorators: [(Story) => <div className="grid max-w-md gap-6"><Story /></div>],
} satisfies Meta<typeof Check>;
export default meta;
type Story = StoryObj<typeof meta>;

/** The consent variant holds the whole consent text; never pre-checked. */
export const Unchecked: Story = {
  render: () => (
    <>
      <Check variant="consent" label={copy.list.smsConsent} readOnly />
      <Check variant="plain" label={copy.accessibility.introToggle.label} readOnly />
    </>
  ),
};
export const Checked: Story = {
  render: () => (
    <>
      <Check variant="consent" label={copy.list.smsConsent} checked readOnly />
      <Check variant="plain" label={copy.accessibility.introToggle.label} checked readOnly />
    </>
  ),
};
export const FocusVisible: Story = {render: () => <Check variant="plain" label={copy.accessibility.introToggle.label} readOnly data-force="focus-visible" />};
export const Invalid: Story = {render: () => <Check variant="consent" label={copy.list.smsConsent} readOnly invalid error={copy.list.consentRequired} />};
