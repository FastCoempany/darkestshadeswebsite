import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy, fill} from '~/lib/copy';
import {store} from '~/lib/mock';
import {Gallery} from './Gallery';

const f01 = store.products.byId('F01')!;
const items = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6'].map((a) => ({shot: `F01-${a}`, ratio: 'stage' as const, image: f01.images.nodes.find((i) => i.ds.angle === a) ?? null}));
const labels = {previous: copy.product.galleryPrevious, next: copy.product.galleryNext, zoomIn: copy.product.galleryZoomIn, zoomOut: copy.product.galleryZoomOut};
const counter = (i: number, t: number) => fill(copy.product.galleryCounter, {index: i, total: t}) ?? `${i} / ${t}`;

const meta = {
  title: 'Base/Gallery',
  component: Gallery,
  parameters: {layout: 'fullscreen'},
  args: {items, label: fill(copy.product.galleryLabel, {name: f01.title}) ?? f01.title, counter, labels},
} satisfies Meta<typeof Gallery>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Swipe with a counter on a phone; a two-column stack from 1024 px. */
export const Ready: Story = {};
export const Loading: Story = {args: {slotState: 'loading'}};
export const Zoomed: Story = {args: {initialZoom: 0}};
export const SingleImage: Story = {args: {items: items.slice(0, 1)}};
