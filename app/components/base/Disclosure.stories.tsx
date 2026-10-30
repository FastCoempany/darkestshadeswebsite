import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Disclosure} from './Disclosure';

const item = copy.questions.items[0];
const meta = {
  title: 'Base/Disclosure',
  component: Disclosure,
  parameters: {layout: 'padded'},
  decorators: [(Story) => <div className="max-w-md border-b border-ds-border-hairline"><Story /></div>],
} satisfies Meta<typeof Disclosure>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Collapsed: Story = {args: {summary: item.q, children: <p>{item.a}</p>}};
export const Expanded: Story = {args: {summary: item.q, children: <p>{item.a}</p>, open: true}};
