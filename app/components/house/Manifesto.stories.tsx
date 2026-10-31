import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Manifesto} from './Manifesto';

const meta = {title: 'House/Manifesto', component: Manifesto, parameters: {layout: 'fullscreen'}, args: {lines: copy.home.manifesto}} satisfies Meta<typeof Manifesto>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Home: three lines, one per screen on a phone. */
export const Home: Story = {args: {variant: 'home'}};
/** Home with the first line as the page's h1. */
export const HomeHeading: Story = {name: 'Home · first line as the h1', args: {variant: 'home', heading: true}};
/** The manifesto page: the statement, then numbered paragraphs. */
export const Page: Story = {
  args: {variant: 'page', lines: [copy.manifesto.paragraphs[copy.manifesto.paragraphs.length - 1]], paragraphs: copy.manifesto.paragraphs.slice(0, -1)},
  globals: {theme: 'paper'},
  // The page's own gutters, so the statement's cap matches the page at every width.
  decorators: [(Story) => <div className="px-4 py-12 md:px-6 lg:px-10 xl:px-14"><Story /></div>],
};
/** Print: the same on paper, for a printed version. */
export const Print: Story = {
  args: {variant: 'print', lines: [copy.manifesto.paragraphs[copy.manifesto.paragraphs.length - 1]], paragraphs: copy.manifesto.paragraphs.slice(0, -1)},
  globals: {theme: 'paper'},
  decorators: [(Story) => <div className="mx-auto max-w-4xl px-6 py-12"><Story /></div>],
};
