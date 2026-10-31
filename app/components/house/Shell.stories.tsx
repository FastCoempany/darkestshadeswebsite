import type {Meta, StoryObj} from '@storybook/react-vite';
import {drops, STORY_NOW} from '~/components/pages/stories/fixtures';
import {CartProvider} from '~/lib/cart';
import {copy} from '~/lib/copy';
import {Footer} from './Footer';
import {Header} from './Header';
import {MenuSheet} from './MenuSheet';

const meta = {
  title: 'House/Shell',
  parameters: {layout: 'fullscreen'},
  decorators: [(Story) => <CartProvider persist={false}><Story /></CartProvider>],
} satisfies Meta;
export default meta;
type Story = StoryObj<typeof meta>;

export const HeaderSolid: Story = {name: 'Header · solid', render: () => <Header bagCount={0} onOpenMenu={() => undefined} onOpenBag={() => undefined} />};
export const HeaderWithBag: Story = {name: 'Header · Bag (3)', render: () => <Header bagCount={3} onOpenMenu={() => undefined} onOpenBag={() => undefined} />};
export const HeaderTransparent: Story = {
  name: 'Header · transparent over the manifesto',
  render: () => (
    <div className="min-h-dvh bg-ds-surface-canvas">
      <Header bagCount={0} onOpenMenu={() => undefined} onOpenBag={() => undefined} surface="transparent" />
      <p className="ds-display px-4 pt-24 text-manifesto leading-manifesto" data-manifesto="home">{copy.entry.cards[0]}</p>
    </div>
  ),
};
export const HeaderMenuOpen: Story = {
  name: 'Header · menu open',
  render: () => (
    <>
      <Header bagCount={0} onOpenMenu={() => undefined} onOpenBag={() => undefined} menuOpen />
      <MenuSheet open onClose={() => undefined} drop={drops.announcedNoDate} />
    </>
  ),
};
export const Menu: Story = {name: 'MenuSheet · open', render: () => <MenuSheet open onClose={() => undefined} drop={drops.live} />};
export const MenuClosed: Story = {name: 'MenuSheet · closed (nothing renders)', render: () => <MenuSheet open={false} onClose={() => undefined} drop={drops.live} />};
export const FooterNight: Story = {name: 'Footer · night', render: () => <Footer year={STORY_NOW.getFullYear()} />};
export const FooterNoList: Story = {name: 'Footer · without the list (home, drop)', render: () => <Footer year={STORY_NOW.getFullYear()} showList={false} />};
