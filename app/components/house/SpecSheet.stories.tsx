import type {Meta, StoryObj} from '@storybook/react-vite';
import {store} from '~/lib/mock';
import {LineDrawing} from './LineDrawing';
import {storyDrawings} from '~/components/pages/stories/fixtures';
import {SpecSheet} from './SpecSheet';

const f01 = store.products.byId('F01')!;
const f06 = store.products.byId('F06')!;
const meta = {
  title: 'House/SpecSheet',
  component: SpecSheet,
  parameters: {layout: 'padded'},
  args: {product: f01},
  decorators: [(Story) => <div className="max-w-2xl"><Story /></div>],
} satisfies Meta<typeof SpecSheet>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Full: Story = {};
export const Compact: Story = {args: {variant: 'compact'}};
/** F06 is a one-piece shield: no bridge row, the size reads 139□— 150. */
export const NullRowsHidden: Story = {name: 'F06 · null rows left out', args: {product: f06}};
export const DrawnTriptych: Story = {name: 'LineDrawing · triptych', render: () => <LineDrawing product={f01} drawings={storyDrawings('F01')} />};
export const DrawnSingle: Story = {name: 'LineDrawing · single', render: () => <LineDrawing product={f01} drawings={storyDrawings('F01')} views={['front']} variant="single" />};
export const DrawnPrint: Story = {name: 'LineDrawing · print (paper)', globals: {theme: 'paper'}, render: () => <LineDrawing product={f06} drawings={storyDrawings('F06')} variant="print" />};
