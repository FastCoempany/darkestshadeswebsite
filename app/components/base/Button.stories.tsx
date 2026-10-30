import type {Meta, StoryObj} from '@storybook/react-vite';
import {copy} from '~/lib/copy';
import {Button, type ButtonSize, type ButtonVariant} from './Button';

const VARIANTS: ButtonVariant[] = ['solid', 'outline', 'quiet'];
const SIZES: ButtonSize[] = [40, 48, 56];

/** One story per state; every variant and size inside it. `data-force` stands in for the pseudo-class. */
function Sheet({force, disabled, busy}: {force?: 'hover' | 'active' | 'focus-visible'; disabled?: boolean; busy?: boolean}) {
  return (
    <div className="grid gap-8 p-6">
      {VARIANTS.map((variant) => (
        <div key={variant} className="flex flex-wrap items-end gap-4">
          {SIZES.map((size) => (
            <Button key={size} variant={variant} size={size} disabled={disabled} busy={busy} data-force={force}>
              {copy.product.addToBag}
            </Button>
          ))}
        </div>
      ))}
    </div>
  );
}

const meta = {
  title: 'Base/Button',
  component: Button,
  parameters: {layout: 'fullscreen'},
  args: {children: copy.product.addToBag},
} satisfies Meta<typeof Button>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {render: () => <Sheet />};
export const Hover: Story = {render: () => <Sheet force="hover" />};
export const Active: Story = {render: () => <Sheet force="active" />};
export const FocusVisible: Story = {render: () => <Sheet force="focus-visible" />};
export const Disabled: Story = {render: () => <Sheet disabled />};
export const Busy: Story = {render: () => <Sheet busy />};
/** On paper, solid is onyx on bone. */
export const Paper: Story = {globals: {theme: 'paper'}, render: () => <Sheet />};
export const AsLink: Story = {
  render: () => (
    <div className="flex gap-4 p-6">
      <Button to="/frames" variant="solid">
        {copy.nav.frames}
      </Button>
      <Button to="/drop" variant="outline">
        {copy.nav.drop}
      </Button>
    </div>
  ),
};
