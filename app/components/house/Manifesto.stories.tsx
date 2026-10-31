import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Manifesto} from './Manifesto';

const meta = {title: 'House/Manifesto', component: Manifesto, parameters: {layout: 'fullscreen'}, args: {lines: copy.home.manifesto}} satisfies Meta<typeof Manifesto>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Home: three lines, one per screen on a phone. */
export const Home: Story = {args: {variant: 'home'}};
/** The manifesto page: the statement, then numbered paragraphs. */
export const Page: Story = {
  args: {variant: 'page', lines: [copy.manifesto.paragraphs[copy.manifesto.paragraphs.length - 1]], paragraphs: copy.manifesto.paragraphs.slice(0, -1)},
  globals: {theme: 'paper'},
  decorators: [(Story) => <div className="mx-auto max-w-4xl px-6 py-12"><Story /></div>],
};
/** Print: the same on paper, for a printed version. */
export const Print: Story = {
  args: {variant: 'print', lines: [copy.manifesto.paragraphs[copy.manifesto.paragraphs.length - 1]], paragraphs: copy.manifesto.paragraphs.slice(0, -1)},
  globals: {theme: 'paper'},
  decorators: [(Story) => <div className="mx-auto max-w-4xl px-6 py-12"><Story /></div>],
};
