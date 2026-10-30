import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Notice} from './Notice';

const meta = {
  title: 'Base/Notice',
  component: Notice,
  parameters: {layout: 'padded'},
  args: {children: copy.list.success},
  decorators: [(Story) => <div className="grid max-w-md gap-4"><Story /></div>],
} satisfies Meta<typeof Notice>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Inline: Story = {
  render: () => (
    <>
      <Notice tone="info">{copy.list.bodyNoEarlyAccess}</Notice>
      <Notice tone="success">{copy.list.success}</Notice>
      <Notice tone="error">{copy.list.error}</Notice>
    </>
  ),
};
export const Toast: Story = {
  parameters: {layout: 'fullscreen'},
  render: () => (
    <div className="grid min-h-dvh content-start gap-3 p-6">
      <Notice tone="info" variant="toast" className="static md:w-auto">
        {copy.list.bodyNoEarlyAccess}
      </Notice>
      <Notice tone="success" variant="toast" className="static md:w-auto">
        {copy.list.success}
      </Notice>
      <Notice tone="error" variant="toast" className="static md:w-auto">
        {copy.list.error}
      </Notice>
    </div>
  ),
};
