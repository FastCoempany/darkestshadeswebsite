import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Field} from './Field';

const meta = {
  title: 'Base/Field',
  component: Field,
  parameters: {layout: 'padded'},
  args: {label: copy.list.emailLabel, kind: 'email'},
  decorators: [(Story) => <div className="grid max-w-md gap-6"><Story /></div>],
} satisfies Meta<typeof Field>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <>
      <Field label={copy.list.emailLabel} kind="email" />
      <Field label={copy.list.phoneLabel} kind="phone" countryLabel={copy.list.countryLabel} />
      <Field label={copy.list.emailLabel} kind="text" />
    </>
  ),
};
export const Focus: Story = {
  render: () => (
    <>
      <Field label={copy.list.emailLabel} kind="email" forceFocus />
      <Field label={copy.list.phoneLabel} kind="phone" forceFocus countryLabel={copy.list.countryLabel} />
    </>
  ),
};
export const Filled: Story = {
  render: () => (
    <>
      <Field label={copy.list.emailLabel} kind="email" value="name@example.com" readOnly />
      <Field label={copy.list.phoneLabel} kind="phone" value="415 555 0123" readOnly countryLabel={copy.list.countryLabel} />
    </>
  ),
};
export const Invalid: Story = {
  render: () => (
    <>
      <Field label={copy.list.emailLabel} kind="email" value="name@" readOnly invalid hint={copy.list.invalidEmail} />
      <Field label={copy.list.phoneLabel} kind="phone" value="12" readOnly invalid hint={copy.list.invalidPhone} countryLabel={copy.list.countryLabel} />
    </>
  ),
};
export const Valid: Story = {
  render: () => (
    <>
      <Field label={copy.list.emailLabel} kind="email" value="name@example.com" readOnly valid />
      <Field label={copy.list.phoneLabel} kind="phone" value="415 555 0123" readOnly valid countryLabel={copy.list.countryLabel} />
    </>
  ),
};
export const Disabled: Story = {
  render: () => (
    <>
      <Field label={copy.list.emailLabel} kind="email" disabled />
      <Field label={copy.list.phoneLabel} kind="phone" disabled countryLabel={copy.list.countryLabel} />
    </>
  ),
};
